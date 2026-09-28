"""Progress maths for targets. compute() is pure so it is easy to test."""


def compute(target_count, completed, today_count, start, end, today):
    pending = max(target_count - completed, 0)
    percent = min(100, int(completed * 100 / target_count)) if target_count else 0
    if today > end:
        days_left = 0
    else:
        days_left = (end - max(today, start)).days + 1
    per_day = -(-pending // days_left) if days_left > 0 else pending  # ceiling division
    return {
        "target_count": target_count, "completed": completed, "pending": pending,
        "percent": percent, "today": today_count, "days_left": days_left,
        "per_day": per_day, "achieved": completed >= target_count,
    }


def count_completed(user, metric, start, end):
    """How many cases this employee completed between start and end (inclusive)."""
    if metric == "inspections":
        from apps.inspections.models import Inspection
        return Inspection.objects.filter(
            field_executive=user, is_submitted=True,
            submitted_at__date__gte=start, submitted_at__date__lte=end,
        ).count()
    if metric == "qc":
        from apps.qc.models import QCReview
        return QCReview.objects.filter(
            qc_executive=user, reviewed_at__date__gte=start, reviewed_at__date__lte=end,
        ).count()
    if metric == "mis":
        from apps.mis.models import MIS
        return MIS.objects.filter(
            created_by=user, created_at__date__gte=start, created_at__date__lte=end,
        ).count()
    return 0


def build_progress(target, today):
    completed = count_completed(target.employee, target.metric, target.start_date, target.end_date)
    today_count = count_completed(target.employee, target.metric, today, today)
    data = compute(target.target_count, completed, today_count, target.start_date, target.end_date, today)
    data.update({
        "target": target, "id": target.id, "employee": target.employee,
        "label": target.get_metric_display(), "start_date": target.start_date,
        "end_date": target.end_date, "incentive_amount": target.incentive_amount,
    })
    return data
