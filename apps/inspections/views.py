from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.audit.utils import log_action
from apps.masters.models import (
    AccessoryMaster, ConditionOption, FuelType, GlassItemMaster, InspectionItemMaster, VideoCategoryMaster,
)

from .models import (
    DocumentType, Inspection, InspectionAccessoryResult, InspectionDocument,
    InspectionGlassResult, InspectionItemResult, PhotoCategory,
)
from .services import add_photo, add_video, bulk_save_checklist, submit_inspection


def _get_inspection(pk):
    return get_object_or_404(
        Inspection.objects.select_related("mis", "mis__customer", "mis__vehicle", "mis__insurance_company", "field_executive"),
        pk=pk,
    )


@login_required
def workspace(request, pk):
    inspection = _get_inspection(pk)
    tab = request.GET.get("tab", "checklist")

    context = {
        "inspection": inspection,
        "mis": inspection.mis,
        "active_tab": tab,
        "tabs": [
            ("checklist", "Body Checklist"), ("glass", "Glass"), ("accessories", "Accessories"),
            ("vehicle", "Vehicle Verification"),
            ("photos", "Photos"), ("videos", "Videos"), ("documents", "Documents"),
            ("previous", "Previous Insurance"), ("timeline", "Timeline"),
        ],
        "condition_options": ConditionOption.objects.filter(active=True),
        "photo_categories": PhotoCategory.choices,
        "document_types": DocumentType.choices,
        "video_categories": VideoCategoryMaster.objects.filter(active=True),
    }

    if tab == "checklist":
        context["checklist_items"] = InspectionItemMaster.objects.filter(active=True)
        context["results_by_item"] = {r.item_id: r for r in inspection.item_results.select_related("condition")}
    elif tab == "glass":
        context["glass_items"] = GlassItemMaster.objects.filter(active=True)
        context["results_by_item"] = {r.item_id: r for r in inspection.glass_results.select_related("condition")}
    elif tab == "accessories":
        context["accessory_items"] = AccessoryMaster.objects.filter(active=True)
        context["results_by_item"] = {r.item_id: r for r in inspection.accessory_results.select_related("condition")}
    elif tab == "vehicle":
        context["fuel_types"] = FuelType.objects.filter(active=True)
    elif tab == "photos":
        context["photos"] = inspection.photos.all()
        context["required_photo_categories"] = [c for c in PhotoCategory.choices if c[0] != PhotoCategory.CHASSIS]
        context["additional_photo_categories"] = [c for c in PhotoCategory.choices if c[0] != PhotoCategory.CHASSIS]
    elif tab == "videos":
        context["videos"] = inspection.videos.filter(active=True)
    elif tab == "documents":
        existing = {d.document_type: d for d in inspection.documents.all()}
        context["documents"] = [(dt, existing.get(dt.value)) for dt in DocumentType]
    elif tab == "previous":
        context["previous_insurance"] = getattr(inspection, "previous_insurance", None)
    elif tab == "timeline":
        context["timeline"] = inspection.status_history.select_related("changed_by")

    return render(request, "inspections/workspace.html", context)


@login_required
@require_POST
def save_checklist(request, pk):
    inspection = _get_inspection(pk)
    rows = []
    for key, condition_id in request.POST.items():
        if key.startswith("item_"):
            rows.append({"item_id": key.removeprefix("item_"), "condition_id": condition_id,
                         "remarks": request.POST.get(f"remarks_{key.removeprefix('item_')}", "")})
    bulk_save_checklist(inspection=inspection, results=rows, result_model=InspectionItemResult, item_field="item")
    messages.success(request, "Body checklist saved.")
    return redirect(f"/inspections/{pk}/?tab=checklist")


@login_required
@require_POST
def save_glass(request, pk):
    inspection = _get_inspection(pk)
    rows = []
    for key, condition_id in request.POST.items():
        if key.startswith("item_"):
            rows.append({"item_id": key.removeprefix("item_"), "condition_id": condition_id, "remarks": ""})
    bulk_save_checklist(inspection=inspection, results=rows, result_model=InspectionGlassResult, item_field="item")
    messages.success(request, "Glass inspection saved.")
    return redirect(f"/inspections/{pk}/?tab=glass")


@login_required
@require_POST
def save_accessories(request, pk):
    inspection = _get_inspection(pk)
    for item in AccessoryMaster.objects.filter(active=True):
        present = request.POST.get(f"present_{item.id}") == "on"
        InspectionAccessoryResult.objects.update_or_create(
            inspection=inspection, item=item, defaults={"present": present}
        )
    messages.success(request, "Accessories saved.")
    return redirect(f"/inspections/{pk}/?tab=accessories")


@login_required
@require_POST
def save_vehicle_details(request, pk):
    inspection = _get_inspection(pk)
    inspection.chassis_number = request.POST.get("chassis_number", "").strip()
    inspection.engine_number = request.POST.get("engine_number", "").strip()
    inspection.vehicle_colour = request.POST.get("vehicle_colour", "").strip()
    fuel_type_id = request.POST.get("verified_fuel_type") or None
    inspection.verified_fuel_type_id = fuel_type_id
    odometer = request.POST.get("odometer_reading") or None
    inspection.odometer_reading = odometer
    year = request.POST.get("verified_manufacturing_year") or None
    inspection.verified_manufacturing_year = year
    inspection.save(update_fields=[
        "chassis_number", "engine_number", "vehicle_colour",
        "verified_fuel_type", "odometer_reading", "verified_manufacturing_year",
    ])
    messages.success(request, "Vehicle verification details saved.")
    return redirect(f"/inspections/{pk}/?tab=vehicle")


@login_required
@permission_required("inspections.upload_photo", raise_exception=True)
@require_POST
def upload_photo(request, pk):
    inspection = _get_inspection(pk)
    files = request.FILES.getlist("file")
    if not files:
        messages.error(request, "No file received.")
        return redirect(f"/inspections/{pk}/?tab=photos")

    slot = request.POST.get("slot", "required")
    slot_limits = {"required": 14, "chassis": 1, "additional": 4}
    max_files = slot_limits.get(slot, 14)
    if len(files) > max_files:
        messages.error(
            request,
            f"That upload allows at most {max_files} file{'s' if max_files != 1 else ''} "
            f"at a time — you selected {len(files)}. Nothing was uploaded; please reselect.",
        )
        return redirect(f"/inspections/{pk}/?tab=photos")

    category = PhotoCategory.CHASSIS if slot == "chassis" else request.POST.get("category", PhotoCategory.OTHER)
    latitude = request.POST.get("latitude") or None
    longitude = request.POST.get("longitude") or None

    uploaded, failed = 0, []
    for file in files:
        try:
            add_photo(
                inspection=inspection, file=file, category=category,
                uploaded_by=request.user, latitude=latitude, longitude=longitude,
            )
            uploaded += 1
        except Exception as exc:  # noqa: BLE001 — one bad file shouldn't sink the whole batch
            failed.append(f"{getattr(file, 'name', 'file')}: {exc}")

    if uploaded:
        messages.success(request, f"{uploaded} photo{'s' if uploaded != 1 else ''} uploaded.")
    for msg in failed:
        messages.error(request, f"Could not upload {msg}")

    return redirect(f"/inspections/{pk}/?tab=photos")


@login_required
@permission_required("inspections.upload_video", raise_exception=True)
@require_POST
def upload_video(request, pk):
    inspection = _get_inspection(pk)
    file = request.FILES.get("file")
    category_id = request.POST.get("category")
    if not file or not category_id:
        messages.error(request, "A file and category are required.")
        return redirect(f"/inspections/{pk}/?tab=videos")
    category = get_object_or_404(VideoCategoryMaster, pk=category_id)
    add_video(inspection=inspection, file=file, category=category, uploaded_by=request.user)
    messages.success(request, "Video uploaded — processing thumbnail in the background.")
    return redirect(f"/inspections/{pk}/?tab=videos")


@login_required
@require_POST
def toggle_document(request, pk, document_type):
    inspection = _get_inspection(pk)
    doc, _ = InspectionDocument.objects.get_or_create(inspection=inspection, document_type=document_type)
    doc.verified = not doc.verified
    doc.verified_by = request.user if doc.verified else None
    doc.verified_at = timezone.now() if doc.verified else None
    doc.save()
    return redirect(f"/inspections/{pk}/?tab=documents")


@login_required
@permission_required("inspections.submit_inspection", raise_exception=True)
@require_POST
def submit(request, pk):
    inspection = _get_inspection(pk)
    try:
        submit_inspection(inspection=inspection, user=request.user)
        messages.success(request, f"{inspection.mis.mis_number} submitted for QC review.")
        return redirect("mis:list")
    except PermissionDenied as exc:
        messages.error(request, str(exc))
        return redirect(f"/inspections/{pk}/")


@login_required
@require_POST
def generate_report_view(request, pk):
    from apps.mis.models import MISQCStage

    inspection = _get_inspection(pk)
    mis = inspection.mis

    if mis.qc_stage not in (MISQCStage.APPROVED, MISQCStage.REJECTED):
        messages.error(
            request,
            "Report cannot be generated until QC review is completed "
            "(current status: " + mis.get_qc_stage_display() + ").",
        )
        return redirect(f"/inspections/{pk}/?tab=documents")

    try:
        from .services import generate_report
        report = generate_report(inspection=inspection, generated_by=request.user, request=request)
        messages.success(request, f"Report v{report.version} generated.")
        return redirect("inspections:download_report", report_pk=report.pk)
    except ImportError:
        messages.error(
            request,
            "PDF generation isn't available — install WeasyPrint and its system "
            "libraries (see README) and try again.",
        )
        return redirect(f"/inspections/{pk}/")


@login_required
def download_report(request, report_pk):
    from django.http import FileResponse

    from .models import InspectionReport
    report = get_object_or_404(InspectionReport, pk=report_pk)
    log_action(action="download", module="inspections", obj=report)
    return FileResponse(report.pdf.open("rb"), as_attachment=False, filename=f"{report.inspection.mis.mis_number}-report-v{report.version}.pdf")


@login_required
def view_video(request, pk, video_id):
    """
    Permanent, login-required link — this is what the QR code / 'View Video'
    link in the PDF report actually points to. Unlike the API's signed
    30-minute link (apps/inspections/viewsets.secure_video_view, meant for a
    short-lived external QR scan), a report can be opened long after it was
    generated, so this link must keep working — but it still requires the
    viewer to be logged into ACIS and only shows videos from inspections
    they're allowed to see (same object-level check as the API).
    """
    from django.http import FileResponse, Http404

    from .models import InspectionVideo
    inspection = _get_inspection(pk)
    video = get_object_or_404(InspectionVideo, pk=video_id, inspection=inspection, active=True)

    user = request.user
    if not (user.is_superuser or user.role in ("super_admin", "admin", "manager", "qc_executive")
            or video.inspection.field_executive_id == user.id):
        raise Http404()

    log_action(action="download", module="inspections", obj=video, new_value={"via": "report_link"})
    return FileResponse(video.file.open("rb"), content_type=video.mime_type)