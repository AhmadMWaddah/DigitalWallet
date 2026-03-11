from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Authentication & Profiles"

    def ready(self):
        """Import signals when the app is ready."""
        from . import signals  # noqa: F401
