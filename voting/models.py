from django.db import models
from django.utils import timezone
import uuid


class Election(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active',  'Active'),
        ('closed',  'Closed'),
    ]

    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date  = models.DateTimeField()
    end_date    = models.DateTimeField()
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by  = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='elections'
    )
    emails_sent = models.BooleanField(default=False)  # track if voter emails sent

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

    def __str__(self):
        return self.title


class Contest(models.Model):

    METHOD_CHOICES = [
        ('plurality',     'Traditional (Plurality)'),
        ('ranked_choice', 'Ranked-Choice Voting'),
    ]

    election      = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='contests')
    title         = models.CharField(max_length=200)
    voting_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='plurality')
    seats         = models.PositiveIntegerField(default=1)  # number of winners
    order         = models.PositiveIntegerField(default=0)  # display order on ballot

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.election.title} — {self.title}"


class ContestCandidate(models.Model):

    contest     = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='candidates')
    name        = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)  # display order on ballot

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.contest.title})"


class ElectoralRoll(models.Model):

    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='electoral_roll')
    email    = models.EmailField()
    token    = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    used     = models.BooleanField(default=False)
    used_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('election', 'email')]

    def __str__(self):
        return f"{self.email} — {self.election.title} ({'voted' if self.used else 'not voted'})"


class Vote(models.Model):

    electoral_roll     = models.ForeignKey(ElectoralRoll, on_delete=models.CASCADE, related_name='votes')
    contest_candidate  = models.ForeignKey(ContestCandidate, on_delete=models.CASCADE, related_name='votes')
    rank               = models.PositiveIntegerField(null=True, blank=True)
    # rank is NULL for plurality votes
    # rank is 1, 2, 3... for ranked_choice votes

    class Meta:
        unique_together = [('electoral_roll', 'contest_candidate')]

    def __str__(self):
        return f"Vote by {self.electoral_roll.email} for {self.contest_candidate.name}"
    
    