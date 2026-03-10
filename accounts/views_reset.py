"""
Accounts app views.

Password reset views for client users.
"""

from django.contrib.auth import get_user_model, login
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views import View

from .forms import ClientPasswordResetForm, ClientSetPasswordForm
from .models import UserType

CustomUser = get_user_model()


class ClientPasswordResetView(View):
    """
    Password reset view for client users.

    Allows clients to request password reset via email.
    """

    template_name = "accounts/password_reset.html"
    email_subject = "Digital Wallet - Password Reset"

    def get(self, request):
        """Display password reset form."""
        form = ClientPasswordResetForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        """Process password reset request."""
        form = ClientPasswordResetForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]

            try:
                user = CustomUser.objects.get(email=email)

                # Only process for CLIENT users
                if user.user_type == UserType.CLIENT:
                    # Generate token
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)

                    # Create reset link
                    reset_link = request.build_absolute_uri(
                        f"/accounts/reset-password/{uid}/{token}/"
                    )

                    # Send email
                    send_mail(
                        self.email_subject,
                        f"Click the link to reset your password:\n\n{reset_link}\n\nThis link expires in 24 hours.",
                        "noreply@digitalwallet.com",
                        [user.email],
                        fail_silently=False,
                    )

            except CustomUser.DoesNotExist:
                # Don't reveal if email exists (security)
                pass

        # Always show success message (security best practice)
        return render(
            request,
            "accounts/password_reset_done.html",
            {"email": form.cleaned_data.get("email", "")},
        )


class ClientPasswordResetConfirmView(View):
    """
    Password reset confirmation view for client users.

    Allows clients to set a new password using the reset link.
    """

    template_name = "accounts/password_reset_confirm.html"

    def get(self, request, uidb64, token):
        """Display password reset confirmation form."""
        # Validate token
        user = self.validate_token(uidb64, token)

        if user is None:
            return render(
                request,
                "accounts/password_reset_invalid.html",
                {"valid": False},
            )

        form = ClientSetPasswordForm()
        return render(
            request,
            self.template_name,
            {"form": form, "valid": True, "uidb64": uidb64, "token": token},
        )

    def post(self, request, uidb64, token):
        """Process new password."""
        # Validate token
        user = self.validate_token(uidb64, token)

        if user is None:
            return render(
                request,
                "accounts/password_reset_invalid.html",
                {"valid": False},
            )

        form = ClientSetPasswordForm(request.POST)

        if form.is_valid():
            # Set new password
            user.set_password(form.cleaned_data["new_password1"])
            user.save()

            # Auto-login
            login(request, user)

            return redirect("wallet:dashboard")

        return render(
            request,
            self.template_name,
            {"form": form, "valid": True, "uidb64": uidb64, "token": token},
        )

    def validate_token(self, uidb64, token):
        """Validate reset token and return user if valid."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)

            # Check if user is CLIENT and token is valid
            if user.user_type == UserType.CLIENT and default_token_generator.check_token(
                user, token
            ):
                return user

        except (CustomUser.DoesNotExist, ValueError):
            pass

        return None
