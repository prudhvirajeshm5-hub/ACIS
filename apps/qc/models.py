from django.conf import settings
from django.db import models

from apps.audit.mixins import UUIDModel


class QCDecision(models.TextChoices):
    RECOMMENDED = "recommended", "Recommended"
    NOT_RECOMMENDED = "not_recommended", "Not Recommended"
    NEED_CORRECTION = "need_correction", "Need Correction"
    REINSPECTION_REQUIRED = "reinspection_required", "Reinspection Required"


class QCReview(UUIDModel):
    """
    One row per QC decision. Kept append-only (no update/delete in
    admin.py) — a corrected re-review creates a *new* QCReview row linked
    via `supersedes`, so the full decision history for an inspection is
    always reconstructable, per the spec's "maintain an immutable audit
    history" requirement.
    """
    inspection = models.ForeignKey("inspections.Inspection", on_delete=models.CASCADE, related_name="qc_reviews")
    qc_executive = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="qc_reviews")
    decision = models.CharField(max_length=25, choices=QCDecision.choices)
    remarks = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    supersedes = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="superseded_by")

    class Meta:
        ordering = ["-reviewed_at"]
        indexes = [models.Index(fields=["inspection", "-reviewed_at"])]

    def __str__(self):
        return f"{self.inspection.mis.mis_number} — {self.get_decision_display()}"
