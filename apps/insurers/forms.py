from django import forms

from apps.masters.models import District

from .models import InsuranceBranch, InsuranceCompany


def _w(attrs=None):
    base = {"class": "input"}
    if attrs:
        base.update(attrs)
    return base


class InsuranceCompanyForm(forms.ModelForm):
    class Meta:
        model = InsuranceCompany
        fields = ["name", "code", "gstin", "contact_email", "contact_phone"]
        widgets = {f: forms.TextInput(attrs=_w()) for f in ["name", "code", "gstin", "contact_email", "contact_phone"]}


class InsuranceBranchForm(forms.ModelForm):
    class Meta:
        model = InsuranceBranch
        fields = ["companies", "name", "code", "district", "address"]
        widgets = {
            "companies": forms.CheckboxSelectMultiple(),
            "name": forms.TextInput(attrs=_w()),
            "code": forms.TextInput(attrs=_w()),
            "district": forms.Select(attrs=_w()),
            "address": forms.Textarea(attrs=_w({"rows": 2})),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["district"].queryset = District.objects.filter(active=True)
        self.fields["companies"].queryset = InsuranceCompany.objects.filter(active=True)
