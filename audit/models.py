from django.db import models
from voting.models import Election, Candidate

class AuditRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    candidate      = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='audits')
    election       = models.ForeignKey(Election,  on_delete=models.CASCADE, related_name='audits')
    reason         = models.TextField()
    status         = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate} ({self.election}) - {self.status}"
    

    