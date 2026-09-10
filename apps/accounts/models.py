import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    """
    Display-only labels for the 8 roles in the spec. The actual permission
    grants live on Django Groups of the same name (see management command
    `seed_roles`), so permissions stay centrally editable from /admin/ or the
    Users & Access screens without touching code. This choice field is a
    convenience default assigned at signup — a user's *real* access is the
    union of their Django Groups + individual user_permissions, exactly like
    stock Django auth.
    """
    SUPER_ADMIN = "super_admin", "Super Admin"
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    QC_EXECUTIVE = "qc_executive", "QC Executive"
    FIELD_EXECUTIVE = "field_executive", "Field Executive"
    MIS_OPERATOR = "mis_operator", "MIS Operator"
    ACCOUNTS_BILLING = "accounts_billing", "Accounts/Billing User"
    READ_ONLY = "read_only", "Read-only/Report User"


class User(AbstractUser):
    """
    Extends Django's battle-tested auth User (secure password hashing,
    session framework, permission framework) rather than reinventing it.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_code = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=32, choices=Role.choices, default=Role.READ_ONLY)
    phone = models.CharField(max_length=15, blank=True)
    must_change_password = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="created_users"
    )
    assigned_clients = models.ManyToManyField(
        "insurers.InsuranceCompany", blank=True, related_name="assigned_users",
        help_text="Insurance companies (clients) this user is scoped to. Currently enforced "
                  "for the MIS Operator role only — see CLIENT_SCOPED_ROLES in this file.",
    )

    # Roles whose visibility of MIS/insurers is restricted to their
    # assigned_clients. Every other role (including one left with an empty
    # assigned_clients set) sees all active clients — client-scoping is an
    # opt-in restriction for specific roles, not a default-deny rule, so
    # adding a role here is a deliberate access-narrowing decision.
    CLIENT_SCOPED_ROLES = {Role.MIS_OPERATOR}

    class Meta:
        ordering = ["username"]
        permissions = [
            ("manage_users", "Can create, edit, deactivate and reset passwords for other users"),
            ("view_login_history", "Can view login history for any user"),
        ]

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def role_label(self):
        return self.get_role_display()

    def is_client_scoped(self):
        return not self.is_superuser and self.role in self.CLIENT_SCOPED_ROLES

    def visible_insurance_companies(self):
        """
        The queryset of InsuranceCompany rows this user may see/select.
        Used to filter the MIS list, dashboard stats, and the Create MIS
        insurer dropdown. Imported lazily to avoid a circular import at
        module load time (insurers app models import from masters, and
        both are loaded well before this method is ever called).
        """
        from apps.insurers.models import InsuranceCompany
        qs = InsuranceCompany.objects.filter(active=True)
        if self.is_client_scoped():
            return self.assigned_clients.filter(active=True)
        return qs


class LoginHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_history")
    login_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    successful = models.BooleanField(default=True)
    logout_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-login_at"]
        verbose_name_plural = "Login history"

    def __str__(self):
        return f"{self.user} @ {self.login_at:%Y-%m-%d %H:%M}"


class FieldExecutiveProfile(models.Model):
    """Extra fields specific to the Field Executive role."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="field_profile")
    assigned_district = models.ForeignKey(
        "masters.District", null=True, blank=True, on_delete=models.SET_NULL
    )
    zone = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Field profile: {self.user}"
