"""
Registration form for client users.
"""

from django import forms
from django.contrib.auth import get_user_model

from accounts.models import UserType

CustomUser = get_user_model()


class ClientRegistrationForm(forms.ModelForm):
    """
    Form for client registration.

    Allows new users to create an account with email and password.
    """

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        help_text="At least 8 characters long.",
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        help_text="Enter the same password as above.",
    )

    class Meta:
        model = CustomUser
        fields = ["email", "password1", "password2"]

    def clean_email(self):
        """Validate email is not already registered."""
        email = self.cleaned_data.get("email")
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_password2(self):
        """Validate passwords match."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")

        if len(password1) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

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
