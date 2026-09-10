from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.audit.utils import log_action
from apps.masters.models import ConditionOption
from apps.mis.models import MISInspectionStage, MISQCStage

from .models import (
    Inspection,
    InspectionAccessoryResult,
    InspectionGlassResult,
    InspectionItemResult,
    InspectionPhoto,
    InspectionStatusHistory,
    InspectionVideo,
)


def _log_event(inspection, event, user):
    InspectionStatusHistory.objects.create(inspection=inspection, event=event, changed_by=user)


@transaction.atomic
def accept_inspection(*, inspection, user):
    inspection.field_executive = user
    inspection.accepted_at = timezone.now()
    inspection.save(update_fields=["field_executive", "accepted_at", "updated_at"])
    _log_event(inspection, "Field executive accepted assignment", user)


@transaction.atomic
def start_inspection(*, inspection, user, latitude=None, longitude=None):
    inspection.started_at = timezone.now()
    if latitude is not None and longitude is not None:
        inspection.latitude = latitude
        inspection.longitude = longitude
        inspection.location_captured_at = timezone.now()
    inspection.save(update_fields=["started_at", "latitude", "longitude", "location_captured_at", "updated_at"])
    inspection.mis.inspection_stage = MISInspectionStage.IN_PROGRESS
    inspection.mis.save(update_fields=["inspection_stage", "updated_at"])
    _log_event(inspection, "Inspection started at customer location", user)


def bulk_save_checklist(*, inspection, results, result_model, item_field):
    """
    `results` is a list of dicts: [{"item_id": ..., "condition_id": ..., "remarks": ...}, ...]
    Shared by the body-checklist, glass and (present/absent) accessory tabs
    so the "don't duplicate business logic" rule from the spec holds.
    """
    for row in results:
        result_model.objects.update_or_create(
            inspection=inspection,
            **{f"{item_field}_id": row[f"{item_field}_id"]},
            defaults={k: v for k, v in row.items() if k != f"{item_field}_id"},
        )


@transaction.atomic
def submit_inspection(*, inspection, user):
    """Enforces the spec's "prevent accidental duplicate submissions" rule:
    submitting an already-submitted inspection (and not currently in a
    QC-requested correction state) raises rather than silently no-op'ing,
    so the UI can show a clear error instead of creating confusing
    duplicate history entries."""
    mis = inspection.mis
    if inspection.is_submitted and mis.qc_stage not in (MISQCStage.CORRECTION,):
        raise PermissionDenied("This inspection has already been submitted.")

    inspection.is_submitted = True
    inspection.submitted_at = timezone.now()
    inspection.save(update_fields=["is_submitted", "submitted_at", "updated_at"])

    mis.inspection_stage = MISInspectionStage.COMPLETED
    mis.qc_stage = MISQCStage.PENDING
    mis.save(update_fields=["inspection_stage", "qc_stage", "updated_at"])

    _log_event(inspection, "Inspection submitted for QC review", user)
    log_action(action="update", module="inspections", obj=inspection, new_value={"submitted": True})


@transaction.atomic
def add_photo(*, inspection, file, category, uploaded_by, **meta):
    photo = InspectionPhoto.objects.create(
        inspection=inspection, file=file, category=category, uploaded_by=uploaded_by,
        original_filename=getattr(file, "name", ""), file_size=file.size,
        mime_type=getattr(file, "content_type", ""), **meta,
    )
    _log_event(inspection, f"{category.name} photo uploaded", uploaded_by)
    log_action(action="upload", module="inspections", obj=photo)
    return photo


@transaction.atomic
def bulk_upload_photos(*, inspection, items, uploaded_by):
    """`items` is a list of (category, file) tuples, mixing any number of
    mandatory slots (Front View, Engine Bay, ...) with any number of files
    for a non-mandatory slot (Additional Photos). Mandatory slots always
    hold a single photo — re-uploading one deletes the old file and
    replaces it. Non-mandatory slots simply add another photo, subject to
    the cap the view has already checked against `category.max_count`."""
    created = []
    for category, file in items:
        if category.is_mandatory:
            InspectionPhoto.objects.filter(inspection=inspection, category=category).delete()
        created.append(add_photo(inspection=inspection, file=file, category=category, uploaded_by=uploaded_by))
    return created


@transaction.atomic
def add_video(*, inspection, file, category, uploaded_by, **meta):
    video = InspectionVideo.objects.create(
        inspection=inspection, file=file, category=category, uploaded_by=uploaded_by,
        original_filename=getattr(file, "name", ""), file_size=file.size,
        mime_type=getattr(file, "content_type", ""), **meta,
    )
    _log_event(inspection, f"{video.category} video uploaded", uploaded_by)
    log_action(action="upload", module="inspections", obj=video)
    return video


@transaction.atomic
def replace_video(*, old_video, new_file, uploaded_by):
    """Never silently overwrites — deactivates the old evidence file and
    links the new one to it, per the spec's video-retention requirement."""
    old_video.active = False
    old_video.save(update_fields=["active", "updated_at"])
    return add_video(
        inspection=old_video.inspection, file=new_file, category=old_video.category,
        uploaded_by=uploaded_by, replaces=old_video,
    )
