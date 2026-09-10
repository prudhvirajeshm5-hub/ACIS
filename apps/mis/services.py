"""
Business logic kept out of views/templates, per the spec's code-quality
requirements. Views call these; the DRF viewsets call these too, so the
web UI and the future Flutter app share identical rules.
"""
from django.db import transaction
from django.utils import timezone

from apps.audit.utils import log_action
from apps.inspections.models import Inspection, InspectionStatusHistory
from apps.masters.models import InspectionStatus

from .models import MIS, MISInspectionStage


@transaction.atomic
def create_mis(*, data, created_by):
    """
    Wrapped in a transaction and locks the MIS table's last row for the
    current year so mis_number generation (see MIS.save) is race-safe under
    concurrent creates. For very high write volume, replace with a
    PostgreSQL sequence/identity column instead of the human-readable
    MIS-YYYY-NNNN scheme.
    """
    MIS.objects.select_for_update().filter(
        mis_number__startswith=f"MIS-{timezone.now().year}-"
    ).order_by("-mis_number").first()

    mis = MIS.objects.create(created_by=created_by, **data)
    log_action(action="create", module="mis", obj=mis)
    return mis


@transaction.atomic
def assign_field_executive(*, mis, field_executive, scheduled_date, assigned_by):
    mis.field_executive = field_executive
    mis.scheduled_date = scheduled_date
    mis.assigned_at = timezone.now()
    mis.inspection_stage = MISInspectionStage.ASSIGNED
    mis.save(update_fields=["field_executive", "scheduled_date", "assigned_at", "inspection_stage", "updated_at", "updated_by"])

    Inspection.objects.get_or_create(mis=mis, defaults={"field_executive": field_executive})

    log_action(action="assign", module="mis", obj=mis, new_value={"field_executive": str(field_executive)})
    return mis
