from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.audit.mixins import UUIDModel


class TargetMetric(models.TextChoices):
    INSPECTIONS = "inspections", "Inspections submitted"
    QC = "qc", "QC reviews completed"
    MIS = "mis", "MIS created"


class IncentiveTarget(UUIDModel):
    """A target of N cases that an admin sets for one employee over a date range."""
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="incentive_targets")
    metric = models.CharField(max_length=20, choices=TargetMetric.choices, default=TargetMetric.INSPECTIONS)
    target_count = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField()
    incentive_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]
        permissions = [("manage_targets", "Can assign targets to employees")]

    def __str__(self):
        return f"{self.employee} - {self.target_count} ({self.start_date} to {self.end_date})"

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before the start date.")
