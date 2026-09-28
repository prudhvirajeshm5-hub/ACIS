import apps.chat.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("kind", models.CharField(choices=[("everyone", "All staff"), ("direct", "Direct"), ("group", "Group")], default="group", max_length=10)),
                ("name", models.CharField(blank=True, max_length=100)),
                ("direct_key", models.CharField(blank=True, max_length=60, null=True, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Membership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("last_read_id", models.BigIntegerField(default=0)),
                ("joined_at", models.DateTimeField(auto_now_add=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="memberships", to="chat.conversation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_memberships", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(blank=True)),
                ("attachment", models.FileField(blank=True, upload_to=apps.chat.models.chat_upload_path)),
                ("attachment_kind", models.CharField(blank=True, max_length=10)),
                ("attachment_name", models.CharField(blank=True, max_length=255)),
                ("attachment_mime", models.CharField(blank=True, max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("conversation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chat.conversation")),
                ("sender", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="chat_messages", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AddConstraint(
            model_name="membership",
            constraint=models.UniqueConstraint(fields=("conversation", "user"), name="uniq_chat_member"),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["conversation", "id"], name="chat_msg_conv_id_idx"),
        ),
    ]
