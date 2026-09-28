from django import forms
from django.contrib.auth import get_user_model

from .models import IncentiveTarget


class TargetForm(forms.ModelForm):
    class Meta:
        model = IncentiveTarget
        fields = ["employee", "metric", "target_count", "start_date", "end_date", "incentive_amount"]
        labels = {"target_count": "Target (number of cases)", "incentive_amount": "Incentive amount if achieved (optional)"}
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        users = get_user_model().objects.filter(is_active=True, is_superuser=False).order_by("first_name", "username")
        self.fields["employee"].queryset = users
        self.fields["employee"].label_from_instance = lambda u: f"{u.get_full_name() or u.username} ({u.role_label})"
