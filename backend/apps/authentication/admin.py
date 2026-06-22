from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CustomerProfile, OTPVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone', 'email', 'full_name', 'is_store_owner', 'is_active')
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Info', {'fields': ('email', 'full_name')}),
        ('Permissions', {'fields': ('is_store_owner', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {'fields': ('phone',)}),
    )
    search_fields = ('phone', 'email')
    ordering = ('phone',)
    filter_horizontal = ()


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tenant', 'created_at')


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone', 'is_used', 'expires_at', 'attempt_count')
