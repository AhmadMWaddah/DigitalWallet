"""
Rate limit tests for authentication endpoints.

Rate limiting is disabled globally in tests (conftest sets
RATELIMIT_ENABLE=False) and enabled explicitly here.
"""

from django.core.cache import cache
from django.urls import reverse


class TestLoginRateLimit:
    """Test login brute-force protection (5/min per IP)."""

    def test_login_blocked_after_five_attempts(self, client, db, settings):
        """Test 6th rapid login POST returns 403."""
        settings.RATELIMIT_ENABLE = True
        cache.clear()
        url = reverse("accounts:login")

        for _ in range(5):
            response = client.post(url, {"email": "brute@test.com", "password": "wrong"})
            assert response.status_code == 200

        response = client.post(url, {"email": "brute@test.com", "password": "wrong"})
        assert response.status_code == 403


class TestPasswordResetRateLimit:
    """Test password reset abuse protection (3/min per IP)."""

    def test_reset_blocked_after_three_requests(self, client, db, settings):
        """Test 4th rapid reset POST returns 403."""
        settings.RATELIMIT_ENABLE = True
        cache.clear()
        url = reverse("accounts:password_reset_client")

        for _ in range(3):
            response = client.post(url, {"email": "nobody@test.com"})
            assert response.status_code == 200

        response = client.post(url, {"email": "nobody@test.com"})
        assert response.status_code == 403
