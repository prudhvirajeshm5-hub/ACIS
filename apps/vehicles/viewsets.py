from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Vehicle
from .serializers import VehicleSerializer


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.select_related("vehicle_type", "fuel_type", "owner").all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["registration_number", "chassis_number", "engine_number", "make", "model"]
    filterset_fields = ["vehicle_type", "fuel_type"]