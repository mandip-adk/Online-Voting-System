from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    role_choice = (
        ("voter", "voter"),
        ("candidate", "candidate"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=role_choice, default="voter")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username