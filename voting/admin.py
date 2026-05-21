from django.contrib import admin
from .models import Election, Candidate, VoterParticipation, Votes



# ELECTION ADMIN


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'status',
        'start_date',
        'end_date',
        'created_by'
    )

    list_filter = ('status',)

    search_fields = ('title',)

    ordering = ('-start_date',)

    readonly_fields = ('status',)



# CANDIDATE ADMIN

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'election',
        'status',
        'bio',
        'photo_url'
    )

    list_filter = ('status',)

    search_fields = (
        'user__username',
        'election__title'
    )

    actions = [
        'approve_candidates',
        'reject_candidates'
    ]

    def approve_candidates(self, request, queryset):
        queryset.update(status='approved')

    approve_candidates.short_description = (
        "Approve selected candidates"
    )

    def reject_candidates(self, request, queryset):
        queryset.update(status='rejected')

    reject_candidates.short_description = (
        "Reject selected candidates"
    )


# VOTER PARTICIPATION ADMIN (READ ONLY)


@admin.register(VoterParticipation)
class VoteParticipationAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'election',
        'voted_at'
    )

    list_filter = ('election',)

    search_fields = ('user__username',)

    ordering = ('-voted_at',)

    readonly_fields = (
        'user',
        'election',
        'voted_at'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser



# VOTES ADMIN (READ ONLY)


@admin.register(Votes)
class VotesAdmin(admin.ModelAdmin):

    list_display = (
        'token',
        'election',
        'candidate',
        'voted_at'
    )

    list_filter = ('election',)

    ordering = ('-voted_at',)

    readonly_fields = (
        'token',
        'election',
        'candidate',
        'voted_at'
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser