from django.contrib import admin
from .models import Election, Contest, ContestCandidate, ElectoralRoll, Vote


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):

    list_display = ('title', 'status', 'start_date', 'end_date', 'created_by', 'emails_sent')
    list_filter  = ('status',)
    search_fields = ('title',)
    ordering     = ('-start_date',)
    readonly_fields = ('status', 'emails_sent')


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):

    list_display  = ('title', 'election', 'voting_method', 'seats', 'order')
    list_filter   = ('voting_method',)
    search_fields = ('title', 'election__title')
    ordering      = ('election', 'order')


@admin.register(ContestCandidate)
class ContestCandidateAdmin(admin.ModelAdmin):

    list_display  = ('name', 'contest', 'order')
    search_fields = ('name', 'contest__title')
    ordering      = ('contest', 'order')


@admin.register(ElectoralRoll)
class ElectoralRollAdmin(admin.ModelAdmin):

    list_display  = ('email', 'election', 'used', 'used_at')
    list_filter   = ('used', 'election')
    search_fields = ('email',)
    ordering      = ('election', 'email')
    readonly_fields = ('token', 'used', 'used_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):

    list_display  = ('contest_candidate', 'electoral_roll', 'rank')
    list_filter   = ('contest_candidate__contest__election',)
    ordering      = ('electoral_roll',)
    readonly_fields = ('electoral_roll', 'contest_candidate', 'rank')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
    
    