from rest_framework import serializers

from . import models as m


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.State
        fields = ["id", "name", "code", "active"]


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.District
        fields = ["id", "name", "code", "state", "active"]


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = m.City
        fields = ["id", "name", "code", "district", "active"]


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VehicleType
        fields = ["id", "name", "code", "active"]


class VehicleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VehicleMake
        fields = ["id", "name", "code", "vehicle_type", "active"]


class VehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VehicleModel
        fields = ["id", "name", "code", "make", "active"]


class InspectionItemMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.InspectionItemMaster
        fields = ["id", "name", "display_order", "active"]


class GlassItemMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.GlassItemMaster
        fields = ["id", "name", "display_order", "active"]


class AccessoryMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.AccessoryMaster
        fields = ["id", "name", "display_order", "active"]


class ConditionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.ConditionOption
        fields = ["id", "name", "is_positive", "active"]


class VideoCategoryMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.VideoCategoryMaster
        fields = ["id", "name", "display_order", "active"]


class PhotoCategoryMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = m.PhotoCategoryMaster
        fields = ["id", "name", "display_order", "is_mandatory", "max_count", "active"]
