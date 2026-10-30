from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.action(description="Approve KYC for selected hosts")
def approve_kyc(modeladmin, request, queryset):
    queryset.update(kyc_status='verified', role='host')


@admin.action(description="Reject KYC for selected hosts")
def reject_kyc(modeladmin, request, queryset):
    queryset.update(kyc_status='rejected')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'kyc_status', 'phone', 'is_staff')
    list_filter = ('role', 'kyc_status', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone', 'aadhaar_no')
    actions = [approve_kyc, reject_kyc]

    fieldsets = UserAdmin.fieldsets + (
        ('ParkEase Role & KYC', {
            'fields': ('role', 'phone', 'aadhaar_no', 'kyc_status', 'photo', 'property_image', 'onboarding_completed')
        }),
    )
