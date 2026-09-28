from django.contrib import admin

from .models import IncentiveTarget


@admin.register(IncentiveTarget)
class IncentiveTargetAdmin(admin.ModelAdmin):
    list_display = ["employee", "metric", "target_count", "start_date", "end_date", "incentive_amount"]
    list_filter = ["metric"]
    search_fields = ["employee__username", "employee__first_name", "employee__last_name"]
