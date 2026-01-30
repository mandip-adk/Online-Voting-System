from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    role_choice = (
        ("admin", "Admin"),
        ("voter", "Voter"),
        ("candidate", "Candidate"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=role_choice, default="voter")
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.role}"
    

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    is_activate = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="created_elections",
        null=True,
        blank=True
        )

    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    election = models.ForeignKey(
        Election, 
        on_delete=models.CASCADE
        )
    manifesto = models.TextField(blank=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Vote(models.Model):
    voter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="votes"
        )
    Candidate = models.ForeignKey(
        Candidate, 
        on_delete=models.CASCADE
        )
    election = models.ForeignKey(
        Election, 
        on_delete=models.CASCADE
        )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voter", "election")

    def __str__(self):
        return f"{self.Voter}"  
