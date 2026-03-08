"""
Tests for wallet management commands.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from accounts.models import UserType
from wallet.models import Wallet

CustomUser = get_user_model()


@pytest.mark.django_db
class TestSeedWalletsCommand:
    """Test seed_wallets management command."""

    def test_seed_command_creates_users(self):
        """Test seed command creates specified number of users."""
        call_command("seed_wallets", count=3, prefix="testseed")

        # Check users were created
        users = CustomUser.objects.filter(email__startswith="testseed")
        assert users.count() == 3

    def test_seed_command_creates_wallets(self):
        """Test seed command creates wallets for users."""
        call_command("seed_wallets", count=2, prefix="wallettest")

        # Check wallets were created
        users = CustomUser.objects.filter(email__startswith="wallettest")
        for user in users:
            assert hasattr(user.client_profile, "wallet")
            wallet = user.client_profile.wallet
            assert wallet.balance > 0  # Should have initial funding

    def test_seed_command_creates_transactions(self):
        """Test seed command creates transaction history."""
        call_command("seed_wallets", count=2, prefix="txntest")

        # Check transactions were created
        users = CustomUser.objects.filter(email__startswith="txntest")
        profiles = [u.client_profile for u in users]
        wallets = Wallet.objects.filter(client_profile__in=profiles)

        total_transactions = sum(w.transactions.count() for w in wallets)
        assert total_transactions > 0  # Should have some transactions

    def test_seed_command_clear_flag(self):
        """Test seed command --clear flag removes existing data."""
        # Create initial dummy data
        call_command("seed_wallets", count=2, prefix="cleartest")

        # Verify created
        initial_count = CustomUser.objects.filter(email__startswith="cleartest").count()
        assert initial_count == 2

        # Clear and recreate
        call_command("seed_wallets", count=2, prefix="cleartest", clear=True)

        # Should still have 2 (cleared and recreated)
        final_count = CustomUser.objects.filter(email__startswith="cleartest").count()
        assert final_count == 2

    def test_seed_command_users_have_correct_password(self):
        """Test seeded users have testpass123 password."""
        call_command("seed_wallets", count=1, prefix="pwdtest")

        user = CustomUser.objects.get(email="pwdtest1@example.com")
        assert user.check_password("testpass123")

    def test_seed_command_users_are_clients(self):
        """Test seeded users have CLIENT user_type."""
        call_command("seed_wallets", count=2, prefix="typetest")

        users = CustomUser.objects.filter(email__startswith="typetest")
        for user in users:
            assert user.user_type == UserType.CLIENT
