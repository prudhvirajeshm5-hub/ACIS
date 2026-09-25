import os
import uuid

from django.conf import settings
from django.db import models

from apps.audit.mixins import TimeStampedModel, UUIDModel
from .validators import validate_document_file, validate_photo_file, validate_video_file


def photo_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"inspections/{instance.inspection.mis.mis_number}/photos/{uuid.uuid4()}.{ext}"


def video_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"inspections/{instance.inspection.mis.mis_number}/videos/{uuid.uuid4()}.{ext}"


def video_thumb_path(instance, filename):
    return f"inspections/{instance.inspection.mis.mis_number}/videos/thumbs/{uuid.uuid4()}.jpg"


def document_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower()
    return f"inspections/{instance.inspection.mis.mis_number}/documents/{uuid.uuid4()}.{ext}"


class InspectionPriority(models.TextChoices):
    NORMAL = "normal", "Normal"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Inspection(UUIDModel, TimeStampedModel):
    """One-to-one with MIS. Kept as a separate model (rather than folding
    everything into MIS) because MIS is the commercial/administrative
    record while Inspection is the field-work record — they have different
    lifecycles and, per the spec, different permission sets."""
    mis = models.OneToOneField("mis.MIS", on_delete=models.CASCADE, related_name="inspection")
    field_executive = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="inspections"
    )
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    odometer_reading = models.PositiveIntegerField(null=True, blank=True)
    engine_condition = models.CharField(max_length=100, blank=True)
    accessories_condition_notes = models.TextField(blank=True)

    chassis_number = models.CharField(max_length=60, blank=True)
    engine_number = models.CharField(max_length=60, blank=True)
    verified_fuel_type = models.ForeignKey(
        "masters.FuelType", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    verified_manufacturing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    vehicle_colour = models.CharField(max_length=40, blank=True)

    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_captured_at = models.DateTimeField(null=True, blank=True)

    is_submitted = models.BooleanField(default=False)
    # Guards against the double-submit race the spec calls out explicitly
    # ("prevent accidental duplicate submissions"): the unique-together-like
    # behaviour comes from checking is_submitted inside a transaction in
    # services.submit_inspection rather than at the DB level, since a
    # resubmission after a QC "Correction" decision is legitimate.

    class Meta:
        permissions = [
            ("accept_inspection", "Can accept an assigned inspection (field executive)"),
            ("start_inspection", "Can mark an inspection as started"),
            ("submit_inspection", "Can submit a completed inspection for QC"),
            ("assign_inspection", "Can assign an inspection to a field executive"),
            ("reassign_inspection", "Can reassign an inspection to a different field executive"),
            ("upload_photo", "Can upload inspection photos"),
            ("upload_video", "Can upload inspection videos"),
            ("download_media", "Can download inspection photos/videos/documents"),
        ]

    def __str__(self):
        return f"Inspection for {self.mis.mis_number}"


class InspectionItemResult(UUIDModel):
    """One row per configurable checklist part (Front Bumper, Bonnet, ...)."""
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="item_results")
    item = models.ForeignKey("masters.InspectionItemMaster", on_delete=models.PROTECT)
    condition = models.ForeignKey("masters.ConditionOption", on_delete=models.PROTECT)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["inspection", "item"], name="uniq_item_per_inspection")]

    def __str__(self):
        return f"{self.item} = {self.condition}"


class InspectionGlassResult(UUIDModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="glass_results")
    item = models.ForeignKey("masters.GlassItemMaster", on_delete=models.PROTECT)
    condition = models.ForeignKey("masters.ConditionOption", on_delete=models.PROTECT)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["inspection", "item"], name="uniq_glass_per_inspection")]


class InspectionAccessoryResult(UUIDModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="accessory_results")
    item = models.ForeignKey("masters.AccessoryMaster", on_delete=models.PROTECT)
    present = models.BooleanField(default=True)
    condition = models.ForeignKey("masters.ConditionOption", on_delete=models.PROTECT, null=True, blank=True)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["inspection", "item"], name="uniq_accessory_per_inspection")]


class PreviousInsurance(UUIDModel):
    inspection = models.OneToOneField(Inspection, on_delete=models.CASCADE, related_name="previous_insurance")
    previous_insurer = models.CharField(max_length=150, blank=True)
    policy_number = models.CharField(max_length=60, blank=True)
    policy_start_date = models.DateField(null=True, blank=True)
    policy_end_date = models.DateField(null=True, blank=True)
    had_previous_claim = models.BooleanField(default=False)
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    no_claim_bonus_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    policy_document = models.FileField(upload_to=document_upload_path, null=True, blank=True, validators=[validate_document_file])
    remarks = models.TextField(blank=True)


class DocumentType(models.TextChoices):
    RC = "rc", "RC (Registration Certificate)"
    INSURANCE = "insurance", "Insurance Policy Document"
    DL = "dl", "Driving License"
    OWNER_VERIFICATION = "owner_verification", "Registered Owner Verification"
    VEHICLE_NUMBER = "vehicle_number", "Vehicle Number Verification"
    ENGINE_NUMBER = "engine_number", "Engine Number Verification"
    CHASSIS_NUMBER = "chassis_number", "Chassis Number Verification"


class InspectionDocument(UUIDModel, TimeStampedModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=DocumentType.choices)
    file = models.FileField(upload_to=document_upload_path, null=True, blank=True, validators=[validate_document_file])
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["inspection", "document_type"], name="uniq_doctype_per_inspection")]


class PhotoCategory(models.TextChoices):
    FRONT = "front", "Front"
    REAR = "rear", "Rear"
    LEFT = "left", "Left"
    RIGHT = "right", "Right"
    INTERIOR = "interior", "Interior"
    ENGINE = "engine", "Engine"
    CHASSIS = "chassis", "Chassis"
    ODOMETER = "odometer", "Odometer"
    DOCUMENTS = "documents", "Documents"
    DAMAGE = "damage", "Damage"
    OTHER = "other", "Other"


class InspectionPhoto(UUIDModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="photos")
    category = models.CharField(max_length=20, choices=PhotoCategory.choices)
    original_filename = models.CharField(max_length=255)
    file = models.ImageField(upload_to=photo_upload_path, validators=[validate_photo_file])
    file_size = models.PositiveIntegerField(help_text="Bytes")
    mime_type = models.CharField(max_length=50)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_photos")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    capture_datetime = models.DateTimeField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    sequence = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sequence", "uploaded_at"]
        indexes = [models.Index(fields=["inspection", "category"])]

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.mime_type:
            self.mime_type = getattr(self.file.file, "content_type", "") or ""
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)


class VideoProcessingStatus(models.TextChoices):
    UPLOADED = "uploaded", "Uploaded"
    PROCESSING = "processing", "Processing"
    READY = "ready", "Ready"
    FAILED = "failed", "Failed"


class InspectionVideo(UUIDModel):
    """
    Mirrors the spec's InspectionVideo model exactly (section 43). The
    original file is stored via Django's normal FileField (local disk in
    dev, S3-compatible storage in prod — see config/settings/prod.py); only
    the metadata below lives in PostgreSQL, per the spec's explicit
    instruction not to store video bytes in the database.
    """
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="videos")
    category = models.ForeignKey("masters.VideoCategoryMaster", on_delete=models.PROTECT)
    title = models.CharField(max_length=150, blank=True)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=video_upload_path, validators=[validate_video_file])
    thumbnail = models.ImageField(upload_to=video_thumb_path, null=True, blank=True)
    mime_type = models.CharField(max_length=50)
    file_size = models.PositiveIntegerField(help_text="Bytes")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    capture_datetime = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="uploaded_videos")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    sequence = models.PositiveSmallIntegerField(default=0)
    processing_status = models.CharField(max_length=15, choices=VideoProcessingStatus.choices, default=VideoProcessingStatus.UPLOADED)
    processing_error = models.TextField(blank=True)
    active = models.BooleanField(default=True)  # replaced videos are deactivated, never hard-deleted
    replaces = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replaced_by")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sequence", "uploaded_at"]
        indexes = [models.Index(fields=["inspection", "category"]), models.Index(fields=["processing_status"])]

    def save(self, *args, **kwargs):
        if self.file and not self.file_size:
            self.file_size = self.file.size
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)
        if self.processing_status == VideoProcessingStatus.UPLOADED:
            from .tasks import run_video_processing
            run_video_processing(str(self.id))


class InspectionStatusHistory(UUIDModel):
    """Append-only trail powering the Video/Media Timeline in the UI and
    the audit requirements in the spec."""
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="status_history")
    event = models.CharField(max_length=150)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at"]
        verbose_name_plural = "Inspection status history"

    def __str__(self):
        return f"{self.inspection} — {self.event}"


def report_upload_path(instance, filename):
    return f"inspections/{instance.inspection.mis.mis_number}/reports/v{instance.version}.pdf"


class InspectionReport(UUIDModel):
    """
    One row per PDF generation. Never overwritten — regenerating creates a
    new version (spec: "Report version history" / ReportVersion), so a
    report that was already shared with an insurer stays retrievable even
    after later corrections.
    """
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name="reports")
    version = models.PositiveSmallIntegerField()
    pdf = models.FileField(upload_to=report_upload_path)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-version"]
        constraints = [models.UniqueConstraint(fields=["inspection", "version"], name="uniq_report_version")]

    def __str__(self):
        return f"{self.inspection.mis.mis_number} report v{self.version}"
