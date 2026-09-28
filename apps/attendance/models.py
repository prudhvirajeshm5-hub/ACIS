from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.audit.mixins import UUIDModel


class Attendance(UUIDModel):
    """One row per employee per day. Start Shift creates it, End Shift closes it."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records")
    date = models.DateField(db_index=True)
    shift_start = models.DateTimeField()
    shift_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-date", "-shift_start"]
        constraints = [models.UniqueConstraint(fields=["user", "date"], name="uniq_attendance_user_date")]
        permissions = [("view_all_attendance", "Can view all employees' attendance")]

    def __str__(self):
        return f"{self.user} - {self.date}"

    @property
    def worked(self):
        if self.shift_end:
            return self.shift_end - self.shift_start
        return None

    @property
    def worked_display(self):
        w = self.worked
        if w is None:
            return "-"
        mins = int(w.total_seconds() // 60)
        return f"{mins // 60}h {mins % 60:02d}m"

    @property
    def status(self):
        if self.shift_end is None:
            return "On shift" if self.date == timezone.localdate() else "Shift not ended"
        full = float(getattr(settings, "ATTENDANCE_FULL_DAY_HOURS", 8))
        half = float(getattr(settings, "ATTENDANCE_HALF_DAY_HOURS", 4))
        hours = self.worked.total_seconds() / 3600
        if hours >= full:
            return "Present"
        if hours >= half:
            return "Half day"
        return "Short hours"

    @property
    def status_class(self):
        return {
            "Present": "b-good", "Half day": "b-warn", "Short hours": "b-bad",
            "On shift": "b-info", "Shift not ended": "b-bad",
        }.get(self.status, "b-neutral")
