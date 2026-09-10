from django.apps import AppConfig


class QcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.qc"
    verbose_name = "Quality Control"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import QCReview
        register_audit_logging(QCReview, "qc")
