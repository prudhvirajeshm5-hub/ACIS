from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.masters.models import (
    AccessoryMaster, ConditionOption, GlassItemMaster, InspectionItemMaster,
    PhotoCategoryMaster, VideoCategoryMaster,
)

from .models import (
    DocumentType, Inspection, InspectionAccessoryResult, InspectionDocument,
    InspectionGlassResult, InspectionItemResult,
)
from .services import add_video, bulk_save_checklist, bulk_upload_photos, submit_inspection


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
            ("photos", "Photos"), ("videos", "Videos"), ("documents", "Documents"),
            ("previous", "Previous Insurance"), ("timeline", "Timeline"),
        ],
        "condition_options": ConditionOption.objects.filter(active=True),
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
    elif tab == "photos":
        categories = list(PhotoCategoryMaster.objects.filter(active=True))
        existing_by_category = {p.category_id: p for p in inspection.photos.select_related("category")}
        mandatory = [c for c in categories if c.is_mandatory]
        additional_category = next((c for c in categories if not c.is_mandatory), None)
        context["mandatory_photo_slots"] = [(c, existing_by_category.get(c.id)) for c in mandatory]
        context["additional_category"] = additional_category
        additional_photos = (
            inspection.photos.filter(category=additional_category) if additional_category else []
        )
        context["additional_photos"] = additional_photos
        context["additional_remaining"] = (
            max(additional_category.max_count - len(additional_photos), 0) if additional_category else 0
        )
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
@permission_required("inspections.upload_photo", raise_exception=True)
@require_POST
def upload_bulk_photos(request, pk):
    """One submit handles the whole photo tab: any of the 14 mandatory
    slots (each an input named `photo_<category_id>`, at most one file)
    plus up to `max_count` files in the `additional_photos` multi-file
    input for the non-mandatory 'Additional Photos' slot."""
    inspection = _get_inspection(pk)
    categories = {str(c.id): c for c in PhotoCategoryMaster.objects.filter(active=True)}

    items = []
    for key, file in request.FILES.items():
        if not key.startswith("photo_"):
            continue
        category = categories.get(key.removeprefix("photo_"))
        if category and category.is_mandatory:
            items.append((category, file))

    additional_category = next((c for c in categories.values() if not c.is_mandatory), None)
    if additional_category:
        additional_files = request.FILES.getlist("additional_photos")
        already = inspection.photos.filter(category=additional_category).count()
        allowed = max(additional_category.max_count - already, 0)
        if len(additional_files) > allowed:
            messages.error(
                request,
                f"Only {allowed} more \"{additional_category.name}\" photo(s) can be added "
                f"(max {additional_category.max_count}).",
            )
            return redirect(f"/inspections/{pk}/?tab=photos")
        items += [(additional_category, f) for f in additional_files]

    if not items:
        messages.error(request, "No files received.")
        return redirect(f"/inspections/{pk}/?tab=photos")

    bulk_upload_photos(inspection=inspection, items=items, uploaded_by=request.user)
    messages.success(request, f"{len(items)} photo(s) uploaded.")
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
