from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import MIS

User = get_user_model()


class MISSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vehicle_number = serializers.CharField(source="vehicle.registration_number", read_only=True)
    field_executive_name = serializers.CharField(source="field_executive.get_full_name", read_only=True)

    class Meta:
        model = MIS
        fields = [
            "id", "mis_number", "mis_date", "insurance_company", "branch",
            "insurance_reference_number", "lead_reference_id", "inspection_type",
            "customer", "customer_name", "vehicle", "vehicle_number",
            "field_executive", "field_executive_name", "priority",
            "scheduled_date", "inspection_location",
            "inspection_stage", "qc_stage", "payment_stage",
            "created_at",
        ]
        read_only_fields = ["id", "mis_number", "created_at", "inspection_stage", "qc_stage"]


class MISAssignSerializer(serializers.Serializer):
    field_executive = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="field_executive")
    )
    scheduled_date = serializers.DateField()
    inspection_location = serializers.CharField(required=False, allow_blank=True)
