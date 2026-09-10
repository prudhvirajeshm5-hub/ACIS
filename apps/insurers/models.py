from django.db import models

from apps.audit.mixins import ActivatableModel, TimeStampedModel, UUIDModel


class InsuranceCompany(UUIDModel, TimeStampedModel, ActivatableModel):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=20, unique=True)
    gstin = models.CharField(max_length=15, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=15, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Insurance companies"

    def __str__(self):
        return self.name


class InsuranceBranch(UUIDModel, TimeStampedModel, ActivatableModel):
    company = models.ForeignKey(InsuranceCompany, on_delete=models.PROTECT, related_name="branches")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, blank=True)
    district = models.ForeignKey("masters.District", on_delete=models.PROTECT, related_name="insurance_branches")
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["company__name", "name"]
        constraints = [models.UniqueConstraint(fields=["company", "name"], name="uniq_branch_per_company")]
        indexes = [models.Index(fields=["company"])]

    def __str__(self):
        return f"{self.company.name} — {self.name}"
