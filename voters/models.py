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
    

class Election(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_activate = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    manifesto = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    Candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)
    election = models.ForeignKey(Election, on_delete=models.CASCADE)
    cast_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voter", "election")

    def __str__(self):
        return f"{self.Voter}"  
