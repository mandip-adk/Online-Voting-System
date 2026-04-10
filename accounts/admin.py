from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Identity', {'fields': ('role', 'voter_id')}),  # ← added voter_id
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'voter_id']  # ← added
    list_filter  = ['role']  # ← filter by role in sidebar

admin.site.register(CustomUser, CustomUserAdmin)