"""
Deliberately minimal for this phase of the build — the spec's billing
requirements (invoicing rules, payment gateway integration, GST handling)
depend on business decisions not specified yet. These two models exist so
MIS.payment_stage has something concrete behind it and the schema doesn't
need a breaking migration later; flesh out fields as those decisions land.
"""
from django.conf import settings
from django.db import models

from apps.audit.mixins import TimeStampedModel, UUIDModel


class Payment(UUIDModel, TimeStampedModel):
    mis = models.ForeignKey("mis.MIS", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mode = models.ForeignKey("masters.PaymentMode", on_delete=models.PROTECT)
    reference_number = models.CharField(max_length=60, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        permissions = [("view_billing_reports", "Can view billing summary reports")]


class Invoice(UUIDModel, TimeStampedModel):
    mis = models.ForeignKey("mis.MIS", on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=30, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_at = models.DateField(null=True, blank=True)
    pdf = models.FileField(upload_to="invoices/", null=True, blank=True)
