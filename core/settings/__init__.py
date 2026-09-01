"""
Django settings package.

Default to development settings if DJANGO_SETTINGS_MODULE is not set.
"""

import os

# Default to dev settings if not specified
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")
