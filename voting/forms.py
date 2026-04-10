from django import forms
from .models import Election

class ElectionForm(forms.ModelForm):
    class Meta:
        model  = Election
        fields = ['title', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date':   forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned_data