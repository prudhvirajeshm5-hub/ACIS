from django.apps import AppConfig


class MastersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.masters"
    verbose_name = "Master Data"

    def ready(self):
        from apps.audit.signals import register_audit_logging
        from . import models as m
        for model in [
            m.State, m.District, m.City, m.VehicleType, m.VehicleMake, m.VehicleModel,
            m.FuelType, m.InspectionStatus, m.QCStatus, m.TicketStatus, m.PaymentMode,
            m.InspectionItemMaster, m.GlassItemMaster, m.AccessoryMaster,
            m.ConditionOption, m.VideoCategoryMaster,
        ]:
            register_audit_logging(model, "masters")
