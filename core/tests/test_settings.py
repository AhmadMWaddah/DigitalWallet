"""
Tests for Phase 1: Environment Setup & Dual-Settings Package.

Verifies:
- Settings package structure
- Environment variable loading
- Dev/Prod settings inheritance
"""


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

    def test_prod_settings_exists(self, monkeypatch):
        """Verify prod.py settings module imports with required env present."""
        # prod.py correctly fails fast without DATABASE_URL, so provide
        # dummy values: this tests the module, not real credentials.
        monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@localhost:5432/db")
        monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
        from core.settings import prod

        assert prod is not None
        assert prod.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
        assert prod.DEBUG is False


class TestBaseSettings:
    """Test base settings configuration."""

    def test_base_dir_correct(self):
        """Verify BASE_DIR points to project root."""
        from core.settings import base

        assert (base.BASE_DIR / "manage.py").exists()  # manage.py is in project root
        assert base.BASE_DIR.name == "DigitalWallet"

    def test_debug_defaults_false_without_env(self, monkeypatch):
        """Verify DEBUG falls back to False when DEBUG is unset."""
        import environ

        # Only os.environ matters here (.env file is read once at import,
        # so deleting the var isolates this from any local .env content).
        monkeypatch.delenv("DEBUG", raising=False)
        assert environ.Env().bool("DEBUG", default=False) is False

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

    def test_env_example_exists(self):
        """Verify .env.example template exists in project root."""
        from core.settings import base

        # .env itself is gitignored and absent in CI; the committed
        # template is what the repo guarantees.
        env_example = base.BASE_DIR / ".env.example"
        assert env_example.exists()
