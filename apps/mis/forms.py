from django import forms

from apps.customers.models import Customer
from apps.insurers.models import InsuranceBranch, InsuranceCompany
from apps.vehicles.models import Vehicle

from .models import MIS


def _w(attrs=None):
    base = {"class": "input"}
    if attrs:
        base.update(attrs)
    return base


class MISDetailsForm(forms.ModelForm):
    """Section 1 — Inspection Details."""
    class Meta:
        model = MIS
        fields = ["mis_date", "insurance_company", "branch", "insurance_reference_number",
                  "inspection_type", "intimator", "intimator_email", "remarks"]
        widgets = {
            "mis_date": forms.DateInput(attrs=_w({"type": "date"})),
            "insurance_company": forms.Select(attrs=_w()),
            "branch": forms.Select(attrs=_w()),
            "insurance_reference_number": forms.TextInput(attrs=_w()),
            "inspection_type": forms.TextInput(attrs=_w()),
            "intimator": forms.TextInput(attrs=_w()),
            "intimator_email": forms.EmailInput(attrs=_w()),
            "remarks": forms.Textarea(attrs=_w({"rows": 2})),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["branch"].queryset = InsuranceBranch.objects.filter(active=True)
        if user is not None:
            self.fields["insurance_company"].queryset = user.visible_insurance_companies()
        else:
            self.fields["insurance_company"].queryset = InsuranceCompany.objects.filter(active=True)


class CustomerForm(forms.ModelForm):
    """Section 2 — Customer Details. Looked up-or-created by mobile number."""
    class Meta:
        model = Customer
        fields = ["name", "mobile", "email", "address", "state", "district", "city"]
        widgets = {f: forms.TextInput(attrs=_w()) for f in ["name", "mobile", "email"]}
        widgets["address"] = forms.Textarea(attrs=_w({"rows": 2}))


class VehicleForm(forms.ModelForm):
    """Section 3 — Vehicle Details."""
    class Meta:
        model = Vehicle
        fields = ["registration_number", "vehicle_type", "make", "model", "fuel_type",
                  "manufacturing_year"]
        widgets = {
            "registration_number": forms.TextInput(attrs=_w()),
            "vehicle_type": forms.Select(attrs=_w()),
            "make": forms.TextInput(attrs=_w()),
            "model": forms.TextInput(attrs=_w()),
            "fuel_type": forms.Select(attrs=_w()),
            "manufacturing_year": forms.TextInput(attrs=_w()),
        }



class AssignmentForm(forms.ModelForm):
    """Section 4 — Inspection Assignment."""
    class Meta:
        model = MIS
        fields = ["field_executive", "priority", "scheduled_date", "inspection_location"]
        widgets = {
            "field_executive": forms.Select(attrs=_w()),
            "priority": forms.Select(attrs=_w()),
            "scheduled_date": forms.DateInput(attrs=_w({"type": "date"})),
            "inspection_location": forms.TextInput(attrs=_w()),
        }
