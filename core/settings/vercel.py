"""
Django Vercel deployment settings.

Inherits from prod.py and overrides for Vercel serverless environment.
"""

import os

# flake8: noqa: F403 F405
from .prod import *

# -- Vercel Serverless Configuration

# Vercel sets these environment variables automatically
DEBUG = False
ALLOWED_HOSTS = list(env.list("ALLOWED_HOSTS", default=[".vercel.app", ".now.sh"]))

# -- Static Files (Vercel handles static files)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# WhiteNoise for static files (still useful for Vercel)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -- Database (SupaBase PostgreSQL)

DATABASES = {
    "default": env.db("DATABASE_URL"),
}

# -- Redis (Use Upstash for serverless Redis)

CELERY_BROKER_URL = env("UPSTASH_REDIS_URL", default=env("CELERY_BROKER_URL"))
CELERY_RESULT_BACKEND = env("UPSTASH_REDIS_URL", default=env("CELERY_RESULT_BACKEND"))

# -- Celery Configuration (Limited on Vercel)

# Note: Celery doesn't work well on Vercel serverless
# Use Vercel Cron Jobs or external task queue instead
CELERY_TASK_ALWAYS_EAGER = True  # Run tasks synchronously on Vercel

# -- Security (Vercel provides HTTPS)

SECURE_SSL_REDIRECT = False  # Vercel handles SSL
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# -- Allowed Hosts for Vercel

if "ALLOWED_HOSTS" not in env:
    ALLOWED_HOSTS = [".vercel.app", ".now.sh", "localhost", "127.0.0.1"]

# -- Vercel Serverless Timeout

# Increase timeout for serverless functions (max 10s on Hobby, 60s on Pro)
VERCEL_MAX_DURATION = 10  # seconds

# -- Logging for Vercel

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
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
    },
}
