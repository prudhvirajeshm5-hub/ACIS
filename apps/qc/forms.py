from django import forms
from django.utils import timezone

from .models import QCDecision


class QCDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=QCDecision.choices, widget=forms.RadioSelect)
    inspection_date = forms.DateField(
        label="Inspection Date",
        widget=forms.DateInput(attrs={"class": "input", "type": "date"}, format="%Y-%m-%d"),
    )
    inspection_time = forms.TimeField(
        label="Inspection Time",
        widget=forms.TimeInput(attrs={"class": "input", "type": "time"}, format="%H:%M"),
    )
    remarks = forms.CharField(widget=forms.Textarea(attrs={"class": "input", "rows": 4}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.localtime()
        self.fields["inspection_date"].initial = now.date()
        self.fields["inspection_time"].initial = now.time().replace(second=0, microsecond=0)
