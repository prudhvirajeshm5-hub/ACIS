from django.conf import settings
from django.db import models


class AuditAction(models.TextChoices):
    CREATE = "create", "Created"
    UPDATE = "update", "Updated"
    DELETE = "delete", "Deleted"
    APPROVE = "approve", "Approved"
    REJECT = "reject", "Rejected"
    ASSIGN = "assign", "Assigned"
    UPLOAD = "upload", "Uploaded"
    DOWNLOAD = "download", "Downloaded"
    LOGIN = "login", "Logged in"
    LOGOUT = "logout", "Logged out"
    EXPORT = "export", "Exported"
    GENERATE_REPORT = "generate_report", "Generated report"


class AuditLog(models.Model):
    """
    Append-only. Nothing in this app exposes an edit or delete view/API —
    see admin.py, where add/change/delete permissions are all disabled.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=32, choices=AuditAction.choices)
    module = models.CharField(max_length=64)  # e.g. "mis", "inspections", "qc"
    object_repr = models.CharField(max_length=255)  # human-readable, e.g. "MIS-2026-0142"
    object_id = models.CharField(max_length=64, blank=True)
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["module", "object_id"]),
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} {self.action} {self.module}:{self.object_repr}"
