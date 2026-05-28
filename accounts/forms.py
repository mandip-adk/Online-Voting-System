from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=50)
    last_name  = forms.CharField(max_length=50)
    email      = forms.EmailField()
    voter_id   = forms.CharField(
        max_length=30,
        label="Unique ID",
        help_text="Citizenship No. / Student ID / Phone Number"
    )
    role = forms.ChoiceField(
        choices=[
            ('voter',     'Voter — I want to participate in elections'),
            ('organizer', 'Organizer — I want to create and manage elections'),
        ]
    )

    class Meta:
        model  = CustomUser
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'voter_id', 'role',
            'password1', 'password2'
        ]

    def clean_voter_id(self):
        voter_id = self.cleaned_data.get('voter_id')
        if CustomUser.objects.filter(voter_id=voter_id).exists():
            raise forms.ValidationError(
                "This ID is already registered. Each person can only have one account."
            )
        return voter_id


from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Your Email Address'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject of Message'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write your message here...', 'rows': 5}),
        }