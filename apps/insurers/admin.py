from django.contrib import admin

from .models import InsuranceBranch, InsuranceCompany


class BranchInline(admin.TabularInline):
    model = InsuranceBranch
    extra = 0


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "contact_email", "active"]
    search_fields = ["name", "code"]
    inlines = [BranchInline]


@admin.register(InsuranceBranch)
class InsuranceBranchAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "district", "active"]
    list_filter = ["company", "active"]
    search_fields = ["name"]
    autocomplete_fields = ["company", "district"]
