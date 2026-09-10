from django.db import models

from apps.audit.mixins import ActivatableModel, TimeStampedModel, UUIDModel


class NamedMaster(UUIDModel, TimeStampedModel, ActivatableModel):
    """Shared shape for simple lookup tables: a name, optional code, active flag."""
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=30, blank=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name


class State(NamedMaster):
    class Meta(NamedMaster.Meta):
        constraints = [models.UniqueConstraint(fields=["name"], name="uniq_state_name")]


class District(NamedMaster):
    state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="districts")

    class Meta(NamedMaster.Meta):
        constraints = [models.UniqueConstraint(fields=["state", "name"], name="uniq_district_per_state")]
        indexes = [models.Index(fields=["state"])]


class City(NamedMaster):
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="cities")

    class Meta(NamedMaster.Meta):
        constraints = [models.UniqueConstraint(fields=["district", "name"], name="uniq_city_per_district")]
        verbose_name_plural = "Cities"


class VehicleType(NamedMaster):
    """Hatchback, Sedan, SUV, Two-wheeler, Commercial, etc."""


class VehicleMake(NamedMaster):
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, related_name="makes")


class VehicleModel(NamedMaster):
    make = models.ForeignKey(VehicleMake, on_delete=models.PROTECT, related_name="models")

    class Meta(NamedMaster.Meta):
        verbose_name = "Vehicle Model"


class FuelType(NamedMaster):
    """Petrol, Diesel, CNG, Electric, Hybrid."""


class InspectionStatus(NamedMaster):
    sequence = models.PositiveSmallIntegerField(default=0, help_text="Controls display/workflow order.")

    class Meta(NamedMaster.Meta):
        ordering = ["sequence", "name"]
        verbose_name_plural = "Inspection statuses"


class QCStatus(NamedMaster):
    sequence = models.PositiveSmallIntegerField(default=0)

    class Meta(NamedMaster.Meta):
        ordering = ["sequence", "name"]
        verbose_name_plural = "QC statuses"


class TicketStatus(NamedMaster):
    class Meta(NamedMaster.Meta):
        verbose_name_plural = "Ticket statuses"


class PaymentMode(NamedMaster):
    """Cash, NEFT, UPI, Cheque, etc."""


class InspectionItemMaster(NamedMaster):
    """Configurable checklist parts — Front Bumper, Bonnet, Left Fender, etc.
    Do NOT hard-code the checklist anywhere else; it is always read from here."""
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta(NamedMaster.Meta):
        ordering = ["display_order", "name"]


class GlassItemMaster(NamedMaster):
    """Front Windshield, Rear Windshield, Quarter Glass, Sunroof, etc."""
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta(NamedMaster.Meta):
        ordering = ["display_order", "name"]


class AccessoryMaster(NamedMaster):
    """AC, Music System, Reverse Camera, Alloy Wheels, etc."""
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta(NamedMaster.Meta):
        ordering = ["display_order", "name"]


class ConditionOption(NamedMaster):
    """Safe / Damaged / Scratched / Dent / Broken / Repaired / Replaced /
    Not Available / Not Applicable — configurable so operations can add a
    new condition (e.g. 'Rusted') without a code change."""
    is_positive = models.BooleanField(default=True, help_text="True = no issue (e.g. Safe). False = flags QC attention.")


class VideoCategoryMaster(NamedMaster):
    """Exterior Walkaround, Engine Bay, Odometer, Damage Evidence, etc."""
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta(NamedMaster.Meta):
        ordering = ["display_order", "name"]
        verbose_name = "Video category"


class PhotoCategoryMaster(NamedMaster):
    """The fixed bulk-upload photo checklist (Front View, Engine Bay, ...)
    plus a free-form 'Additional Photos' slot for anything not covered.

    Mandatory slots (is_mandatory=True) hold exactly one photo per
    inspection — re-uploading a slot replaces its photo. Non-mandatory
    slots (e.g. 'Additional Photos') allow up to max_count photos per
    inspection instead of just one.
    """
    display_order = models.PositiveSmallIntegerField(default=0)
    is_mandatory = models.BooleanField(default=True)
    max_count = models.PositiveSmallIntegerField(
        default=1, help_text="Photos allowed per inspection for this slot. Mandatory slots are always 1."
    )

    class Meta(NamedMaster.Meta):
        ordering = ["display_order", "name"]
        verbose_name = "Photo category"
