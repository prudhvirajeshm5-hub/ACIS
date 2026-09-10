from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from .models import QCReview
from .serializers import QCReviewSerializer
from .services import record_qc_decision


class QCReviewViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Append-only from the API too — no update/destroy actions registered."""
    queryset = QCReview.objects.select_related("inspection", "qc_executive").all()
    serializer_class = QCReviewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["inspection", "decision"]

    def perform_create(self, serializer):
        review = record_qc_decision(
            inspection=serializer.validated_data["inspection"],
            qc_executive=self.request.user,
            decision=serializer.validated_data["decision"],
            remarks=serializer.validated_data.get("remarks", ""),
        )
        serializer.instance = review
