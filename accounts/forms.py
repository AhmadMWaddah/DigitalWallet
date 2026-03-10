"""
Accounts app forms.

Custom forms for authentication and password reset.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm as BasePasswordResetForm
from django.core.exceptions import ValidationError

from accounts.models import UserType

CustomUser = get_user_model()


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
