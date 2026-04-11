from django.db import models
from django.conf import settings
import uuid
from django.utils import timezone

class Election(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active',  'Active'),
        ('closed',  'Closed'),
    ]
    ELIGIBILITY_CHOICES = [
        ('open',   'Open — Anyone registered can vote'),
        ('domain', 'Domain — Only specific email domain'),
        ('id_list','ID List — Only specific voter IDs'),
    ]

    title             = models.CharField(max_length=50)
    start_date        = models.DateTimeField()
    end_date          = models.DateTimeField()
    status            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_by        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="elections"
    )
    eligibility_type  = models.CharField(
        max_length=10,
        choices=ELIGIBILITY_CHOICES,
        default='open'
    )
    # For domain: store "school.edu"
    # For id_list: store comma-separated IDs "ID001,ID002,ID003"
    # For open: leave blank
    eligibility_value = models.TextField(
        blank=True,
        null=True,
        help_text="Domain: e.g. school.edu | ID List: e.g. ID001,ID002,ID003"
    )

    def __str__(self):
        return f"{self.title} ({self.status})"

    def sync_status(self):
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

    def is_eligible(self, user):
        """Check if a user is eligible to vote in this election."""
        if self.eligibility_type == 'open':
            return True

        elif self.eligibility_type == 'domain':
            # Check if user email ends with the specified domain
            domain = (self.eligibility_value or '').strip()
            return user.email.endswith(f'@{domain}')

        elif self.eligibility_type == 'id_list':
            # Check if user voter_id is in the comma-separated list
            id_list = [
                vid.strip()
                for vid in (self.eligibility_value or '').split(',')
                if vid.strip()
            ]
            return user.voter_id in id_list

        return False


class Candidate(models.Model):
    STATUS_CHOICES = [
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    election  = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="candidates"
    )
    bio       = models.TextField(blank=True, null=True)
    photo_url = models.URLField(blank=True)
    status    = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    class Meta:
        unique_together = [('user', 'election')]

    def __str__(self):
        return f"{self.user.username} - {self.election.title} ({self.status})"


class VoterParticipation(models.Model):
    class Meta:
        unique_together = [('user', 'election')]

    user     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="voters"
    )
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="participations"
    )
    voted_at = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - ({self.voted_at})"


class Votes(models.Model):
    token     = models.UUIDField(default=uuid.uuid4, editable=False)
    election  = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    voted_at  = models.DateTimeField()

    def __str__(self):
        return str(self.token)
    
    