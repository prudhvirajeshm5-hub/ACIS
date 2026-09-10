from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.mis.models import MIS, MISInspectionStage, MISQCStage


class DashboardStatsAPIView(APIView):
    """Same numbers the server-rendered dashboard shows, exposed for the
    future Flutter app / any other client (spec: /api/v1/dashboard/)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = MIS.objects.all()
        today = timezone.now().date()
        return Response({
            "total_mis": qs.count(),
            "todays_mis": qs.filter(mis_date=today).count(),
            "pending_inspections": qs.filter(inspection_stage=MISInspectionStage.PENDING).count(),
            "assigned_inspections": qs.filter(inspection_stage=MISInspectionStage.ASSIGNED).count(),
            "completed_inspections": qs.filter(inspection_stage=MISInspectionStage.COMPLETED).count(),
            "pending_qc": qs.filter(qc_stage=MISQCStage.PENDING).count(),
            "qc_approved": qs.filter(qc_stage=MISQCStage.APPROVED).count(),
            "qc_rejected": qs.filter(qc_stage=MISQCStage.REJECTED).count(),
        })
