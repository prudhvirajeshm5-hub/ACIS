from django.apps import AppConfig


class VehiclesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.vehicles"
    verbose_name = "Vehicles"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from .models import Vehicle
        register_audit_logging(Vehicle, "vehicles")
