from django.apps import AppConfig


class InsurersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.insurers"
    verbose_name = "Insurance Companies"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import InsuranceBranch, InsuranceCompany
        register_audit_logging(InsuranceCompany, "insurers")
        register_audit_logging(InsuranceBranch, "insurers")
