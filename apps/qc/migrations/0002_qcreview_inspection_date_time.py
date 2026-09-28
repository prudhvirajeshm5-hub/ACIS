from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qc", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="qcreview",
            name="inspection_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="qcreview",
            name="inspection_time",
            field=models.TimeField(blank=True, null=True),
        ),
    ]
