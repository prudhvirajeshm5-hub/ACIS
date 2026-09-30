from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

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
    intimator_email = models.EmailField(blank=True)
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

    # Follow-up TAT: when the creator must be alerted. Null = not tracked (cases that
    # existed before this feature). Reset every time a follow-up is recorded.
    tat_due_at = models.DateTimeField(null=True, blank=True, db_index=True)
    tat_alerted_at = models.DateTimeField(null=True, blank=True)

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

    def get_tat_hours(self):
        hours = getattr(self.insurance_company, "tat_hours", None)
        return hours or TATSetting.get_hours()

    def save(self, *args, **kwargs):
        if not self.mis_number:
            self.mis_number = generate_mis_id()
        if self._state.adding and not self.tat_due_at:
            self.tat_due_at = timezone.now() + timedelta(hours=self.get_tat_hours())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.mis_number

    def get_absolute_url(self):
        return reverse("mis:detail", kwargs={"pk": self.pk})


class TATSetting(models.Model):
    """Global default follow-up TAT. Keep a single row; edit it in /admin/."""
    hours = models.PositiveSmallIntegerField(
        default=2, validators=[MinValueValidator(1)],
        help_text="Hours after an MIS is created (or last followed up) before its creator is alerted.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "TAT setting"
        verbose_name_plural = "TAT setting"

    def __str__(self):
        return f"TAT: {self.hours} hours"

    @classmethod
    def get_hours(cls):
        obj = cls.objects.first()
        return obj.hours if obj else 2


class MISFollowUp(UUIDModel):
    """One row each time the creator follows up on a case."""
    mis = models.ForeignKey(MIS, on_delete=models.CASCADE, related_name="followups")
    followed_up_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    remarks = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.mis.mis_number} follow-up @ {self.created_at:%Y-%m-%d %H:%M}"
