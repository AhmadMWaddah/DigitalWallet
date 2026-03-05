"""
Tests for accounts app signals.

Verifies automatic profile creation based on user_type.
"""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import ClientProfile, StaffProfile, UserType

CustomUser = get_user_model()


@pytest.mark.django_db
class TestProfileCreationSignals:
    """Test automatic profile creation signals."""

    def test_creating_staff_user_auto_creates_staff_profile(self):
        """Test that creating a staff user automatically creates a StaffProfile."""
        staff_user = CustomUser.objects.create_user(
            email="staff-signal@test.com", password="testpass123", user_type=UserType.STAFF
        )

        # Should have a staff_profile
        assert hasattr(staff_user, "staff_profile")
        assert isinstance(staff_user.staff_profile, StaffProfile)
        assert staff_user.staff_profile.role == StaffProfile.Role.LABOR

    def test_creating_client_user_auto_creates_client_profile(self):
        """Test that creating a client user automatically creates a ClientProfile."""
        client_user = CustomUser.objects.create_user(
            email="client-signal@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        # Should have a client_profile
        assert hasattr(client_user, "client_profile")
        assert isinstance(client_user.client_profile, ClientProfile)
        assert client_user.client_profile.kyc_verified is False

    def test_creating_superuser_auto_creates_staff_profile(self):
        """Test that creating a superuser automatically creates a StaffProfile."""
        superuser = CustomUser.objects.create_superuser(
            email="admin-signal@test.com", password="adminpass123"
        )

        # Superuser should have staff_profile
        assert hasattr(superuser, "staff_profile")
        assert isinstance(superuser.staff_profile, StaffProfile)
        assert superuser.staff_profile.role == StaffProfile.Role.LABOR

    def test_profile_user_field_correctly_set(self):
        """Test that profile's user field is correctly set to the creating user."""
        user = CustomUser.objects.create_user(
            email="profile-link@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        profile = user.client_profile
        assert profile.user == user
        assert profile.user.email == "profile-link@test.com"

    def test_multiple_users_create_separate_profiles(self):
        """Test that multiple users create separate profile instances."""
        user1 = CustomUser.objects.create_user(
            email="user1@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        user2 = CustomUser.objects.create_user(
            email="user2@test.com", password="testpass123", user_type=UserType.CLIENT
        )

        # Each should have their own profile
        assert user1.client_profile != user2.client_profile
        assert user1.client_profile.user == user1
        assert user2.client_profile.user == user2

    def test_staff_profile_role_default(self):
        """Test that StaffProfile role defaults to LABOR."""
        staff_user = CustomUser.objects.create_user(
            email="staff-default@test.com", password="testpass123", user_type=UserType.STAFF
        )

        assert staff_user.staff_profile.role == StaffProfile.Role.LABOR

    def test_staff_profile_role_admin(self):
        """Test creating staff user with ADMIN role."""
        staff_user = CustomUser.objects.create_user(
            email="admin-user@test.com", password="testpass123", user_type=UserType.STAFF
        )

        # Update role to ADMIN
        staff_user.staff_profile.role = StaffProfile.Role.ADMIN
        staff_user.staff_profile.save()

        # Refresh from database
        staff_user.refresh_from_db()
        assert staff_user.staff_profile.role == StaffProfile.Role.ADMIN
