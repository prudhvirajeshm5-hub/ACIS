from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mis", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="mis",
            name="intimator_email",
            field=models.EmailField(blank=True, max_length=254),
        ),
    ]
