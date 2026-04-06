from django import forms
from .models import AuditRequest

class AuditRequestForm(forms.ModelForm):
    class Meta:
        model = AuditRequest
        fields = ['reason']

        widgets ={
            'reason': forms.Textarea(attrs={'rows':4, 'palceholder':'Enter reason.....'}),
        } 

class AuditResponseForm(forms.ModelForm):
    class Meta:
        model = AuditRequest
        fields = [
            'status', 'admin_response'
        ]

