import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("users", "0012_userlibrary_current_season")]

    operations = [
        migrations.RenameModel(old_name="UserAnalytics", new_name="UserActivitySummary"),
        migrations.AlterField(
            model_name="useractivitysummary",
            name="user",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="activity_summary", to="users.user"),
        ),
        migrations.AddField(
            model_name="privacysettings", name="analytics_consent_state",
            field=models.CharField(choices=[("unknown", "Не выбрано"), ("granted", "Разрешено"), ("denied", "Отклонено")], default="unknown", max_length=10),
        ),
        migrations.AddField(
            model_name="privacysettings", name="analytics_consent_version",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="privacysettings", name="analytics_consent_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="privacysettings", name="analytics_consent_source",
            field=models.CharField(blank=True, max_length=24),
        ),
        migrations.AddField(
            model_name="dataexport", name="error_code",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AlterField(
            model_name="dataexport", name="status",
            field=models.CharField(choices=[("queued", "В очереди"), ("processing", "Обработка"), ("ready", "Готов"), ("expired", "Истёк"), ("failed", "Ошибка"), ("canceled", "Отменён")], default="queued", max_length=20),
        ),
        migrations.AlterModelOptions(
            name="useractivitysummary",
            options={"verbose_name": "User activity summary", "verbose_name_plural": "User activity summaries"},
        ),
    ]
