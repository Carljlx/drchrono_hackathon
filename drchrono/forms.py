from django import forms

class DemographicsForm(forms.Form):
	first_name = forms.CharField(required=True, max_length=100, label='First Name (required)', widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
	last_name = forms.CharField(required=True, max_length=100, label='Last Name (required)', widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
	cell_phone = forms.RegexField(regex='^(\d{3}\-\d{3}\-\d{4})$', label='Mobile Phone (required)', error_messages={'invalid': 'A valid phone number must in the format xxx-xxx-xxxx'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
	email = forms.EmailField(required=True, label='Email Address (required)', widget=forms.EmailInput(attrs={'class': 'form-control'}))
	address = forms.CharField(required=False, label='Address', widget=forms.TextInput(attrs={'class': 'form-control'}))
	zip_code = forms.RegexField(required=False, regex='^\d{5}$', label='Zip Code', error_messages={'invalid': 'A valid zip-code must in the format xxxxx'}, widget=forms.TextInput(attrs={'class': 'form-control'}))
	emergency_contact_name = forms.CharField(required=False, max_length=100, label='Emergency Contact Name', widget=forms.TextInput(attrs={'class': 'form-control'}))
	emergency_contact_phone = forms.RegexField(required=False, regex='^(\d{3}\-\d{3}\-\d{4})$', label='Emergency Contact Phone', error_messages={'invalid': 'A valid phone number must in the format xxx-xxx-xxxx'}, widget=forms.TextInput(attrs={'class': 'form-control'}))

class CheckinForm(forms.Form):
	first_name = forms.CharField(max_length=100, label='First Name', widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
	last_name = forms.CharField(max_length=100, label='Last Name', widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))
	SSN = forms.RegexField(regex='^(\d{3}\-\d{2}\-\d{4})$', label='Social Security Number', error_messages={'invalid': 'Must enter valid SSN in the format xxx-xx-xxxx'}, widget=forms.TextInput(attrs={'required': True, 'class': 'form-control'}))

class SearchForm(forms.Form):
    search_term = forms.CharField(required=False, max_length=255, label='Search by Names:')
