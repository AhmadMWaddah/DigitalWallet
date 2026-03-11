"""
Django production settings.

Inherits from base.py and overrides settings for production deployment.
"""

import environ

from .base import *

# Disable debug mode for production
DEBUG = False

# Allowed hosts must be set via environment variable in production
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Database - PostgreSQL for production (SupaBase)
DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# Static files with WhiteNoise for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Celery settings for production
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True

# Logging for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
