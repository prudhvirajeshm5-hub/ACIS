from django.contrib import admin

from .models import MIS


@admin.register(MIS)
class MISAdmin(admin.ModelAdmin):
    list_display = ["mis_number", "mis_date", "customer", "vehicle", "insurance_company",
                     "field_executive", "inspection_stage", "qc_stage", "payment_stage"]
    list_filter = ["inspection_stage", "qc_stage", "payment_stage", "insurance_company", "priority"]
    search_fields = ["mis_number", "customer__name", "customer__mobile", "vehicle__registration_number", "insurance_reference_number"]
    autocomplete_fields = ["insurance_company", "branch", "customer", "vehicle", "field_executive"]
    readonly_fields = ["mis_number", "created_at", "updated_at", "created_by", "updated_by"]
    date_hierarchy = "mis_date"
