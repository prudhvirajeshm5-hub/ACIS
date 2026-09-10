from .middleware import get_current_ip, get_current_user, get_current_user_agent
from .models import AuditLog


def log_action(*, action, module, obj, old_value=None, new_value=None):
    """Call this from views/services for actions that aren't simple model
    saves (e.g. 'export', 'download', 'generate_report', QC decisions)."""
    AuditLog.objects.create(
        user=get_current_user(),
        action=action,
        module=module,
        object_repr=str(obj),
        object_id=str(getattr(obj, "pk", "")),
        old_value=old_value,
        new_value=new_value,
        ip_address=get_current_ip(),
        user_agent=get_current_user_agent(),
    )
