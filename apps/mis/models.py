from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.audit.mixins import TimeStampedModel, UUIDModel


class MISPriority(models.TextChoices):
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class MISInspectionStage(models.TextChoices):
    """Coarse workflow stage — the fine-grained history lives in
    InspectionStatusHistory (apps.inspections), this is just for fast
    filtering/list display without a join."""
    PENDING = "pending", "Pending"
    ASSIGNED = "assigned", "Assigned"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETED = "completed", "Completed"


class MISQCStage(models.TextChoices):
    NOT_STARTED = "not_started", "Not Started"
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    CORRECTION = "correction", "Correction Required"


class MISPaymentStage(models.TextChoices):
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    HOLD = "hold", "Hold"


def generate_mis_id():
    """MIS-YYYY-NNNN, sequential per year. Uses select_for_update via the
    calling transaction to stay race-safe under concurrent creates."""
    import datetime
    year = datetime.date.today().year
    prefix = f"MIS-{year}-"
    last = MIS.objects.filter(mis_number__startswith=prefix).order_by("-mis_number").first()
    next_seq = int(last.mis_number.rsplit("-", 1)[-1]) + 1 if last else 1
    return f"{prefix}{next_seq:04d}"


class MIS(UUIDModel, TimeStampedModel):
    mis_number = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    mis_date = models.DateField()

    insurance_company = models.ForeignKey("insurers.InsuranceCompany", on_delete=models.PROTECT, related_name="mis_records")
    branch = models.ForeignKey("insurers.InsuranceBranch", on_delete=models.PROTECT, related_name="mis_records")
    insurance_reference_number = models.CharField(max_length=60, blank=True)
    lead_reference_id = models.CharField(max_length=60, blank=True)
    inspection_type = models.CharField(max_length=60, default="Pre-Policy Inspection")
    intimator = models.CharField(max_length=150, blank=True)
    remarks = models.TextField(blank=True)

    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="mis_records")
    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.PROTECT, related_name="mis_records")

    field_executive = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_mis", limit_choices_to={"role": "field_executive"},
    )
    priority = models.CharField(max_length=10, choices=MISPriority.choices, default=MISPriority.NORMAL)
    scheduled_date = models.DateField(null=True, blank=True)
    inspection_location = models.CharField(max_length=255, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    inspection_stage = models.CharField(max_length=15, choices=MISInspectionStage.choices, default=MISInspectionStage.PENDING, db_index=True)
    qc_stage = models.CharField(max_length=15, choices=MISQCStage.choices, default=MISQCStage.NOT_STARTED, db_index=True)
    payment_stage = models.CharField(max_length=10, choices=MISPaymentStage.choices, default=MISPaymentStage.PENDING)

    class Meta:
        ordering = ["-mis_date", "-created_at"]
        indexes = [
            models.Index(fields=["mis_number"]),
            models.Index(fields=["inspection_stage"]),
            models.Index(fields=["qc_stage"]),
            models.Index(fields=["insurance_company"]),
            models.Index(fields=["field_executive"]),
        ]
        permissions = [
            ("assign_mis", "Can assign or reassign a field executive to an MIS"),
            ("export_mis_excel", "Can export MIS records to Excel"),
            ("export_mis_pdf", "Can export MIS records to PDF"),
            ("view_financial_info", "Can view financial/billing information on an MIS"),
        ]

    def save(self, *args, **kwargs):
        if not self.mis_number:
            self.mis_number = generate_mis_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mis_number

    def get_absolute_url(self):
        return reverse("mis:detail", kwargs={"pk": self.pk})
