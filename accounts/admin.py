from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):

    list_display = (
        'email',
        'first_name',
        'last_name',
        'role',
        'organization_name',
        'country',
        'is_active',
        'date_joined',
    )

    list_filter = ('role', 'is_active')

    search_fields = ('email', 'first_name', 'last_name', 'organization_name')

    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('iVote Info', {'fields': ('role', 'organization_name', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name',
                'role', 'organization_name', 'country',
                'password1', 'password2'
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return self.readonly_fields + ('is_superuser', 'user_permissions', 'groups')
        return self.readonly_fields
    
    