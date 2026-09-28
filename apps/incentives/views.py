from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import TargetForm
from .models import IncentiveTarget
from .services import build_progress


@login_required
def my_targets(request):
    today = timezone.localdate()
    mine = IncentiveTarget.objects.filter(employee=request.user).select_related("employee")
    active = [build_progress(t, today) for t in mine if t.start_date <= today <= t.end_date]
    upcoming = [build_progress(t, today) for t in mine if t.start_date > today]
    past = [build_progress(t, today) for t in mine.filter(end_date__lt=today)[:10]]
    return render(request, "incentives/my_targets.html", {"active": active, "upcoming": upcoming, "past": past})


@login_required
@permission_required("incentives.manage_targets", raise_exception=True)
def manage_targets(request):
    today = timezone.localdate()
    if request.method == "POST":
        form = TargetForm(request.POST)
        if form.is_valid():
            target = form.save(commit=False)
            target.assigned_by = request.user
            target.save()
            messages.success(request, f"Target of {target.target_count} set for {target.employee.get_full_name() or target.employee.username}.")
            return redirect("incentives:manage")
    else:
        form = TargetForm(initial={"start_date": today, "end_date": today})
    rows = [build_progress(t, today) for t in IncentiveTarget.objects.select_related("employee")]
    return render(request, "incentives/manage.html", {"form": form, "rows": rows, "today": today})


@login_required
@permission_required("incentives.manage_targets", raise_exception=True)
@require_POST
def delete_target(request, pk):
    target = get_object_or_404(IncentiveTarget, pk=pk)
    target.delete()
    messages.success(request, "Target removed.")
    return redirect("incentives:manage")
