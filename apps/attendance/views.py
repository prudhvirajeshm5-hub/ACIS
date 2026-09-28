from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Attendance


def _back(request):
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(reverse("attendance:home"))


@login_required
@require_POST
def start_shift(request):
    record, created = Attendance.objects.get_or_create(
        user=request.user, date=timezone.localdate(),
        defaults={"shift_start": timezone.now()},
    )
    if created:
        messages.success(request, f"Shift started at {timezone.localtime(record.shift_start):%I:%M %p}.")
    else:
        messages.info(request, "You have already started your shift today.")
    return _back(request)


@login_required
@require_POST
def end_shift(request):
    record = Attendance.objects.filter(user=request.user, date=timezone.localdate(), shift_end__isnull=True).first()
    if record is None:
        messages.info(request, "There is no open shift to end.")
    else:
        record.shift_end = timezone.now()
        record.save(update_fields=["shift_end"])
        messages.success(request, f"Shift ended. You worked {record.worked_display} today.")
    return _back(request)


@login_required
def attendance_home(request):
    today = timezone.localdate()
    today_record = Attendance.objects.filter(user=request.user, date=today).first()

    my_records = list(Attendance.objects.filter(user=request.user, date__gte=today - timedelta(days=30)))
    done = [r for r in my_records if r.shift_end]
    total_seconds = sum(r.worked.total_seconds() for r in done)
    summary = {
        "shifts": len(done),
        "hours": f"{total_seconds / 3600:.1f}",
        "avg": f"{(total_seconds / 3600 / len(done)):.1f}" if done else "0.0",
    }

    ctx = {"today": today, "today_record": today_record, "my_records": my_records, "summary": summary}

    if request.user.has_perm("attendance.view_all_attendance"):
        day = parse_date(request.GET.get("date", "")) or today
        team = list(Attendance.objects.filter(date=day).select_related("user"))
        present_ids = {r.user_id for r in team}
        absent = get_user_model().objects.filter(is_active=True, is_superuser=False).exclude(pk__in=present_ids)
        ctx.update({"can_view_all": True, "team": team, "absent": absent, "team_date": day})

    return render(request, "attendance/attendance.html", ctx)
