import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="IncentiveTarget",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("metric", models.CharField(choices=[("inspections", "Inspections submitted"), ("qc", "QC reviews completed"), ("mis", "MIS created")], default="inspections", max_length=20)),
                ("target_count", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("incentive_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incentive_targets", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-start_date", "-created_at"],
                "permissions": [("manage_targets", "Can assign targets to employees")],
            },
        ),
    ]
