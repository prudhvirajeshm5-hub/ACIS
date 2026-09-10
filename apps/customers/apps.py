from django.apps import AppConfig


class CustomersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.customers"
    verbose_name = "Customers"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import Customer
        register_audit_logging(Customer, "customers")
