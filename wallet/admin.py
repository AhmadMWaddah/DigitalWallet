"""
Wallet app admin configuration.

Registers Wallet and Transaction models for Django admin.
"""

from django.contrib import admin

from .models import Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Admin configuration for Wallet model."""

    list_display = [
        "id",
        "client_profile",
        "balance",
        "is_frozen",
        "created_at",
    ]

    list_filter = ["is_frozen", "created_at"]

    search_fields = [
        "client_profile__user__email",
        "client_profile__full_name",
    ]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Wallet Information",
            {
                "fields": (
                    "client_profile",
                    "balance",
                    "is_frozen",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model."""

    list_display = [
        "id",
        "wallet",
        "amount",
        "type",
        "status",
        "created_at",
    ]

    list_filter = ["type", "status", "created_at"]

    search_fields = [
        "wallet__client_profile__user__email",
        "reference_id",
        "description",
    ]

    readonly_fields = ["created_at"]

    fieldsets = (
        (
            "Transaction Details",
            {
                "fields": (
                    "wallet",
                    "counterparty_wallet",
                    "amount",
                    "type",
                    "status",
                    "description",
                    "reference_id",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": ("metadata",),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamp",
            {
                "fields": ("created_at",),
                "classes": ("collapse",),
            },
        ),
    )
