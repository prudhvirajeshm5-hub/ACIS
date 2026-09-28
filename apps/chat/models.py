import uuid

from django.conf import settings
from django.db import models

from apps.audit.mixins import UUIDModel


def chat_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    ext = "".join(c for c in ext if c.isalnum())[:5] or "bin"
    return f"chat/{uuid.uuid4()}.{ext}"


class ConversationKind(models.TextChoices):
    EVERYONE = "everyone", "All staff"
    DIRECT = "direct", "Direct"
    GROUP = "group", "Group"


class Conversation(UUIDModel):
    kind = models.CharField(max_length=10, choices=ConversationKind.choices, default=ConversationKind.GROUP)
    name = models.CharField(max_length=100, blank=True)
    # For direct chats: the two user ids sorted, so a pair only ever has one chat.
    direct_key = models.CharField(max_length=60, null=True, blank=True, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"{self.get_kind_display()} {self.pk}"


class Membership(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_memberships")
    last_read_id = models.BigIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["conversation", "user"], name="uniq_chat_member")]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="chat_messages")
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to=chat_upload_path, blank=True)
    attachment_kind = models.CharField(max_length=10, blank=True)  # "image" or "video"
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_mime = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["id"]
        indexes = [models.Index(fields=["conversation", "id"], name="chat_msg_conv_id_idx")]
