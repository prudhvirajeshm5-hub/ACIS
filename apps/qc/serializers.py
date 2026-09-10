from rest_framework import serializers

from .models import QCReview


class QCReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = QCReview
        fields = ["id", "inspection", "qc_executive", "decision", "remarks", "reviewed_at", "supersedes"]
        read_only_fields = ["id", "qc_executive", "reviewed_at", "supersedes"]
