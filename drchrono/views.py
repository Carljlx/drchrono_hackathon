from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib import messages
from .models import Doctor, Patient, Appointment
from .forms import CheckinForm, DemographicsForm, SearchForm
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.utils import timezone
from drchrono_hackathon.settings import SOCIAL_AUTH_CLIENT_ID, SOCIAL_AUTH_CLIENT_SECRET, EMAIL_HOST_USER
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from twilio.rest import Client
from django.db.models import Q
from dateutil import parser
from dateutil.tz import tzlocal
import datetime, time
import requests, pytz
import json

# Create your views here.
def home(request):
    return render(request, 'drchrono/home.html')

@login_required
def authorize(request):
    # User authorizes application
    base_url = 'https://drchrono.com/o/authorize/'
    redirect_uri = 'http://127.0.0.1:8000/drchrono_login'
    client_id = SOCIAL_AUTH_CLIENT_ID
    scope = 'patients:write patients:read patients:summary user:read user:write calendar:read calendar:write clinical:read clinical:write'
    url = base_url + "?redirect_uri={}&response_type=code&client_id={}&scope={}".format(redirect_uri, client_id, scope)
    return HttpResponseRedirect(url)

@login_required
def drchrono_login(request):
    # Drchrono authorization & token exchange
    response = requests.post('https://drchrono.com/o/token/', data={
        'code': request.GET['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://127.0.0.1:8000/drchrono_login',
        'client_id': SOCIAL_AUTH_CLIENT_ID,
        'client_secret': SOCIAL_AUTH_CLIENT_SECRET,
    })
    response.raise_for_status()
    data = response.json()
    # Saves these in database associated with the user
    access_token = data['access_token']
    refresh_token = data['refresh_token']
    expires_timestamp = datetime.datetime.now(pytz.utc) + datetime.timedelta(seconds=data['expires_in'])
    # Create a new doctor or update doctor's information
    try:
        current_user = Doctor.objects.get(user=request.user.id)
        current_user.access_token = access_token
        current_user.refresh_token = refresh_token
        current_user.expires_timestamp = expires_timestamp
        current_user.save()
    # Set the name of doctor to the user's name, it could be modified if doctor changes
    except Doctor.DoesNotExist:
        user = Doctor(
            first_name='Carl',
            last_name='Yu',
            user=request.user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_timestamp=expires_timestamp,
        )
        user.save()

    get_doctor_info(request)
    return redirect('home')

# Get doctor info from Drchrono.com
def get_doctor_info(request):
    user = Doctor.objects.get(user=request.user)
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    users_url = 'https://drchrono.com/api/users/current'
    office_url = 'https://drchrono.com/api/offices'
    data_user = requests.get(users_url, headers=headers).json()
    data_office = requests.get(office_url, headers=headers).json()
    current_user = Doctor.objects.get(user=request.user.id)
    current_user.doctor_api_id = data_user['doctor']
    current_user.office = int(data_office['results'][0]['id'])
    current_user.save()

def get_all_logged_in_users(request):
    # Query all non-expired sessions
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    uid_list = []
    # Build a list of user ids from that query
    for session in sessions:
        data = session.get_decoded()
        uid_list.append(data.get('_auth_user_id', None))
    # Query all logged in users based on id list
    users = User.objects.filter(id__in=uid_list)
    return users

def checkin(request):
    users = get_all_logged_in_users(request)
    # After the doctor is logged in, redirect the patient page to the checkin page
    if len(users) != 0:
        return render(request, 'drchrono/checkin.html')
    # If not, redirect to the home page
    else:
        return render(request, 'drchrono/home.html')

def patients_checkin(request):
    if request.method == 'POST':
        form = CheckinForm(request.POST)
        today = datetime.datetime.today().date()
        if form.is_valid():
            # get cleaned_data from the form
            cleaned_form = form.cleaned_data
            f_name = cleaned_form['first_name'].strip()
            l_name = cleaned_form['last_name'].strip()
            ssn = cleaned_form['SSN'].strip()
            # Check if the input is correct
            try:
                patient = Patient.objects.get(first_name=f_name, last_name=l_name, social_security_number=ssn)
                # Check if the patient has an appointment today
                try:
                    appointment_obj = Appointment.objects.filter((Q(patient_api_id=patient.patient_api_id) & Q(date=today)) & (Q(status="Confirmed") | Q(status="Rescheduled"))).order_by('scheduled_time')
                    # If duplicate, get the first appointment ordered by scheduled time
                    if appointment_obj:
                        return render(request, 'drchrono/checkin_or_update.html', {'appointment':appointment_obj[0]})
                    # Return error if no appointment today
                    else:
                        form = CheckinForm()
                        error = "You do not have any confirmed appointment today"
                        return render(request, 'drchrono/patients_checkin.html', {'form':form, 'error':error})
                # Return error if no appointment today
                except Appointment.DoesNotExist:
                    form = CheckinForm()
                    error = "You do not have any confirmed appointment today"
                    return render(request, 'drchrono/patients_checkin.html', {'form':form, 'error':error})
            # Return error if the patient does not exist
            except Patient.DoesNotExist:
                form = CheckinForm()
                error = "Patient information is incorrect or does not exist"
                return render(request, 'drchrono/patients_checkin.html', {'form':form, 'error':error})
    else:
        form = CheckinForm()

    return render(request, 'drchrono/patients_checkin.html', {'form':form})

def demographics(request, id):
    user_name = get_all_logged_in_users(request)[0]
    user = Doctor.objects.get(user=user_name)
    appointment_obj = Appointment.objects.get(appointment_api_id=id)
    patient_api_id = appointment_obj.patient_api_id
    patient_obj = Patient.objects.get(patient_api_id=patient_api_id)
    url = "https://drchrono.com/api/patients/" + str(patient_api_id)
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    # If it is a post request, update the demographics info
    if request.method == 'POST':
        form = DemographicsForm(request.POST)
        # If not valid, return back to the same page
        if form.is_valid():
            cleaned_form = form.cleaned_data
            f_name = cleaned_form['first_name'].strip()
            l_name = cleaned_form['last_name'].strip()
            cell_phone = cleaned_form['cell_phone'].strip()
            email = cleaned_form['email'].strip()
            address = cleaned_form['address'].strip()
            zip_code = cleaned_form['zip_code'].strip()
            emergency_contact_name = cleaned_form['emergency_contact_name'].strip()
            emergency_contact_phone = cleaned_form['emergency_contact_phone'].strip()
            # Initial data
            data = {
                'first_name': f_name,
                'last_name' : l_name,
                'cell_phone': cell_phone,
                'email'     : email,
                'address'   : address,
                'zip_code'  : zip_code,
                'emergency_contact_name' : emergency_contact_name,
                'emergency_contact_phone': emergency_contact_phone,
            }
            # Pop empty fileds in data dict
            for idx in data.copy():
                if not data[idx]:
                    data.pop(idx)
            # Patch the data to the patients api of drchrono
            re_code = requests.patch(url, data=data, headers=headers)
            # print(re_code)
            # Modify the local database
            if re_code.status_code == 204:
                patient_obj.first_name = f_name
                patient_obj.last_name  = l_name
                patient_obj.cell_phone = cell_phone
                patient_obj.email      = email
                patient_obj.save()
                count = len(Appointment.objects.filter(status="Arrived"))
                # Check in action
                return checkin_complete(request, id)
            else:
                form = DemographicsForm()
    else:
        form = DemographicsForm() # Initial empty form
    return render(request, 'drchrono/demographics.html', {'form':form})

def checkin_complete(request, id):
    user_name = get_all_logged_in_users(request)[0]
    user = Doctor.objects.get(user=user_name)
    data = {'status':'Arrived'}
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    url = "https://drchrono.com/api/appointments/" + str(id)
    re_code = requests.patch(url, data=data, headers=headers)
    # Check the API return code
    if re_code.status_code == 204:
        appointment_obj = Appointment.objects.get(appointment_api_id=id)
        today = datetime.datetime.today().date()
        count = len(Appointment.objects.filter(Q(status="Arrived") & Q(date=today)))
        appointment_obj.status = "Arrived"
        appointment_obj.arrival_time = datetime.datetime.now()
        appointment_obj.save()
        # Send check in email warning to doctor's email address
        # Need to modify the settings.py file
        patient = Patient.objects.get(patient_api_id=appointment_obj.patient_api_id)
        patient_name = patient.first_name + ' ' + patient.last_name
        email = EmailMessage('Check in action!', patient_name + ' checked in! You can start this session right now.', to=[EMAIL_HOST_USER])
        email.send()
    else:
        error = "Checkin failed, please try again"
        return render(request, 'drchrono/patients_checkin.html', {'error':error})

    return render(request, 'drchrono/checkin_complete.html', {'success':'Check in Complete!', 'doctor':user_name, 'count':count})

@login_required
def status_change(request, id):
    user = Doctor.objects.get(user=request.user)
    url = "https://drchrono.com/api/appointments/" + str(id)
    appointment_obj = Appointment.objects.get(appointment_api_id=id)
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    # Change the status based on different situations
    # If it is "Arrived", change it to "In Session"
    if appointment_obj.status == "Arrived":
        next_stage = "In Session"
    # If it is "In Session/ In Room", change it to "Complete"
    elif appointment_obj.status == "In Session" or appointment_obj.status == "In Room":
        next_stage = "Complete"
    # If it is "Confirmed", we may need a button to cancel it
    elif appointment_obj.status == "Confirmed":
        next_stage = "Cancelled"
    else:
        return redirect('appointments')

    data = {'status':next_stage}
    re_code = requests.patch(url, data=data, headers=headers)
    # Check if the update is successful
    # Return back to the appointment page
    if re_code.status_code == 204:
        appointment_obj.status = next_stage
        # Save the time information in local database
        if next_stage == "In Session" and appointment_obj.arrival_time:
            appointment_obj.waiting_time = datetime.datetime.now() - appointment_obj.arrival_time
            patient = Patient.objects.get(patient_api_id=appointment_obj.patient_api_id)
            patient_name = patient.first_name + ' ' + patient.last_name
            # Send email to specific patient after confirmation
            if patient.email:
                email = EmailMessage('Doctor confirmed!', 'Your appointment is about to start! Please go to room: ' + str(appointment_obj.exam_room), to=[patient.email])
                email.send()
        # Update the duration when complete the appointment
        elif appointment_obj.waiting_time:
            appointment_obj.duration = datetime.datetime.now() - appointment_obj.arrival_time - appointment_obj.waiting_time

        appointment_obj.save()
        return redirect('appointments')
        # If failed, return an error message and do not modify the local database
    else:
        error = "Change status failed, please try again"
        return render(request, 'drchrono/appointments.html', {'error':error})

# Get all patients from drchrono.com
@login_required
def get_all_patients(request):
    user = Doctor.objects.get(user=request.user)
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    patients = []
    patients_url = 'https://drchrono.com/api/patients'
    # Get all patients
    while patients_url:
        data = requests.get(patients_url, headers=headers).json()
        patients.extend(data['results'])
        patients_url = data['next'] # A JSON null on the last page
    # Create and update patient information
    for patient in patients:
        try:
            patient_obj = Patient.objects.get(patient_api_id = patient['id'])
            patient_obj.doctor_api_id = patient['doctor']
            patient_obj.first_name = patient['first_name']
            patient_obj.last_name = patient['last_name']
            patient_obj.patient_api_id = patient['id']
            patient_obj.email = patient['email']
            patient_obj.social_security_number = patient['social_security_number']
            patient_obj.cell_phone = patient['cell_phone']
            patient_obj.save()

        except Patient.DoesNotExist:
            patient_obj = Patient(
                doctor_api_id = patient['doctor'],
                first_name = patient['first_name'],
                last_name = patient['last_name'],
                patient_api_id = patient['id'],
                email = patient['email'],
                social_security_number = patient['social_security_number'])

            patient_obj.save()

    return redirect('home')

@login_required
def appointments(request):
    raw_apps, avg_hour, avg_min = get_all_appointments(request)
    search_form = SearchForm(request.GET) # Search by patient's name
    today = datetime.datetime.today().date()
    now = datetime.datetime.now().time()
    appointments = []
    # Check the content of the search form
    if search_form.is_valid():
        search_data = search_form.cleaned_data['search_term'].strip().lower()
        # If the input is empty, return the entire appointment list
        if len(search_data) == 0:
            appointments = raw_apps
        # Filter the list by the patient's first name or last name
        else:
            for app in raw_apps:
                if app['patient_first_name'].lower().startswith(search_data) or app['patient_last_name'].lower().startswith(search_data):
                    appointments.append(app)
    # Displayed data
    data = {
        'appointments':appointments,
        'search_form':search_form,
        'today':today,
        'now':now,
        'avg_hour':avg_hour,
        'avg_min':avg_min}

    return render(request, 'drchrono/appointments.html', data)

# Get avg time and shows on the appointment page
def get_avg_time(request, total_hour, total_min, count):
    # zero case
    total_time = total_hour * 60 + total_min
    if count == 0 or total_time == 0:
        avg_hour = 0
        avg_min  = 0
    # Calculate the avg time
    else:
        avg_time = int(total_time / count)
        avg_hour = avg_time // 60
        avg_min  = avg_time % 60
    return avg_hour, avg_min

# Get all appointments from the drchrono.com
@login_required
def get_all_appointments(request):
    # Lists all of today's appointments.
    user = Doctor.objects.get(user=request.user)
    headers = {'Authorization': 'Bearer %s' % user.access_token}
    today = datetime.datetime.today()
    # Save the result to appointments list
    appointments = []
    appointments_url = 'https://drchrono.com/api/appointments?doctor=' + str(user.doctor_api_id) + '&date=' + str(today)
    # Parameters to count the avg waiting time
    count = 0
    total_hour = 0
    total_min = 0
    # Get every pages of the appointments
    while appointments_url:
        data = requests.get(appointments_url, headers=headers).json()
        # if api calling failed, redirect to appointment page
        if not data:
            return redirect('appointment')
        # process every appointment
        for appointment in data['results']:
            if appointment['status'] == "Cancelled":
                continue
            if appointment['status'] == "Not Confirmed":
                continue
            # prepare schedule time, name to be sent to the front end
            raw_time = parser.parse(appointment['scheduled_time'])
            appointment['scheduled_time'] = raw_time.time()
            # Add patient's name to the appointment dict
            appointment['patient_first_name'] = Patient.objects.get(patient_api_id=appointment['patient']).first_name
            appointment['patient_last_name'] = Patient.objects.get(patient_api_id=appointment['patient']).last_name
            appointments.append(appointment)
            # Save data to appointment dict
            try:
                appointment_obj = Appointment.objects.get(appointment_api_id=appointment['id'])
                appointment_obj.scheduled_time = raw_time
                appointment_obj.date = today.date()
                appointment_obj.status = appointment['status']
                appointment_obj.exam_room = appointment['exam_room']
                #appointment_obj.patient_api_id = appointment['patient']
                appointment_obj.save()
                # Update duration time if it exist
                if appointment_obj.duration:
                    if str(appointment_obj.waiting_time)[2].isdigit():
                        appointment['duration'] = str(appointment_obj.duration)[:4]
                    # More than 10 hours
                    else:
                        appointment['duration'] = str(appointment_obj.duration)[:5]
                # If not, leave it blank
                else:
                    appointment['duration'] = ""
                # Update the arrival time
                if appointment_obj.arrival_time:
                    appointment['arrival_time'] = appointment_obj.arrival_time.time()
                    appointment['curr_waiting_time'] = str(datetime.datetime.now() - appointment_obj.arrival_time)[:4]
                else:
                    appointment['arrival_time'] = ""
                # Update the waiting time
                if appointment_obj.waiting_time:
                    # Handle different cases less or more than 10 hours
                    if str(appointment_obj.waiting_time)[2].isdigit():
                        appointment['waiting_time'] = str(appointment_obj.waiting_time)[:4]
                        # Count the total time for avg time calculating
                        total_hour += int(appointment['waiting_time'][:1])
                        total_min += int(appointment['waiting_time'][2:4])
                        count += 1
                    # More than 10 hours
                    else:
                        appointment['waiting_time'] = str(appointment_obj.waiting_time)[:5]
                        total_hour += int(appointment['waiting_time'][:2])
                        total_min += int(appointment['waiting_time'][3:5])
                        count += 1
                else:
                    appointment['waiting_time'] = ""

            # If not exist, create a new object in database
            except Appointment.DoesNotExist:
                Appointment_obj = Appointment(
                    patient_api_id = appointment['patient'],
                    appointment_api_id = appointment['id'],
                    scheduled_time = raw_time,
                    date = today.date(),
                    status = appointment['status'],
                )
                Appointment_obj.save()
        # Next page
        appointments_url = data['next']

    avg_hour, avg_min = get_avg_time(request, total_hour, total_min, count)
    return appointments, avg_hour, avg_min
