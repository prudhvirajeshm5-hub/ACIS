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
    _log_event(inspection, f"{photo.get_category_display()} photo uploaded", uploaded_by)
    log_action(action="upload", module="inspections", obj=photo)
    return photo


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


def generate_report(*, inspection, generated_by, request=None):
    """
    Renders the inspection to PDF (WeasyPrint) and saves it as a new,
    immutable InspectionReport version. Called from the "Generate Report"
    button on the QC review / MIS detail screens.

    Photos are embedded via file:// paths (WeasyPrint resolves these
    directly from disk — no running server needed to render the PDF).
    Each video gets a QR code + clickable link pointing at a permanent,
    login-required view (apps.inspections.views.view_video) rather than
    embedding the video itself, per the spec's "don't embed full video
    files in the PDF" requirement.
    """
    import base64
    import io

    import qrcode
    from django.core.files.base import ContentFile
    from django.template.loader import render_to_string
    from django.urls import reverse
    from weasyprint import HTML

    from .models import InspectionReport, PhotoCategory

    last = inspection.reports.first()  # ordering = -version
    next_version = (last.version + 1) if last else 1

    def _file_uri(field_file):
        try:
            return f"file://{field_file.path}"
        except (ValueError, FileNotFoundError):
            return ""

    all_photos = list(inspection.photos.all())
    photo_rows = [{"photo": p, "uri": _file_uri(p.file)} for p in all_photos]
    chassis_photo = next((p for p in all_photos if p.category == PhotoCategory.CHASSIS), None)
    chassis_photo_uri = _file_uri(chassis_photo.file) if chassis_photo else ""

    video_rows = []
    for v in inspection.videos.filter(active=True):
        view_path = reverse("inspections:view_video", args=[inspection.pk, v.pk])
        view_url = request.build_absolute_uri(view_path) if request else view_path
        buf = io.BytesIO()
        qrcode.make(view_url).save(buf, format="PNG")
        video_rows.append({
            "video": v, "view_url": view_url,
            "qr_base64": base64.b64encode(buf.getvalue()).decode(),
        })

    html_string = render_to_string("inspections/report_pdf.html", {
        "inspection": inspection,
        "mis": inspection.mis,
        "item_results": inspection.item_results.select_related("item", "condition"),
        "glass_results": inspection.glass_results.select_related("item", "condition"),
        "accessory_results": inspection.accessory_results.select_related("item", "condition"),
        "photo_rows": photo_rows,
        "chassis_photo_uri": chassis_photo_uri,
        "video_rows": video_rows,
        "documents": inspection.documents.all(),
        "previous_insurance": getattr(inspection, "previous_insurance", None),
        "latest_qc": inspection.qc_reviews.select_related("qc_executive").first(),
        "version": next_version,
        "generated_by": generated_by,
    })

    pdf_bytes = HTML(string=html_string).write_pdf()

    report = InspectionReport.objects.create(
        inspection=inspection, version=next_version, generated_by=generated_by,
    )
    report.pdf.save(f"v{next_version}.pdf", ContentFile(pdf_bytes), save=True)

    log_action(action="generate_report", module="inspections", obj=report)
    _log_event(inspection, f"Inspection report v{next_version} generated", generated_by)
    return report