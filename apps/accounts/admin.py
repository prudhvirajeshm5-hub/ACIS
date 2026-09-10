from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import FieldExecutiveProfile, LoginHistory, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "email", "role", "employee_code", "is_active", "is_locked", "last_login"]
    list_filter = ["role", "is_active", "is_locked"]
    search_fields = ["username", "email", "employee_code", "first_name", "last_name"]
    filter_horizontal = ["assigned_clients"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("ACIS profile", {"fields": ("employee_code", "role", "phone", "must_change_password", "is_locked", "created_by")}),
        ("Client scope (MIS Operator role only)", {"fields": ("assigned_clients",)}),
    )
    readonly_fields = ["created_at", "updated_at"]


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ["user", "login_at", "ip_address", "successful", "logout_at"]
    list_filter = ["successful"]
    search_fields = ["user__username", "ip_address"]
    readonly_fields = [f.name for f in LoginHistory._meta.fields]

    def has_add_permission(self, request):
        return False  # audit-style records are system-generated only


@admin.register(FieldExecutiveProfile)
class FieldExecutiveProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "assigned_district", "zone", "active"]
