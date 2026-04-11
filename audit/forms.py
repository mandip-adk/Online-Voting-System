from django import forms
from .models import AuditRequest

class AuditRequestForm(forms.ModelForm):
    class Meta:
        model  = AuditRequest
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'rows':        4,
                'placeholder': 'Explain why you are requesting an audit...'
            }),
        }

class AuditResponseForm(forms.ModelForm):
    class Meta:
        model  = AuditRequest
        fields = ['status', 'admin_response']
        widgets = {
            'admin_response': forms.Textarea(attrs={
                'rows':        4,
                'placeholder': 'Write your response to the candidate...'
            }),
        }

    def clean(self):
        cleaned_data   = super().clean()
        status         = cleaned_data.get('status')
        admin_response = cleaned_data.get('admin_response')

        # Response is required when approving or rejecting
        if status in ['approved', 'rejected'] and not admin_response:
            raise forms.ValidationError(
                "Please provide a response when approving or rejecting an audit request."
            )
        return cleaned_data
    
    