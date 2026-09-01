"""
Django signals for accounts app.

Automatically creates profile instances when users are created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ClientProfile, CustomUser, StaffProfile, UserType


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create appropriate profile based on user_type when a user is created.

    Args:
        sender: The model class (CustomUser)
        instance: The actual user instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional signal arguments
    """
    if created:
        if instance.user_type == UserType.STAFF:
            StaffProfile.objects.create(user=instance)
        elif instance.user_type == UserType.CLIENT:
            ClientProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the associated profile when a user is saved.

    This ensures profile changes are persisted when user is updated.
    """
    # Save associated profiles if they exist
    if hasattr(instance, "staff_profile"):
        instance.staff_profile.save()
    if hasattr(instance, "client_profile"):
        instance.client_profile.save()
