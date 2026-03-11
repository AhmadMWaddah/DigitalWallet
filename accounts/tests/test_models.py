"""
Tests for accounts app models.

Covers CustomUser, StaffProfile, and ClientProfile models.
"""

import pytest
from django.contrib.auth import get_user_model

from accounts.models import ClientProfile, StaffProfile, UserType

CustomUser = get_user_model()


# -- CustomUser Model Tests


@pytest.mark.django_db
class TestCustomUserCreation:
    """Test CustomUser model creation."""

    def test_create_user_with_email_success(self):
        """Test creating a user with email works correctly."""
        user = CustomUser.objects.create_user(email="test@example.com", password="testpass123")

        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.user_type == UserType.CLIENT
        assert user.is_verified is False
        assert user.is_staff is False
        assert user.is_active is True

    def test_create_user_email_normalized(self):
        """Test that email domain is normalized (lowercase)."""
        # Note: Django's normalize_email only lowercases the domain part
        user = CustomUser.objects.create_user(email="TEST@EXAMPLE.COM", password="testpass123")

        # Domain is normalized to lowercase, local part preserved
        assert user.email == "TEST@example.com"

    def test_create_user_without_email_raises_error(self):
        """Test that creating user without email raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            CustomUser.objects.create_user(email=None, password="testpass123")

        assert "Email address is required" in str(excinfo.value)

    def test_create_user_with_empty_email_raises_error(self):
        """Test that creating user with empty email raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            CustomUser.objects.create_user(email="", password="testpass123")

        assert "Email address is required" in str(excinfo.value)

    def test_create_user_with_user_type_staff(self):
        """Test creating a staff user."""
        user = CustomUser.objects.create_user(
            email="staff@example.com", password="testpass123", user_type=UserType.STAFF
        )

        assert user.user_type == UserType.STAFF

    def test_create_user_with_extra_fields(self):
        """Test creating user with extra fields like is_verified."""
        user = CustomUser.objects.create_user(
            email="verified@example.com", password="testpass123", is_verified=True
        )

        assert user.is_verified is True


@pytest.mark.django_db
class TestCustomUserSuperuser:
    """Test CustomUser superuser creation."""

    def test_create_superuser_success(self):
        """Test creating a superuser with all permissions."""
        superuser = CustomUser.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        assert superuser.email == "admin@example.com"
        assert superuser.check_password("adminpass123")
        assert superuser.user_type == UserType.STAFF
        assert superuser.is_verified is True
        assert superuser.is_staff is True
        assert superuser.is_superuser is True

    def test_create_superuser_is_staff_false_raises_error(self):
        """Test that creating superuser with is_staff=False raises error."""
        with pytest.raises(ValueError) as excinfo:
            CustomUser.objects.create_superuser(
                email="admin2@example.com", password="adminpass123", is_staff=False
            )

        assert "Superuser must have is_staff=True" in str(excinfo.value)

    def test_create_superuser_is_superuser_false_raises_error(self):
        """Test that creating superuser with is_superuser=False raises error."""
        with pytest.raises(ValueError) as excinfo:
            CustomUser.objects.create_superuser(
                email="admin3@example.com", password="adminpass123", is_superuser=False
            )

        assert "Superuser must have is_superuser=True" in str(excinfo.value)


@pytest.mark.django_db
class TestCustomUserProperties:
    """Test CustomUser model properties and methods."""

    def test_user_str_representation(self):
        """Test user string representation returns email."""
        user = CustomUser.objects.create_user(email="strtest@example.com", password="testpass123")

        assert str(user) == "strtest@example.com"

    def test_get_short_name_returns_email_local_part(self):
        """Test get_short_name returns email local part."""
        user = CustomUser.objects.create_user(email="john.doe@example.com", password="testpass123")

        assert user.get_short_name() == "john.doe"

    def test_is_client_property(self):
        """Test is_client property returns True for CLIENT type."""
        client = CustomUser.objects.create_user(
            email="client@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        assert client.is_client is True

        staff = CustomUser.objects.create_user(
            email="staff@example.com", password="testpass123", user_type=UserType.STAFF
        )

        assert staff.is_client is False

    def test_is_staff_user_property(self):
        """Test is_staff_user property returns True for STAFF type."""
        staff = CustomUser.objects.create_user(
            email="staff@example.com", password="testpass123", user_type=UserType.STAFF
        )

        assert staff.is_staff_user is True

        client = CustomUser.objects.create_user(
            email="client@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        assert client.is_staff_user is False


# -- Profile Model Tests


@pytest.mark.django_db
class TestStaffProfile:
    """Test StaffProfile model."""

    def test_create_staff_profile(self):
        """Test creating a staff profile."""
        staff_user = CustomUser.objects.create_user(
            email="staffprofile@example.com", password="testpass123", user_type=UserType.STAFF
        )

        profile = StaffProfile.objects.get(user=staff_user)

        assert profile.user == staff_user
        assert profile.role == StaffProfile.Role.LABOR

    def test_staff_profile_str_representation(self):
        """Test staff profile string representation."""
        staff_user = CustomUser.objects.create_user(
            email="staffstr@example.com", password="testpass123", user_type=UserType.STAFF
        )

        profile = StaffProfile.objects.get(user=staff_user)

        assert "Labor" in str(profile)
        assert "staffstr@example.com" in str(profile)


@pytest.mark.django_db
class TestClientProfile:
    """Test ClientProfile model."""

    def test_create_client_profile(self):
        """Test creating a client profile."""
        client_user = CustomUser.objects.create_user(
            email="clientprofile@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        profile = ClientProfile.objects.get(user=client_user)

        assert profile.user == client_user
        assert profile.kyc_verified is False

    def test_client_profile_with_full_name(self):
        """Test client profile with full name."""
        client_user = CustomUser.objects.create_user(
            email="namedclient@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        profile = ClientProfile.objects.get(user=client_user)
        profile.full_name = "John Doe"
        profile.save()

        assert profile.full_name == "John Doe"

    def test_client_profile_str_representation(self):
        """Test client profile string representation."""
        client_user = CustomUser.objects.create_user(
            email="clientstr@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        profile = ClientProfile.objects.get(user=client_user)

        assert "clientstr@example.com" in str(profile)


# -- Signal Tests


@pytest.mark.django_db
class TestProfileCreationSignals:
    """Test automatic profile creation signals."""

    def test_creating_staff_user_auto_creates_staff_profile(self):
        """Test that creating a staff user automatically creates a StaffProfile."""
        staff_user = CustomUser.objects.create_user(
            email="signalstaff@example.com", password="testpass123", user_type=UserType.STAFF
        )

        # Should have a staff_profile
        assert hasattr(staff_user, "staff_profile")
        assert isinstance(staff_user.staff_profile, StaffProfile)

    def test_creating_client_user_auto_creates_client_profile(self):
        """Test that creating a client user automatically creates a ClientProfile."""
        client_user = CustomUser.objects.create_user(
            email="signalclient@example.com", password="testpass123", user_type=UserType.CLIENT
        )

        # Should have a client_profile
        assert hasattr(client_user, "client_profile")
        assert isinstance(client_user.client_profile, ClientProfile)

    def test_creating_superuser_auto_creates_staff_profile(self):
        """Test that creating a superuser automatically creates a StaffProfile."""
        superuser = CustomUser.objects.create_superuser(
            email="superadmin@example.com", password="adminpass123"
        )

        # Superuser should have staff_profile
        assert hasattr(superuser, "staff_profile")
        assert isinstance(superuser.staff_profile, StaffProfile)
