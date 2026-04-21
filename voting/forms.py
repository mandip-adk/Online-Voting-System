from django import forms
from .models import Election, Candidate

class ElectionForm(forms.ModelForm):
    class Meta:
        model  = Election
        fields = [
            'title',
            'start_date',
            'end_date',
            'eligibility_type',
            'eligibility_value',
        ]
        widgets = {
            'start_date':        forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date':          forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'eligibility_value': forms.TextInput(attrs={
                'placeholder': 'Domain: school.edu  |  ID List: ID001,ID002,ID003'
            }),
        }

    def clean(self):
        cleaned_data      = super().clean()
        start             = cleaned_data.get('start_date')
        end               = cleaned_data.get('end_date')
        eligibility_type  = cleaned_data.get('eligibility_type')
        eligibility_value = cleaned_data.get('eligibility_value')

        # Date validation
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")

        # Eligibility value required for domain and id_list
        if eligibility_type in ['domain', 'id_list'] and not eligibility_value:
            raise forms.ValidationError(
                "Please provide a value for the eligibility rule you selected."
            )

        return cleaned_data
    
class CandidateApplicationForm(forms.ModelForm):
    class Meta:
        model  = Candidate
        fields = ['bio', 'photo_url']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows':        5,
                'placeholder': 'Tell voters who you are and why you are running...'
            }),
            'photo_url': forms.URLInput(attrs={
                'placeholder': 'https://example.com/your-photo.jpg (optional)'
            }),
        }
        labels = {
            'bio':       'Your bio / campaign statement',
            'photo_url': 'Profile photo URL (optional)',
        }