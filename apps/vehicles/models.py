from django.db import models

from apps.audit.mixins import TimeStampedModel, UUIDModel


class Vehicle(UUIDModel, TimeStampedModel):
    registration_number = models.CharField(max_length=15, unique=True, db_index=True)
    vehicle_type = models.ForeignKey("masters.VehicleType", on_delete=models.PROTECT)
    make = models.ForeignKey("masters.VehicleMake", on_delete=models.PROTECT)
    model = models.ForeignKey("masters.VehicleModel", on_delete=models.PROTECT)
    fuel_type = models.ForeignKey("masters.FuelType", on_delete=models.PROTECT)
    manufacturing_year = models.PositiveSmallIntegerField()
    engine_number = models.CharField(max_length=40, blank=True)
    chassis_number = models.CharField(max_length=40, blank=True)
    owner = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="vehicles")

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["registration_number"]),
            models.Index(fields=["chassis_number"]),
            models.Index(fields=["engine_number"]),
        ]

    def __str__(self):
        return f"{self.registration_number} — {self.make} {self.model}"
