from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import InsuranceBranch, InsuranceCompany
from .serializers import InsuranceBranchSerializer, InsuranceCompanySerializer


class InsuranceCompanyViewSet(viewsets.ModelViewSet):
    queryset = InsuranceCompany.objects.filter(active=True)
    serializer_class = InsuranceCompanySerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "code"]


class InsuranceBranchViewSet(viewsets.ModelViewSet):
    queryset = InsuranceBranch.objects.filter(active=True).select_related("district").prefetch_related("companies")
    serializer_class = InsuranceBranchSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["company"]
    search_fields = ["name"]
