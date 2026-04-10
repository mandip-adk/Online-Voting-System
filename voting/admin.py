from django.contrib import admin
from .models import Election, Candidate, VoterParticipation, Votes

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display  = ['title', 'status', 'start_date', 'end_date', 'created_by']  # ← added created_by
    list_filter   = ['status']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display  = ['user', 'election', 'status', 'bio', 'photo_url']  # ← added status
    list_filter   = ['status']  # ← filter by pending/approved/rejected
    actions       = ['approve_candidates', 'reject_candidates']

    def approve_candidates(self, request, queryset):
        queryset.update(status='approved')
    approve_candidates.short_description = "Approve selected candidates"

    def reject_candidates(self, request, queryset):
        queryset.update(status='rejected')
    reject_candidates.short_description = "Reject selected candidates"

@admin.register(VoterParticipation)
class VoteParticipationAdmin(admin.ModelAdmin):
    list_display = ['user', 'election', 'voted_at']

@admin.register(Votes)
class VotesAdmin(admin.ModelAdmin):
    list_display = ['token', 'election', 'candidate', 'voted_at']