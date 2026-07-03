from django import forms
from .models import Election, Contest, ContestCandidate


class ElectionForm(forms.ModelForm):
    class Meta:
        model  = Election
        fields = ['title', 'description', 'start_date', 'end_date']
        widgets = {
            'title':       forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. Student Council Election 2026',
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        4,
                'placeholder': 'Describe this election (optional)...',
            }),
            'start_date':  forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type':  'datetime-local',
            }),
            'end_date':    forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type':  'datetime-local',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end   = cleaned_data.get('end_date')
        if start and end and end <= start:
            raise forms.ValidationError("End date must be after start date.")
        return cleaned_data


class ContestForm(forms.ModelForm):
    class Meta:
        model  = Contest
        fields = ['title', 'voting_method', 'seats', 'order']
        widgets = {
            'title':         forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'e.g. President, Vice President, Approve Budget...',
            }),
            'voting_method': forms.Select(attrs={
                'class': 'form-control',
            }),
            'seats':         forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   1,
            }),
            'order':         forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   0,
            }),
        }
        labels = {
            'seats': 'Number of Winners',
            'order': 'Display Order (0 = first)',
        }

    def clean_seats(self):
        seats = self.cleaned_data.get('seats')
        if seats and seats < 1:
            raise forms.ValidationError("Must have at least 1 winner.")
        return seats


class ContestCandidateForm(forms.ModelForm):
    class Meta:
        model  = ContestCandidate
        fields = ['name', 'description', 'order']
        widgets = {
            'name':        forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Candidate full name',
            }),
            'description': forms.Textarea(attrs={
                'class':       'form-control',
                'rows':        3,
                'placeholder': 'Short bio or description (optional)',
            }),
            'order':       forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   0,
            }),
        }
        labels = {
            'order': 'Display Order (0 = first)',
        }


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Upload CSV file",
        help_text="One email address per row, no header needed. Example: voter@example.com",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.txt'}),
    )


class EmailListForm(forms.Form):
    """Alternative to CSV — paste emails directly."""
    emails = forms.CharField(
        label="Voter Email Addresses",
        help_text="One email per line, or comma-separated.",
        widget=forms.Textarea(attrs={
            'class':       'form-control',
            'rows':        8,
            'placeholder': 'voter1@example.com\nvoter2@example.com\nvoter3@example.com',
        }),
    )

    def clean_emails(self):
        raw = self.cleaned_data.get('emails', '')
        # support both newline and comma separated
        emails = []
        for part in raw.replace(',', '\n').splitlines():
            email = part.strip().lower()
            if email:
                # basic validation
                try:
                    forms.EmailField().clean(email)
                    emails.append(email)
                except forms.ValidationError:
                    raise forms.ValidationError(f"'{email}' is not a valid email address.")
        if not emails:
            raise forms.ValidationError("Please enter at least one email address.")
        return emails
    
    