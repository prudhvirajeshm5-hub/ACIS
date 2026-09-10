from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import MIS
from .serializers import MISAssignSerializer, MISSerializer
from .services import assign_field_executive


class MISViewSet(viewsets.ModelViewSet):
    queryset = MIS.objects.select_related("customer", "vehicle", "insurance_company", "branch", "field_executive").all()
    serializer_class = MISSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["inspection_stage", "qc_stage", "insurance_company", "field_executive", "priority"]
    search_fields = ["mis_number", "customer__name", "customer__mobile", "vehicle__registration_number"]
    ordering_fields = ["mis_date", "created_at"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        if not request.user.has_perm("mis.assign_mis"):
            return Response({"detail": "You do not have permission to assign inspections."}, status=403)
        mis = self.get_object()
        serializer = MISAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assign_field_executive(mis=mis, assigned_by=request.user, **serializer.validated_data)
        return Response(MISSerializer(mis).data)
