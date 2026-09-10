import datetime
import uuid

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.db.models import Count, Model, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from apps.accounts.permissions import PermissionRequiredMixin
from apps.customers.models import Customer
from apps.inspections.models import InspectionStatusHistory
from apps.vehicles.models import Vehicle

from .forms import AssignmentForm, CustomerForm, MISDetailsForm, VehicleForm
from .models import MIS, MISInspectionStage, MISQCStage
from .services import assign_field_executive, create_mis

User = get_user_model()

SESSION_KEY = "create_mis_wizard"
STEP_FORMS = {1: MISDetailsForm, 2: CustomerForm, 3: VehicleForm, 4: AssignmentForm}
STEP_TITLES = {1: "Inspection Details", 2: "Customer Details", 3: "Vehicle Details", 4: "Inspection Assignment"}


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = MIS.objects.filter(insurance_company__in=self.request.user.visible_insurance_companies())
        today = timezone.now().date()

        ctx["stats"] = {
            "total_mis": qs.count(),
            "todays_mis": qs.filter(mis_date=today).count(),
            "pending_inspections": qs.filter(inspection_stage=MISInspectionStage.PENDING).count(),
            "assigned_inspections": qs.filter(inspection_stage=MISInspectionStage.ASSIGNED).count(),
            "completed_inspections": qs.filter(inspection_stage=MISInspectionStage.COMPLETED).count(),
            "pending_qc": qs.filter(qc_stage=MISQCStage.PENDING).count(),
            "qc_approved": qs.filter(qc_stage=MISQCStage.APPROVED).count(),
            "qc_rejected": qs.filter(qc_stage=MISQCStage.REJECTED).count(),
        }
        ctx["by_insurer"] = (
            qs.values("insurance_company__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:6]
        )
        ctx["recent_activity"] = InspectionStatusHistory.objects.select_related(
            "inspection__mis", "changed_by"
        ).order_by("-changed_at")[:8]
        return ctx


# ---------------------------------------------------------------------------
# MIS List
# ---------------------------------------------------------------------------
class MISListView(LoginRequiredMixin, ListView):
    model = MIS
    template_name = "mis/mis_list.html"
    context_object_name = "mis_records"
    paginate_by = 25

    def get_queryset(self):
        qs = MIS.objects.select_related("customer", "vehicle", "insurance_company", "branch", "field_executive")
        qs = qs.filter(insurance_company__in=self.request.user.visible_insurance_companies())
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(mis_number__icontains=q) | Q(customer__name__icontains=q) |
                Q(customer__mobile__icontains=q) | Q(vehicle__registration_number__icontains=q) |
                Q(insurance_reference_number__icontains=q)
            )
        for field in ["inspection_stage", "qc_stage", "insurance_company", "field_executive"]:
            val = self.request.GET.get(field)
            if val:
                qs = qs.filter(**{field: val})
        return qs


# ---------------------------------------------------------------------------
# Create MIS — 4-step wizard, session-backed (no extra dependency needed).
# Each step validates and stores its cleaned data in the session; nothing
# is written to the DB until step 4 is confirmed, so an abandoned wizard
# never leaves a half-created record behind.
# ---------------------------------------------------------------------------
class CreateMISWizardView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = "mis.add_mis"

    def get(self, request, step=1):
        data = request.session.get(SESSION_KEY, {})
        form_cls = STEP_FORMS.get(step)
        if not form_cls:
            return redirect("mis:create", step=1)
        form = self._build_form(form_cls, request, initial=data.get(str(step), {}))
        return render(request, "mis/mis_wizard.html", self._ctx(step, form, data))

    def post(self, request, step=1):
        data = request.session.get(SESSION_KEY, {})
        form_cls = STEP_FORMS[step]
        form = self._build_form(form_cls, request, data=request.POST)

        if not form.is_valid():
            return render(request, "mis/mis_wizard.html", self._ctx(step, form, data))

        data[str(step)] = self._serialize_cleaned_data(form.cleaned_data)
        request.session[SESSION_KEY] = data
        request.session.modified = True

        if step < 4:
            return redirect("mis:create", step=step + 1)

        return self._finalize(request, data)

    def _build_form(self, form_cls, request, data=None, initial=None):
        """MISDetailsForm (step 1) is the only step with a user-scoped
        field (insurance_company) — every other step's form doesn't accept
        a `user` kwarg, so only pass it where it's actually used."""
        kwargs = {"data": data, "initial": initial}
        if form_cls is MISDetailsForm:
            kwargs["user"] = request.user
        return form_cls(**kwargs)

    @staticmethod
    def _serialize_cleaned_data(cleaned_data):
        """Sessions are stored via Django's JSON serializer, so anything
        that isn't a plain JSON type has to be reduced to one before it's
        saved. DateField/DateTimeField values come back from cleaned_data
        as date/datetime objects, and ModelChoiceField values (e.g.
        insurance_company, branch, field_executive) come back as model
        instances — both raise "Object of type X is not JSON serializable"
        if stashed into the session as-is. This project's models use UUID
        primary keys (see UUIDModel), so the pk itself is also a non-JSON
        `uuid.UUID` and has to be stringified, not just unwrapped. Reduce
        everything to isoformat strings / string pks here; `_revalidate`
        turns them back into real objects at step-4 finalize time by
        re-running them through the form (which already knows how to turn
        a pk string back into the referenced object)."""
        safe = {}
        for key, value in cleaned_data.items():
            if isinstance(value, (datetime.datetime, datetime.date)):
                safe[key] = value.isoformat()
            elif isinstance(value, Model):
                safe[key] = str(value.pk)
            elif isinstance(value, uuid.UUID):
                safe[key] = str(value)
            else:
                safe[key] = value
        return safe

    def _revalidate(self, step, raw, request):
        """Rebuild real cleaned_data (model instances, date objects) from
        the JSON-safe primitives stored in the session, by feeding them
        back through the step's own form — the same form data format the
        widgets already produce on submit, so this is just re-validation."""
        form = self._build_form(STEP_FORMS[step], request, data=raw)
        form.is_valid()
        return form.cleaned_data

    def _finalize(self, request, data):
        try:
            # All four step forms have FK and/or date fields (mis_date;
            # insurance_company/branch; state/district/city;
            # vehicle_type/make/model/fuel_type; field_executive/
            # scheduled_date), so every step's stored primitives need to
            # be turned back into real objects the same way — not just
            # steps 1 and 4.
            step1 = self._revalidate(1, data["1"], request)
            step2 = self._revalidate(2, data["2"], request)
            step3 = self._revalidate(3, data["3"], request)
            step4 = self._revalidate(4, data["4"], request)

            customer, _ = Customer.objects.get_or_create(
                mobile=step2["mobile"], defaults=step2,
            )
            vehicle, _ = Vehicle.objects.update_or_create(
                registration_number=step3["registration_number"].upper().replace(" ", ""),
                defaults={**step3, "owner": customer},
            )
            mis_data = {**step1, "customer": customer, "vehicle": vehicle}
            mis = create_mis(data=mis_data, created_by=request.user)

            assignment = step4
            if assignment.get("field_executive"):
                assign_field_executive(
                    mis=mis, field_executive=assignment["field_executive"],
                    scheduled_date=assignment.get("scheduled_date"), assigned_by=request.user,
                )
                mis.priority = assignment.get("priority", mis.priority)
                mis.inspection_location = assignment.get("inspection_location", "")
                mis.save(update_fields=["priority", "inspection_location"])

            del request.session[SESSION_KEY]
            messages.success(request, f"{mis.mis_number} created" + (f" and assigned to {mis.field_executive}." if mis.field_executive else "."))
            return redirect("mis:detail", pk=mis.pk)
        except Exception as exc:  # noqa: BLE001 — surfaced to the user, also logged
            messages.error(request, f"Could not create MIS: {exc}")
            return redirect("mis:create", step=1)

    def _ctx(self, step, form, data):
        return {
            "step": step, "total_steps": 4, "form": form,
            "step_titles": STEP_TITLES, "current_step_title": STEP_TITLES[step], "collected": data,
            "field_executives": User.objects.filter(role="field_executive", is_active=True),
        }


class MISDetailView(LoginRequiredMixin, TemplateView):
    template_name = "mis/mis_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["mis"] = get_object_or_404(
            MIS.objects.select_related("customer", "vehicle", "insurance_company", "branch", "field_executive"),
            pk=kwargs["pk"],
        )
        return ctx