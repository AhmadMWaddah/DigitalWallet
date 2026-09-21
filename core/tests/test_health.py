"""
Tests for the health endpoint.

Verifies:
- Healthy service returns 200 with db/cache status
- Database failure returns 503
- Cache failure returns 503
"""

import pytest
from django.db import OperationalError
from django.urls import reverse


@pytest.mark.django_db
class TestHealthEndpoint:
    """Test GET /health/ service status reporting."""

    def test_health_healthy(self, client):
        """Test healthy service returns 200 with ok statuses."""
        response = client.get(reverse("health"))

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["db"] == "ok"
        assert data["cache"] == "ok"

    def test_health_database_failure(self, client, monkeypatch):
        """Test database failure returns 503 unhealthy."""
        import core.views as core_views

        def _broken_db():
            raise OperationalError("db down")

        monkeypatch.setattr(core_views, "_check_database", _broken_db)

        response = client.get(reverse("health"))

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["db"] != "ok"

    def test_health_cache_failure(self, client, monkeypatch):
        """Test cache failure returns 503 unhealthy."""
        import core.views as core_views

        def _broken_cache():
            raise ConnectionError("cache down")

        monkeypatch.setattr(core_views, "_check_cache", _broken_cache)

        response = client.get(reverse("health"))

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["cache"] != "ok"
