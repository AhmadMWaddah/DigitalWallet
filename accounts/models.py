"""
Accounts app models.

CustomUser model with email-based authentication and user profiles.
"""

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# -- User Type Choices

class UserType(models.TextChoices):
    """User type enumeration for portal separation."""
    STAFF = 'STAFF', 'Staff'
    CLIENT = 'CLIENT', 'Client'


# -- Custom User Manager

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
            raise ValueError('Email address is required')
        
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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('user_type', UserType.STAFF)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


# -- Custom User Model

class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model using email as the unique identifier.
    
    Replaces username with email and adds user_type for portal separation.
    """
    
    # -- Core Fields
    
    email = models.EmailField(
        'Email Address',
        unique=True,
        max_length=255,
        help_text='Required. A valid email address.'
    )
    
    user_type = models.CharField(
        'User Type',
        max_length=10,
        choices=UserType.choices,
        default=UserType.CLIENT,
        help_text='Determines which portal the user can access.'
    )
    
    is_verified = models.BooleanField(
        'Email Verified',
        default=False,
        help_text='Indicates if the email has been verified.'
    )
    
    # -- Django Auth Fields
    
    is_staff = models.BooleanField(
        'Staff Status',
        default=False,
        help_text='Designates whether the user can log into admin site.'
    )
    
    is_active = models.BooleanField(
        'Active',
        default=True,
        help_text='Designates whether this user should be treated as active.'
    )
    
    date_joined = models.DateTimeField(
        'Date Joined',
        default=timezone.now,
        help_text='The date and time when the user joined.'
    )
    
    # -- Manager and Metadata
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by default
    
    class Meta:
        db_table = 'accounts_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's email as full name (or profile name if available)."""
        try:
            if hasattr(self, 'client_profile') and self.client_profile.full_name:
                return self.client_profile.full_name
            if hasattr(self, 'staff_profile') and self.staff_profile.role:
                return f'Staff ({self.staff_profile.role})'
        except (ClientProfile.DoesNotExist, StaffProfile.DoesNotExist):
            pass
        return self.email
    
    def get_short_name(self):
        """Return the user's email local part (before @)."""
        return self.email.split('@')[0]
    
    @property
    def is_client(self):
        """Check if user is a client."""
        return self.user_type == UserType.CLIENT
    
    @property
    def is_staff_user(self):
        """Check if user is staff (alias for is_staff for consistency)."""
        return self.user_type == UserType.STAFF or self.is_staff


# -- Profile Models

class StaffProfile(models.Model):
    """
    Profile for staff users (Admins and Labor).
    
    Contains role-specific information for internal team members.
    """
    
    # -- Role Choices
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        LABOR = 'LABOR', 'Labor'
    
    # -- Fields
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        help_text='The user this profile belongs to.'
    )
    
    role = models.CharField(
        'Role',
        max_length=10,
        choices=Role.choices,
        default=Role.LABOR,
        help_text='Staff role: Admin or Labor.'
    )
    
    assigned_permissions = models.TextField(
        'Assigned Permissions',
        blank=True,
        help_text='Comma-separated list of special permissions.'
    )
    
    created_at = models.DateTimeField(
        'Created At',
        auto_now_add=True,
        help_text='When this profile was created.'
    )
    
    updated_at = models.DateTimeField(
        'Updated At',
        auto_now=True,
        help_text='When this profile was last updated.'
    )
    
    class Meta:
        db_table = 'accounts_staff_profile'
        verbose_name = 'Staff Profile'
        verbose_name_plural = 'Staff Profiles'
    
    def __str__(self):
        return f'{self.get_role_display()} - {self.user.email}'


class ClientProfile(models.Model):
    """
    Profile for client users (wallet holders).
    
    Contains personal and contact information for platform users.
    """
    
    # -- Fields
    
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='client_profile',
        help_text='The user this profile belongs to.'
    )
    
    full_name = models.CharField(
        'Full Name',
        max_length=255,
        blank=True,
        help_text='User\'s full legal name.'
    )
    
    company = models.CharField(
        'Company',
        max_length=255,
        blank=True,
        help_text='Company or organization name.'
    )
    
    job_title = models.CharField(
        'Job Title',
        max_length=255,
        blank=True,
        help_text='Current job title or occupation.'
    )
    
    phone = models.CharField(
        'Phone Number',
        max_length=20,
        blank=True,
        help_text='Contact phone number.'
    )
    
    address = models.TextField(
        'Address',
        blank=True,
        help_text='Physical address.'
    )
    
    kyc_verified = models.BooleanField(
        'KYC Verified',
        default=False,
        help_text='Know Your Customer verification status.'
    )
    
    created_at = models.DateTimeField(
        'Created At',
        auto_now_add=True,
        help_text='When this profile was created.'
    )
    
    updated_at = models.DateTimeField(
        'Updated At',
        auto_now=True,
        help_text='When this profile was last updated.'
    )
    
    class Meta:
        db_table = 'accounts_client_profile'
        verbose_name = 'Client Profile'
        verbose_name_plural = 'Client Profiles'
    
    def __str__(self):
        return f'{self.full_name or "Client"} - {self.user.email}'
