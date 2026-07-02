from django.db import models
from voting.models import Election


class AuditRequest(models.Model):

    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    election       = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='audits')
    reason         = models.TextField()
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Audit — {self.election.title} ({self.status})"
    
    