from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import localtime, now


class Doctor(models.Model):
    doctor_id = models.IntegerField(primary_key=True)
    doctor_api_id = models.IntegerField(default=0)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    office = models.IntegerField(default=0)
    access_token = models.CharField(max_length=200)
    refresh_token = models.CharField(max_length=200)
    expires_timestamp = models.CharField(max_length=200)

class Patient(models.Model):
    patient_id = models.IntegerField(primary_key=True)
    patient_api_id = models.IntegerField(default=0)
    doctor_api_id = models.IntegerField(default=0)
    social_security_number = models.CharField(max_length=30, default="")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default="")
    cell_phone = models.CharField(max_length=50, null=True)

class Appointment(models.Model):
    appointment_id = models.IntegerField(primary_key=True)
    patient_api_id = models.IntegerField(default=0)
    appointment_api_id = models.CharField(max_length=50, null=True)
    date = models.DateField(auto_now=False, auto_now_add=False, null=True, default=None)
    scheduled_time = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)
    waiting_time = models.DurationField(null=True)
    duration = models.DurationField(null=True)
    arrival_time = models.DateTimeField(auto_now=False, auto_now_add=False, null=True, default=None)
    status = models.CharField(max_length=50, null=True)
    exam_room = models.CharField(max_length=50, null=True)

#class Appointment(models.Model):
