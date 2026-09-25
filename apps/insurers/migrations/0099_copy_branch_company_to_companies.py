from django.db import migrations


def copy_company_to_companies(apps, schema_editor):
    InsuranceBranch = apps.get_model("insurers", "InsuranceBranch")
    for branch in InsuranceBranch.objects.all():
        if branch.company_id:
            branch.companies.add(branch.company_id)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("insurers", "0002_alter_insurancebranch_options_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_company_to_companies, reverse_noop),
    ]
