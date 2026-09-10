"""
Centralized, reusable permission helpers used by both the server-rendered
views and the DRF API, so a permission is defined once (as a Django
Permission tied to a model) and enforced everywhere the same way.
"""
from django.contrib.auth.mixins import PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.core.exceptions import PermissionDenied


class PermissionRequiredMixin(DjangoPermissionRequiredMixin):
    """Same as Django's, but raises 403 instead of redirecting to login
    when the user is authenticated but simply lacks the permission —
    redirecting an authenticated-but-unauthorized user to /login/ is
    confusing and leaks nothing useful."""

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied(self.get_permission_denied_message())
        return super().handle_no_permission()


def user_has_perms(user, *perm_codenames):
    """`perm_codenames` like 'mis.assign_mis'. Superusers and Super Admin role bypass."""
    if user.is_superuser or user.role == "super_admin":
        return True
    return all(user.has_perm(p) for p in perm_codenames)
