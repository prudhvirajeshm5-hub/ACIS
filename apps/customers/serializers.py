from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "name", "mobile", "email", "address", "state", "district", "city", "created_at"]
        read_only_fields = ["id", "created_at"]
