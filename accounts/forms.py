"""
Accounts app forms.

Custom forms for authentication and password reset.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.core.exceptions import ValidationError

from accounts.models import UserType

CustomUser = get_user_model()


class ClientRegistrationForm(forms.ModelForm):
    """
    Form for client registration.

    Allows new users to create an account with email and password.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "class": "form-input"}),
        help_text="At least 8 characters long.",
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••", "class": "form-input"}),
        help_text="Enter the same password as above.",
    )

    class Meta:
        model = CustomUser
        fields = ["email"]
        widgets = {
            "email": forms.EmailInput(
                attrs={"placeholder": "you@example.com", "class": "form-input"}
            )
        }

    def clean_email(self):
        """Validate email is not already registered."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        return password2

    def save(self, commit=True):
        """Create user with CLIENT user_type."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.user_type = UserType.CLIENT
        user.is_verified = False

        if commit:
            user.save()

        return user


class ClientPasswordResetForm(BasePasswordResetForm):
    """
    Password reset form for client users only.

    Only allows password reset for users with CLIENT user_type.
    """

    email = forms.EmailField(
        label="Email",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "class": "form-input",
                "placeholder": "you@example.com",
                "autofocus": True,
            }
        ),
    )

    def clean_email(self):
        """Validate email belongs to a client user."""
        email = self.cleaned_data["email"]

        try:
            user = CustomUser.objects.get(email=email)

            # Only allow CLIENT users to reset via this form
            if user.user_type != UserType.CLIENT:
                raise ValidationError("Please use the staff password reset system.")

        except CustomUser.DoesNotExist:
            # Don't reveal if email exists or not (security best practice)
            pass

        return email


class ClientPasswordChangeForm(PasswordChangeForm):
    """
    Password change form styled for the client security page.
    """

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)

        field_config = {
            "old_password": {
                "placeholder": "Enter your current password",
                "autocomplete": "current-password",
            },
            "new_password1": {
                "placeholder": "Choose a new password",
                "autocomplete": "new-password",
            },
            "new_password2": {
                "placeholder": "Confirm your new password",
                "autocomplete": "new-password",
            },
        }

        for field_name, attrs in field_config.items():
            self.fields[field_name].widget.attrs.update(
                {
                    "class": "form-input",
                    **attrs,
                }
            )


class ClientSetPasswordForm(forms.Form):
    """
    Set password form for client users.
    """

    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "••••••••",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_new_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")

        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords do not match.")

        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")

        return password2


class KYCUploadForm(forms.Form):
    """Form for uploading a KYC identity document."""

    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
    MAX_SIZE_BYTES = 5 * 1024 * 1024

    document = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={"class": "form-input", "accept": ".pdf,.jpg,.jpeg,.png"}
        ),
        help_text="PDF, JPG, or PNG up to 5MB",
    )

    def clean_document(self):
        """Validate file type and size."""
        document = self.cleaned_data.get("document")
        if document is None:
            raise ValidationError("Please choose a document to upload.")

        suffix = f".{document.name.rsplit('.', 1)[-1].lower()}" if "." in document.name else ""
        if suffix not in self.ALLOWED_EXTENSIONS:
            raise ValidationError("Only PDF, JPG, and PNG files are accepted.")

        if document.size > self.MAX_SIZE_BYTES:
            raise ValidationError("File must be 5MB or smaller.")

        return document
