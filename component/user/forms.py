from datetime import date

from django import forms
from django.core.exceptions import ValidationError

from .models import Parent
from .models import Child
import re


class ParentRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}))
    password2 = forms.CharField(label='Confirm Password',
                                widget=forms.PasswordInput(attrs={'placeholder': 'Confirm your password'}))

    class Meta:
        model = Parent
        fields = ['email', 'password1', 'password2', 'name', 'phoneNo']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
            'name': forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
            'phoneNo': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
        }

    # Other validations remain unchanged

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two password fields must match.")
            if len(password1) < 8 and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password1):
                raise forms.ValidationError("This password is too short. It must contain at least 8 characters and one special character")
        return password2

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if "@" not in email:
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_phoneNo(self):
        phoneNo = self.cleaned_data.get("phoneNo")
        if not re.match(r"^(\+60|0)[1-9][0-9]{7,8}$", phoneNo):
            raise forms.ValidationError("Please enter a valid Malaysian phone number.")
        return phoneNo


class LoginForm(forms.Form):
    email = forms.EmailField(label="email")
    password = forms.CharField(widget=forms.PasswordInput, label="password")



class ChildAccountForm(forms.ModelForm):
    image = forms.ImageField(required=False)

    class Meta:
        model = Child
        fields = ['name', 'birthday', 'image']  # Fields for the child's information

    def clean_birthday(self):
        birthday = self.cleaned_data.get('birthday')
        if not birthday:
            return birthday

        # Get today's date
        today = date.today()

        # Calculate age by comparing birthday with today's date
        age_in_days = (today - birthday).days
        age_in_years = age_in_days / 365.25  # To account for leap years

        if age_in_years < 1:
            raise forms.ValidationError("The child must be at least 1 year old.")
        if age_in_years > 5:
            raise forms.ValidationError("The child cannot be older than 5 year old.")

        return birthday


class ParentDetailForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    class Meta:
        model = Parent
        fields = ['name', 'phoneNo', 'image']  # Exclude 'email' if not updatable

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Check if 'email' is in fields to avoid KeyError
        if 'email' in self.fields:
            self.fields['email'].disabled = True  # Make email read-only if present

