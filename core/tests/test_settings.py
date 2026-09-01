"""
Tests for Phase 1: Environment Setup & Dual-Settings Package.

Verifies:
- Settings package structure
- Environment variable loading
- Dev/Prod settings inheritance
"""

from pathlib import Path

import pytest


class TestSettingsStructure:
    """Test the settings package structure."""

    def test_settings_package_exists(self):
        """Verify settings package directory exists."""
        from core import settings

        assert settings is not None

    def test_base_settings_exists(self):
        """Verify base.py settings module exists."""
        from core.settings import base

        assert base is not None

    def test_dev_settings_exists(self):
        """Verify dev.py settings module exists."""
        from core.settings import dev

        assert dev is not None

    def test_prod_settings_exists(self):
        """Verify prod.py settings module exists."""
        from core.settings import prod

        assert prod is not None


class TestBaseSettings:
    """Test base settings configuration."""

    def test_base_dir_correct(self):
        """Verify BASE_DIR points to project root."""
        from core.settings import base

        assert (base.BASE_DIR / "manage.py").exists()  # manage.py is in project root
        assert base.BASE_DIR.name == "DigitalWallet"

    def test_debug_from_env(self):
        """Verify DEBUG is loaded from environment (True in dev)."""
        from core.settings import base

        # DEBUG is True because .env sets DEBUG=True for development
        assert base.DEBUG is True

    def test_installed_apps_default(self):
        """Verify default Django apps are installed."""
        from core.settings import base

        assert "django.contrib.admin" in base.INSTALLED_APPS
        assert "django.contrib.auth" in base.INSTALLED_APPS
        assert "django.contrib.contenttypes" in base.INSTALLED_APPS

    def test_templates_dir_configured(self):
        """Verify templates directory is configured."""
        from core.settings import base

        template_dirs = base.TEMPLATES[0]["DIRS"]
        assert any("templates" in str(d) for d in template_dirs)


class TestDevSettings:
    """Test development settings."""

    def test_debug_enabled_in_dev(self):
        """Verify DEBUG is True in dev settings."""
        from core.settings import dev

        assert dev.DEBUG is True

    def test_localhost_allowed_in_dev(self):
        """Verify localhost is in ALLOWED_HOSTS for dev."""
        from core.settings import dev

        assert "localhost" in dev.ALLOWED_HOSTS
        assert "127.0.0.1" in dev.ALLOWED_HOSTS

    def test_sqlite_database_in_dev(self):
        """Verify SQLite is used for dev database."""
        from core.settings import dev

        db_engine = dev.DATABASES["default"]["ENGINE"]
        assert "sqlite3" in db_engine


class TestEnvironmentVariables:
    """Test environment variable loading."""

    def test_secret_key_loaded(self):
        """Verify SECRET_KEY is loaded from environment."""
        from core.settings import base

        assert base.SECRET_KEY is not None
        assert base.SECRET_KEY != ""
        assert "change-me" not in base.SECRET_KEY.lower() or "django-insecure" in base.SECRET_KEY

    def test_env_file_exists(self):
        """Verify .env file exists in project root."""
        from core.settings import base

        env_file = base.BASE_DIR / ".env"
        assert env_file.exists()
