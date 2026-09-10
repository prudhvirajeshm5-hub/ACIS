def role_permissions(request):
    """Exposes a light permission summary to every template so the sidebar
    and action buttons can hide/disable themselves without each view having
    to pass the same booleans down manually."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {
        "current_role_label": user.role_label,
        "can_manage_users": user.has_perm("accounts.manage_users"),
        "can_manage_masters": user.has_perm("masters.change_insurancecompany"),
        "can_view_audit_log": user.has_perm("audit.view_auditlog"),
        "can_export_reports": user.has_perm("mis.export_mis_excel") or user.has_perm("mis.export_mis_pdf"),
    }
