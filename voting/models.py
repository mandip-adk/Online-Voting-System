from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone

class Election(models.Model):
    title = models.CharField(max_length=50)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    status = models.CharField(max_length= 10, choices= STATUS_CHOICES, default='pending')
    
 # FK to the user who created the election
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # points to your CustomUser
        on_delete= models.CASCADE,
        related_name= "elections"
    )

    def __str__(self):
        return f"{self.title} ({self.status})"

    def sync_status(self):
        """Compute status from dates and save if it changed."""
        now = timezone.now()
        if now < self.start_date:
            new_status = 'pending'
        elif self.start_date <= now <= self.end_date:
            new_status = 'active'
        else:
            new_status = 'closed'

        if self.status != new_status:
            self.status = new_status
            self.save(update_fields=['status'])

class Candidate(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    election = models.ForeignKey(
        "election",
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    bio = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.user.username} - ({self.election.title})"

class VoterParticipation(models.Model):

    class Meta:
        unique_together = [('user', 'election')]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete= models.CASCADE,
        related_name="voters"
    )
    election = models.ForeignKey(
        "election",
        on_delete= models.CASCADE,
        related_name="participations"
    )
    voted_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - ({self.voted_at})"

class Votes(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    election = models.ForeignKey(
        "election",
        on_delete= models.CASCADE,
        related_name="votes"
    )
    candidate = models.ForeignKey(
        "candidate",
        on_delete= models.CASCADE,
        related_name="votes"
    )
    voted_at = models.DateTimeField()

    def __str__(self):
        return str(self.token)
    
