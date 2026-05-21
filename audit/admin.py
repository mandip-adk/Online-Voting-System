from django.contrib import admin
from .models import AuditRequest


@admin.register(AuditRequest)
class AuditRequestAdmin(admin.ModelAdmin):

    list_display = (
        'candidate',
        'election',
        'status',
        'created_at'
    )

    list_filter = ('status',)

    search_fields = (
        'candidate__user__username',
        'election__title'
    )

    ordering = ('-created_at',)