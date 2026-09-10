import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inspections", "0001_initial"),
        ("masters", "0002_photocategorymaster"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="inspectionphoto",
            name="inspections_inspect_d40079_idx",
        ),
        migrations.RemoveField(
            model_name="inspectionphoto",
            name="category",
        ),
        migrations.AddField(
            model_name="inspectionphoto",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="photos",
                to="masters.photocategorymaster",
                default=None,
            ),
            preserve_default=False,
        ),
        migrations.AddIndex(
            model_name="inspectionphoto",
            index=models.Index(fields=["inspection", "category"], name="inspections_inspect_photocat_idx"),
        ),
    ]
