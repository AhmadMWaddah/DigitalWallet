"""
Celery configuration for Digital Wallet project.

This module initializes the Celery application and loads tasks from installed apps.
"""

import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")

# Create the Celery application
app = Celery("DigitalWallet")

# Load configuration from Django settings
# Using namespace 'CELERY' means settings should be prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
# This will look for tasks.py in each app directory
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Test task to verify Celery is working correctly."""
    print(f"Request: {self.request!r}")
    return "Debug task completed successfully"
