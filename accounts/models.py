from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    ROLE_CHOICES = [
        ('voter',     'Voter'),
        ('organizer', 'Organizer'),
        ('admin',     'Admin'),
    ]
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='voter')

    voter_id = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=False,
        help_text="Citizenship No. / Student ID / Phone Number"
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"

