from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0009_userlibrary_episode_baseline_and_more")]
    operations = [
        migrations.CreateModel(
            name="TransactionalEmailEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("deduplication_key", models.CharField(max_length=64, unique=True)),
                ("provider_message_id", models.CharField(blank=True, max_length=255)),
                ("event_type", models.CharField(max_length=32)),
                ("recipient", models.EmailField(max_length=254)),
                ("occurred_at", models.DateTimeField()),
                ("diagnostic_code", models.CharField(blank=True, max_length=100)),
                ("diagnostic_reason", models.CharField(blank=True, max_length=500)),
                ("supported", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="SuppressedEmail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("reason", models.CharField(max_length=32)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
