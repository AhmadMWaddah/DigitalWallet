"""
Django test settings.

CI-optimized: in-memory SQLite, fast hashers, eager Celery, no network.
Rate limiting off by default (targeted tests re-enable per case).
"""

from .base import *

SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Same default as conftest.py: shared locmem cache would leak limit
# counters between cases, and eager-off Celery needs a broker.
RATELIMIT_ENABLE = False
