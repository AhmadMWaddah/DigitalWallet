"""
Custom user managers for accounts app.

Handles user and superuser creation with email-based authentication.
"""

from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom manager for creating users and superusers with email.

    Handles user creation with email as the unique identifier.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with the given email and password.

        Args:
            email: The user's email address (required, normalized)
            password: The user's password (required)
            **extra_fields: Additional fields like user_type, full_name, etc.

        Returns:
            CustomUser: The created user instance

        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError("Email address is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with admin privileges.

        Args:
            email: The superuser's email address
            password: The superuser's password
            **extra_fields: Additional fields (automatically sets is_staff, is_superuser)

        Returns:
            CustomUser: The created superuser instance
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("user_type", "STAFF")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(email, password, **extra_fields)
