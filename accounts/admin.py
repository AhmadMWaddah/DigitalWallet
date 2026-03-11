"""
Admin configuration for accounts app.

Registers CustomUser and profile models for Django admin.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ClientProfile, CustomUser, StaffProfile, UserType

# -- Custom User Admin


@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for CustomUser model."""

    # -- Display Options

    list_display = ("email", "user_type", "is_verified", "is_staff", "is_active", "date_joined")
    list_filter = ("user_type", "is_verified", "is_staff", "is_active", "date_joined")
    search_fields = ("email",)
    ordering = ("-date_joined",)

    # -- Form Fields

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("User Type", {"fields": ("user_type", "is_verified")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important Dates", {"fields": ("date_joined",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "user_type", "password1", "password2", "is_verified"),
            },
        ),
    )

    readonly_fields = ("date_joined",)

    # -- Configuration

    ordering = ("-date_joined",)

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related("staff_profile", "client_profile")


# -- Profile Admins


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    """Admin configuration for StaffProfile model."""

    list_display = ("user", "role", "created_at", "updated_at")
    list_filter = ("role", "created_at")
    search_fields = ("user__email", "assigned_permissions")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("User Information", {"fields": ("user", "role")}),
        ("Permissions", {"fields": ("assigned_permissions",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for ClientProfile model."""

    list_display = ("user", "full_name", "company", "kyc_verified", "created_at", "updated_at")
    list_filter = ("kyc_verified", "created_at")
    search_fields = ("full_name", "company", "user__email", "phone")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Personal Information", {"fields": ("user", "full_name", "phone", "address")}),
        ("Professional Information", {"fields": ("company", "job_title")}),
        ("Verification", {"fields": ("kyc_verified",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
