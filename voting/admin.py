from django.contrib import admin
from .models import Election, Candidate, VoterParticipation, Votes

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'start_date', 'end_date']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['user', 'election', 'bio', 'photo_url']

@admin.register(VoterParticipation)
class VoteParticipationAdmin(admin.ModelAdmin):
    list_display = ['user', 'election', 'voted_at']

@admin.register(Votes)
class VotesAdmin(admin.ModelAdmin):
    list_display = ['token', 'election', 'candidate', 'voted_at']


