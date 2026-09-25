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
    companies = models.ManyToManyField(InsuranceCompany, related_name="branches", blank=True)
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, blank=True)
    district = models.ForeignKey("masters.District", on_delete=models.PROTECT, related_name="insurance_branches")
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
