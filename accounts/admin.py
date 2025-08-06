from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser

    search_fields = ['email', 'first_name', 'last_name']
    list_display = ['email', 'first_name', 'last_name', 'is_agent', 'is_customer', 'is_staff', 'is_active']
    list_filter = ['is_agent', 'is_customer', 'is_staff', 'is_active']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'username')}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_agent', 'is_customer',
                'groups', 'user_permissions'
            )
        }),
        ('Important Dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'password1', 'password2',
                'is_staff', 'is_active', 'is_agent', 'is_customer'
            ),
        }),
    )

    ordering = ['email']
