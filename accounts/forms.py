from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.db import models


class RegisterForm(forms.ModelForm):

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput,
    )

    class Meta:
        model  = CustomUser
        fields = ['first_name', 'last_name', 'email', 'role', 'organization_name', 'country']
        widgets = {
            'role': forms.RadioSelect,
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        org  = cleaned_data.get('organization_name')
        country = cleaned_data.get('country')

        if role == 'organizer':
            if not org:
                self.add_error('organization_name', 'Organization name is required for organizers.')
            if not country:
                self.add_error('country', 'Country is required for organizers.')

        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user
    

class ContactMessage(models.Model):
    name         = models.CharField(max_length=100)
    email        = models.EmailField()
    subject      = models.CharField(max_length=200)
    message      = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class ContactForm(forms.Form):
    name    = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Your Full Name'
    }))
    email   = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Your Email Address'
    }))
    subject = forms.CharField(max_length=200, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Subject of Message'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'form-control', 'placeholder': 'Write your message here...', 'rows': 5
    }))

    