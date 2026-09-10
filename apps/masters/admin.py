from django.contrib import admin

from . import models as m


@admin.register(m.State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "active"]
    search_fields = ["name"]
    list_filter = ["active"]


@admin.register(m.District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ["name", "state", "active"]
    list_filter = ["state", "active"]
    search_fields = ["name"]
    autocomplete_fields = ["state"]


@admin.register(m.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ["name", "district", "active"]
    list_filter = ["district__state", "active"]
    search_fields = ["name"]
    autocomplete_fields = ["district"]


@admin.register(m.VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "active"]
    search_fields = ["name"]


@admin.register(m.VehicleMake)
class VehicleMakeAdmin(admin.ModelAdmin):
    list_display = ["name", "vehicle_type", "active"]
    list_filter = ["vehicle_type"]
    search_fields = ["name"]
    autocomplete_fields = ["vehicle_type"]


@admin.register(m.VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ["name", "make", "active"]
    list_filter = ["make__vehicle_type"]
    search_fields = ["name"]
    autocomplete_fields = ["make"]


@admin.register(m.FuelType)
class FuelTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "active"]
    search_fields = ["name"]


@admin.register(m.InspectionStatus)
class InspectionStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "sequence", "active"]


@admin.register(m.QCStatus)
class QCStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "sequence", "active"]


@admin.register(m.TicketStatus)
class TicketStatusAdmin(admin.ModelAdmin):
    list_display = ["name", "active"]


@admin.register(m.PaymentMode)
class PaymentModeAdmin(admin.ModelAdmin):
    list_display = ["name", "active"]


@admin.register(m.InspectionItemMaster)
class InspectionItemMasterAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "active"]
    ordering = ["display_order"]


@admin.register(m.GlassItemMaster)
class GlassItemMasterAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "active"]


@admin.register(m.AccessoryMaster)
class AccessoryMasterAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "active"]


@admin.register(m.ConditionOption)
class ConditionOptionAdmin(admin.ModelAdmin):
    list_display = ["name", "is_positive", "active"]


@admin.register(m.VideoCategoryMaster)
class VideoCategoryMasterAdmin(admin.ModelAdmin):
    list_display = ["name", "display_order", "active"]
