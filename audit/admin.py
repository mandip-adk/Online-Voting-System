from django.contrib import admin
from .models import AuditRequest


@admin.register(AuditRequest)
class AuditRequestAdmin(admin.ModelAdmin):

    list_display  = ('election', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('election__title', 'reason')
    ordering      = ('-created_at',)

    