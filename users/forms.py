from django import forms
from survey_admin.models import CustomUser
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import Profile

class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="First Name")
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Last Name")
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Username")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Email")
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Confirm Password")

    class Meta:
        model = CustomUser  # Use CustomUser instead of User
        fields = ['first_name', 'last_name', 'username', 'email', 'password1', 'password2']

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="First Name")
    last_name = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Last Name")
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Username")
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Email")

    class Meta:
        model = CustomUser  # Use CustomUser instead of User
        fields = ['first_name', 'last_name', 'username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['image']

class UpdatePasswords(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Old Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control form-control-sm rounded-0'}), label="Confirm New Password")
    
    class Meta:
        model = CustomUser  # Use CustomUser instead of User
        fields = ('old_password', 'new_password1', 'new_password2')
