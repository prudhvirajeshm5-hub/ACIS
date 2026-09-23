from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehicles", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="vehicle",
            name="vehicles_ve_chassis_9b0dd7_idx",
        ),
        migrations.RemoveIndex(
            model_name="vehicle",
            name="vehicles_ve_engine__c969a4_idx",
        ),
        migrations.RemoveField(
            model_name="vehicle",
            name="engine_number",
        ),
        migrations.RemoveField(
            model_name="vehicle",
            name="chassis_number",
        ),
        migrations.RemoveField(
            model_name="vehicle",
            name="vehicle_type",
        ),
        migrations.RemoveField(
            model_name="vehicle",
            name="make",
        ),
        migrations.RemoveField(
            model_name="vehicle",
            name="model",
        ),
        migrations.AddField(
            model_name="vehicle",
            name="vehicle_type",
            field=models.CharField(
                choices=[("commercial", "Commercial"), ("private", "Private")],
                default="private",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="make",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="vehicle",
            name="model",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
    ]
