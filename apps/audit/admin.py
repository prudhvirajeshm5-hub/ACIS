from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "user", "action", "module", "object_repr", "ip_address"]
    list_filter = ["action", "module"]
    search_fields = ["object_repr", "object_id", "user__username"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False  # immutable — retention/purging is a DB-level job, not a user action
