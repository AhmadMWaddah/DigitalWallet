"""
Django production settings.

Inherits from base.py and overrides settings for production deployment.
"""

import environ

from .base import *

# -- Security & Debug

DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])

# Security headers for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Content Security Policy (optional, recommended for production)
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC = ("'self'", "https://unpkg.com")
# CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com")
# CSP_FONT_SRC = ("'self'", "https://cdnjs.cloudflare.com")
# CSP_IMG_SRC = ("'self'", "data:", "https:")

# -- Database (PostgreSQL via SupaBase)

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# -- Static Files (WhiteNoise)

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -- Celery & Redis

CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=env("CELERY_BROKER_URL"))
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True

# -- Email Configuration

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Digital Wallet <noreply@yourdomain.com>")

# -- Logging for Production

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "wallet": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "operations": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "analytics": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
