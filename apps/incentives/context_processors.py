from django.utils import timezone

from .models import IncentiveTarget
from .services import build_progress


def target_strips(request):
    """Active targets for the logged-in employee, shown at the top of every page."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    today = timezone.localdate()
    targets = IncentiveTarget.objects.filter(employee=user, start_date__lte=today, end_date__gte=today).select_related("employee")
    return {"target_strips": [build_progress(t, today) for t in targets]}
