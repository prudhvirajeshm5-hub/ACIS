from django import forms

from .models import QCDecision


class QCDecisionForm(forms.Form):
    decision = forms.ChoiceField(choices=QCDecision.choices, widget=forms.RadioSelect)
    remarks = forms.CharField(widget=forms.Textarea(attrs={"class": "input", "rows": 4}), required=False)
