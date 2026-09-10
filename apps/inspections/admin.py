from django.contrib import admin

from . import models as m


class ItemResultInline(admin.TabularInline):
    model = m.InspectionItemResult
    extra = 0


class GlassResultInline(admin.TabularInline):
    model = m.InspectionGlassResult
    extra = 0


class PhotoInline(admin.TabularInline):
    model = m.InspectionPhoto
    extra = 0
    readonly_fields = ["uploaded_at", "file_size", "mime_type"]


class VideoInline(admin.TabularInline):
    model = m.InspectionVideo
    extra = 0
    readonly_fields = ["uploaded_at", "file_size", "mime_type", "processing_status"]


@admin.register(m.Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ["mis", "field_executive", "started_at", "submitted_at", "is_submitted"]
    search_fields = ["mis__mis_number"]
    autocomplete_fields = ["mis", "field_executive"]
    inlines = [ItemResultInline, GlassResultInline, PhotoInline, VideoInline]


@admin.register(m.InspectionVideo)
class InspectionVideoAdmin(admin.ModelAdmin):
    list_display = ["inspection", "category", "duration_seconds", "processing_status", "active", "uploaded_by", "uploaded_at"]
    list_filter = ["processing_status", "active", "category"]
    readonly_fields = ["file_size", "mime_type", "uploaded_at"]


@admin.register(m.InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    list_display = ["inspection", "category", "uploaded_by", "uploaded_at"]
    list_filter = ["category"]


@admin.register(m.InspectionDocument)
class InspectionDocumentAdmin(admin.ModelAdmin):
    list_display = ["inspection", "document_type", "verified", "verified_by", "verified_at"]
    list_filter = ["document_type", "verified"]


@admin.register(m.PreviousInsurance)
class PreviousInsuranceAdmin(admin.ModelAdmin):
    list_display = ["inspection", "previous_insurer", "policy_number", "had_previous_claim"]


@admin.register(m.InspectionStatusHistory)
class InspectionStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["inspection", "event", "changed_by", "changed_at"]
    readonly_fields = [f.name for f in m.InspectionStatusHistory._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(m.InspectionReport)
class InspectionReportAdmin(admin.ModelAdmin):
    list_display = ["inspection", "version", "generated_by", "generated_at"]
    readonly_fields = [f.name for f in m.InspectionReport._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
