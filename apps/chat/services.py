from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import F

from .models import Conversation, ConversationKind, Membership, Message


def person_name(user):
    return (user.get_full_name() or user.username) if user else "Deleted user"


def ensure_everyone(user):
    conv, _ = Conversation.objects.get_or_create(direct_key="everyone", defaults={"kind": ConversationKind.EVERYONE, "name": "All Staff"})
    Membership.objects.get_or_create(conversation=conv, user=user)
    return conv


def unread_total(user):
    return Message.objects.filter(
        conversation__memberships__user=user,
        id__gt=F("conversation__memberships__last_read_id"),
    ).exclude(sender=user).count()


def classify_upload(f):
    """Photos and videos only. Uses the same content sniffing as inspection uploads."""
    from apps.inspections.validators import _sniff_mime
    mime = _sniff_mime(f)
    if mime in settings.ALLOWED_PHOTO_TYPES:
        kind, limit = "image", settings.MAX_PHOTO_SIZE_MB
    elif mime in settings.ALLOWED_VIDEO_TYPES:
        kind, limit = "video", int(getattr(settings, "CHAT_MAX_VIDEO_MB", 50))
    else:
        raise ValidationError("Only photos (JPG, PNG, WebP) and videos (MP4, MOV, WebM) can be shared.")
    if f.size > limit * 1024 * 1024:
        raise ValidationError(f"That {kind} is too large (maximum {limit} MB).")
    return kind, mime
