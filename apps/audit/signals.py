"""
Generic audit hook. Call `register_audit_logging(Model, module_label)` from
any app's AppConfig.ready() to automatically log create/update/delete for
that model, without writing a signal handler per model.
"""
from django.db.models.signals import post_delete, post_save

from .utils import log_action


def register_audit_logging(model, module_label, repr_field=None):
    def _on_save(sender, instance, created, **kwargs):
        log_action(
            action="create" if created else "update",
            module=module_label,
            obj=instance,
        )

    def _on_delete(sender, instance, **kwargs):
        log_action(action="delete", module=module_label, obj=instance)

    post_save.connect(_on_save, sender=model, weak=False)
    post_delete.connect(_on_delete, sender=model, weak=False)
