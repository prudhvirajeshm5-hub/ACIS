from django.contrib import admin

from .models import QCReview


@admin.register(QCReview)
class QCReviewAdmin(admin.ModelAdmin):
    list_display = ["inspection", "decision", "qc_executive", "reviewed_at"]
    list_filter = ["decision"]
    search_fields = ["inspection__mis__mis_number"]
    readonly_fields = [f.name for f in QCReview._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
