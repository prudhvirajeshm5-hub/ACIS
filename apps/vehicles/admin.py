from django.contrib import admin

from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["registration_number", "make", "model", "manufacturing_year", "owner"]
    search_fields = ["registration_number", "chassis_number", "engine_number", "owner__name", "make", "model"]
    list_filter = ["vehicle_type", "fuel_type"]
    autocomplete_fields = ["vehicle_type", "fuel_type", "owner"]