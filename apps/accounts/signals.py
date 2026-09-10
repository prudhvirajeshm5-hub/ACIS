# Reserved for account lifecycle signals (e.g. auto-creating a
# FieldExecutiveProfile when a user is saved with role=field_executive).
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import FieldExecutiveProfile, Role, User


@receiver(post_save, sender=User)
def ensure_field_executive_profile(sender, instance, created, **kwargs):
    if instance.role == Role.FIELD_EXECUTIVE:
        FieldExecutiveProfile.objects.get_or_create(user=instance)
