from django.apps import AppConfig


class InspectionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.inspections"
    verbose_name = "Inspections"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import Inspection, InspectionPhoto, InspectionVideo
        register_audit_logging(Inspection, "inspections")
        register_audit_logging(InspectionPhoto, "inspections")
        register_audit_logging(InspectionVideo, "inspections")
