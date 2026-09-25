from django.db import models

from apps.audit.mixins import TimeStampedModel, UUIDModel


class VehicleCategory(models.TextChoices):
    COMMERCIAL = "commercial", "Commercial"
    PRIVATE = "private", "Private"


class Vehicle(UUIDModel, TimeStampedModel):
    registration_number = models.CharField(max_length=15, unique=True, db_index=True)
    vehicle_type = models.CharField(max_length=20, choices=VehicleCategory.choices, default=VehicleCategory.PRIVATE)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    fuel_type = models.ForeignKey("masters.FuelType", on_delete=models.PROTECT)
    manufacturing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    owner = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="vehicles")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["registration_number"]),
        ]

    def __str__(self):
        return f"{self.registration_number} — {self.make} {self.model}"
