from django.conf import settings
from django.db import models

from apps.audit.mixins import UUIDModel


class NotificationChannel(models.TextChoices):
    IN_APP = "in_app", "In-app"
    EMAIL = "email", "Email"
    SMS = "sms", "SMS"
    WHATSAPP = "whatsapp", "WhatsApp"
    PUSH = "push", "Push"


class Notification(UUIDModel):
    """
    Only IN_APP is actually delivered in this phase (see services.notify
    below). The channel field and this model's shape are what let
    email/SMS/WhatsApp/push get added later as pure delivery-backend work
    without touching every place that currently calls notify().
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=10, choices=NotificationChannel.choices, default=NotificationChannel.IN_APP)
    title = models.CharField(max_length=150)
    body = models.TextField(blank=True)
    link = models.CharField(max_length=255, blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
