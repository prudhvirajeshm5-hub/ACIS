from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.inspections.models import Inspection

from .forms import QCDecisionForm
from .services import record_qc_decision


@login_required
@permission_required("qc.add_qcreview", raise_exception=True)
def qc_review(request, pk):
    inspection = get_object_or_404(
        Inspection.objects.select_related("mis", "mis__customer", "mis__vehicle", "mis__insurance_company", "field_executive")
        .prefetch_related("item_results__condition", "item_results__item", "glass_results", "photos", "videos", "documents"),
        pk=pk,
    )

    if request.method == "POST":
        form = QCDecisionForm(request.POST)
        if form.is_valid():
            record_qc_decision(
                inspection=inspection, qc_executive=request.user,
                decision=form.cleaned_data["decision"], remarks=form.cleaned_data["remarks"],
            )
            messages.success(request, f"QC decision recorded for {inspection.mis.mis_number}.")
            return redirect("mis:list")
    else:
        form = QCDecisionForm()

    flagged_items = [r for r in inspection.item_results.all() if not r.condition.is_positive]
    flagged_glass = [r for r in inspection.glass_results.all() if not r.condition.is_positive]

    return render(request, "qc/qc_review.html", {
        "inspection": inspection, "mis": inspection.mis, "form": form,
        "flagged_items": flagged_items, "flagged_glass": flagged_glass,
        "previous_reviews": inspection.qc_reviews.select_related("qc_executive")[:5],
    })
