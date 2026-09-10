from django.core.validators import RegexValidator
from django.db import models

from apps.audit.mixins import TimeStampedModel, UUIDModel

phone_validator = RegexValidator(r"^[6-9]\d{9}$", "Enter a valid 10-digit Indian mobile number.")


class Customer(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=10, validators=[phone_validator], db_index=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    state = models.ForeignKey("masters.State", null=True, blank=True, on_delete=models.SET_NULL)
    district = models.ForeignKey("masters.District", null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey("masters.City", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["mobile"]), models.Index(fields=["name"])]

    def __str__(self):
        return f"{self.name} ({self.mobile})"
