from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .serializers import UserCreateSerializer, UserSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Never serializes password_hash or any credential — see UserSerializer."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # DjangoModelPermissions (global default) additionally
    # requires accounts.manage_users-equivalent add/change/delete perms for
    # non-safe methods, since those are the auto-generated permissions for
    # this model.
    search_fields = ["username", "email", "employee_code"]
    filterset_fields = ["role", "is_active"]

    def get_serializer_class(self):
        return UserCreateSerializer if self.action == "create" else UserSerializer
