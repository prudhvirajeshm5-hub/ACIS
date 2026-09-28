from django.utils import timezone

from .models import Attendance


def attendance_today(request):
    """Gives every page today's attendance row so the shift banner can render."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    record = Attendance.objects.filter(user=user, date=timezone.localdate()).first()
    return {"att_today": record}
