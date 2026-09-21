"""
Rate limit tests for money-movement endpoints.

Rate limiting is disabled globally in tests (conftest sets
RATELIMIT_ENABLE=False) and enabled explicitly here.
"""

from decimal import Decimal

from django.core.cache import cache
from django.urls import reverse

from accounts.models import CustomUser, UserType
from wallet.models import Wallet


def _make_client(email, balance=Decimal("50000.00")):
    """Create a client user with a funded wallet."""
    user = CustomUser.objects.create_user(
        email=email,
        password="testpass123",
        user_type=UserType.CLIENT,
    )
    Wallet.objects.create(client_profile=user.client_profile, balance=balance)
    return user


class TestTransferRateLimit:
    """Test transfer abuse protection (10/min per user)."""

    def test_transfer_blocked_after_ten(self, client, db, settings):
        """Test 11th rapid transfer POST returns 403."""
        settings.RATELIMIT_ENABLE = True
        cache.clear()
        _make_client("sender@test.com")
        _make_client("receiver@test.com")
        client.login(email="sender@test.com", password="testpass123")
        url = reverse("wallet:transfer")

        for _ in range(10):
            response = client.post(
                url,
                {
                    "recipient_email": "receiver@test.com",
                    "amount": "10.00",
                    "description": "rate test",
                },
            )
            assert response.status_code == 200

        response = client.post(
            url,
            {
                "recipient_email": "receiver@test.com",
                "amount": "10.00",
                "description": "rate test",
            },
        )
        assert response.status_code == 403


class TestWithdrawRateLimit:
    """Test withdraw abuse protection (10/min per user)."""

    def test_withdraw_blocked_after_ten(self, client, db, settings):
        """Test 11th rapid withdraw POST returns 403."""
        settings.RATELIMIT_ENABLE = True
        cache.clear()
        _make_client("withdrawer@test.com")
        client.login(email="withdrawer@test.com", password="testpass123")
        url = reverse("wallet:withdraw")

        for _ in range(10):
            response = client.post(url, {"amount": "5.00", "description": "rate test"})
            assert response.status_code == 200

        response = client.post(url, {"amount": "5.00", "description": "rate test"})
        assert response.status_code == 403
