from django import forms
from .models import Parent
from .models import Child
import re



class ParentRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Parent
        fields = ['email', 'password1', 'password2', 'name', 'phoneNo']

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
    class Meta:
        model = Child
        fields = ['name', 'age', 'image']  # Fields for the child's information