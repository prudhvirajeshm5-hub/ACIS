from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from . import models as m
from . import serializers as s


class ActiveOnlyMixin:
    """Masters expose only active=True rows by default so form dropdowns
    never show retired options; ?include_inactive=1 surfaces everything
    for the Masters admin screens."""

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("include_inactive") == "1":
            return qs
        return qs.filter(active=True)


class StateViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.State.objects.all()
    serializer_class = s.StateSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["active"]
    search_fields = ["name"]


class DistrictViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.District.objects.select_related("state").all()
    serializer_class = s.DistrictSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["state", "active"]
    search_fields = ["name"]


class CityViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.City.objects.select_related("district").all()
    serializer_class = s.CitySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["district", "active"]
    search_fields = ["name"]


class VehicleTypeViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.VehicleType.objects.all()
    serializer_class = s.VehicleTypeSerializer
    permission_classes = [IsAuthenticated]


class VehicleMakeViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.VehicleMake.objects.select_related("vehicle_type").all()
    serializer_class = s.VehicleMakeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["vehicle_type", "active"]


class VehicleModelViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.VehicleModel.objects.select_related("make").all()
    serializer_class = s.VehicleModelSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["make", "active"]


class InspectionItemMasterViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.InspectionItemMaster.objects.all()
    serializer_class = s.InspectionItemMasterSerializer
    permission_classes = [IsAuthenticated]


class GlassItemMasterViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.GlassItemMaster.objects.all()
    serializer_class = s.GlassItemMasterSerializer
    permission_classes = [IsAuthenticated]


class AccessoryMasterViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.AccessoryMaster.objects.all()
    serializer_class = s.AccessoryMasterSerializer
    permission_classes = [IsAuthenticated]


class ConditionOptionViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.ConditionOption.objects.all()
    serializer_class = s.ConditionOptionSerializer
    permission_classes = [IsAuthenticated]


class VideoCategoryMasterViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.VideoCategoryMaster.objects.all()
    serializer_class = s.VideoCategoryMasterSerializer
    permission_classes = [IsAuthenticated]


class PhotoCategoryMasterViewSet(ActiveOnlyMixin, viewsets.ModelViewSet):
    queryset = m.PhotoCategoryMaster.objects.all()
    serializer_class = s.PhotoCategoryMasterSerializer
    permission_classes = [IsAuthenticated]
