from django.apps import AppConfig


class MisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.mis"
    verbose_name = "MIS Management"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import MIS
        register_audit_logging(MIS, "mis")
