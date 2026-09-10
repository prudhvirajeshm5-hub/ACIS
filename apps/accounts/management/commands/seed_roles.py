"""
Creates the 8 roles from the spec as Django Groups and assigns a sensible
default permission set to each, using Django's built-in, auto-generated
per-model permissions (add_/change_/delete_/view_<model>) plus the custom
ones declared in each app's Meta.permissions.

This is the "centralized permission system" the spec asks for: permissions
are never hard-coded into views/templates — they're granted to groups here
(or later from /admin/), and every view/API checks request.user.has_perm(...).

Run again any time you add a new custom permission — it's idempotent.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


ROLE_PERMISSIONS = {
    "Super Admin": "__all__",
    "Admin": "__all__",
    "Manager": [
        "mis.*", "insurers.*", "customers.*", "vehicles.*",
        "inspections.view_*", "inspections.assign_inspection", "inspections.reassign_inspection",
        "qc.*", "audit.view_auditlog", "mis.export_mis_excel", "mis.export_mis_pdf",
    ],
    "QC Executive": [
        "inspections.view_*", "qc.*", "mis.view_mis",
        "inspections.download_media",
    ],
    "Field Executive": [
        "inspections.view_inspection", "inspections.change_inspection",
        "inspections.upload_photo", "inspections.upload_video",
        "inspections.add_inspectionphoto", "inspections.add_inspectionvideo",
        "inspections.submit_inspection",
        "mis.view_mis",
    ],
    "MIS Operator": [
        "mis.add_mis", "mis.change_mis", "mis.view_mis", "mis.assign_mis",
        "customers.*", "vehicles.*",
        "inspections.view_inspection", "insurers.view_insurancecompany",
    ],
    "Accounts/Billing User": [
        "billing.*", "mis.view_mis", "mis.view_financial_info", "mis.export_mis_excel",
    ],
    "Read-only/Report User": [
        "mis.view_mis", "inspections.view_inspection", "qc.view_qcreview", "mis.export_mis_excel", "mis.export_mis_pdf",
    ],
}


class Command(BaseCommand):
    help = "Create/update the standard ACIS roles (Django Groups) and their default permissions."

    def handle(self, *args, **options):
        all_perms = Permission.objects.all()

        for role_name, spec in ROLE_PERMISSIONS.items():
            group, created = Group.objects.get_or_create(name=role_name)

            if spec == "__all__":
                perms = all_perms
            else:
                perms = []
                for pattern in spec:
                    if pattern.endswith(".*"):
                        app_label = pattern[:-2]
                        perms += list(all_perms.filter(content_type__app_label=app_label))
                    elif ".view_*" in pattern:
                        app_label = pattern.split(".")[0]
                        perms += list(all_perms.filter(content_type__app_label=app_label, codename__startswith="view_"))
                    else:
                        app_label, codename = pattern.split(".")
                        perms += list(all_perms.filter(content_type__app_label=app_label, codename=codename))

            group.permissions.set(perms)
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} role '{role_name}' with {len(perms) if spec != '__all__' else perms.count()} permissions"))

        self.stdout.write(self.style.SUCCESS("Done. Assign users to these groups from /admin/ or the Users & Access screen."))
