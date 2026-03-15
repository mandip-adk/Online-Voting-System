from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser (AbstractUser):

    ROLE_CHOICES = [
        ('voter', 'Voter'),
        ('candidate', 'Candidate'),
        ('admin','Admin'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="voter")

    def __str__(self):
        return f"{self.username} ({self.role})"
    