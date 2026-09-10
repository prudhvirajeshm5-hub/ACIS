from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related("state", "district", "city").all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ["name", "mobile", "email"]
    filterset_fields = ["district", "state"]
