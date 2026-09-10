import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("masters", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PhotoCategoryMaster",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("active", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=150)),
                ("code", models.CharField(blank=True, max_length=30)),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("is_mandatory", models.BooleanField(default=True)),
                (
                    "max_count",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Photos allowed per inspection for this slot. Mandatory slots are always 1.",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True, editable=False, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True, editable=False, null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Photo category",
                "ordering": ["display_order", "name"],
                "abstract": False,
            },
        ),
    ]
