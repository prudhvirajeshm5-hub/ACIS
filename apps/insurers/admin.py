from django.contrib import admin

from .models import InsuranceBranch, InsuranceCompany


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "contact_email", "active"]
    search_fields = ["name", "code"]


@admin.register(InsuranceBranch)
class InsuranceBranchAdmin(admin.ModelAdmin):
    list_display = ["name", "district", "active"]
    list_filter = ["companies", "active"]
    search_fields = ["name"]
    autocomplete_fields = ["district"]
    filter_horizontal = ["companies"]
