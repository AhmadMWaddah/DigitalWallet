"""
Django development settings.

Inherits from base.py and overrides settings for local development.
"""

from .base import *

# Enable debug mode for development
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Internal IPs for debug toolbar (if added later)
INTERNAL_IPS = ["127.0.0.1"]

# Use SQLite for simple local development (override base DATABASES if needed)
# For PostgreSQL locally, set DATABASE_URL in .env
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Email backend for development (console output)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery settings for development
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True

# For testing: run tasks synchronously without a worker
CELERY_TASK_ALWAYS_EAGER = False

# -- Development Security Overrides (Insecure for Local Dev Only)

SESSION_COOKIE_SECURE = False  # Allow HTTP for local development
CSRF_COOKIE_SECURE = False  # Allow HTTP for local development
