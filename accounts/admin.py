from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser



# CUSTOM USER ADMIN


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'username',
        'email',
        'voter_id',
        'role',
        'is_active',
        'date_joined'
    )

    list_filter = (
        'role',
        'is_active'
    )

    search_fields = (
        'username',
        'email',
        'voter_id'
    )

    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('iVote Info', {
            'fields': (
                'role',
                'voter_id'
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('iVote Info', {
            'fields': (
                'role',
                'voter_id'
            )
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + (
                'is_superuser',
                'user_permissions',
                'groups',
            )
        return self.readonly_fields