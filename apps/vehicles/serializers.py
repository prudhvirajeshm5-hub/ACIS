from rest_framework import serializers

from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "registration_number", "vehicle_type", "make", "model", "fuel_type",
            "manufacturing_year", "engine_number", "chassis_number", "owner", "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_registration_number(self, value):
        return value.upper().replace(" ", "")
