from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("notifications", "0007_episode_baselines"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complaint",
            name="reason",
            field=models.CharField(choices=[('spam', 'Спам'), ('harassment', 'Харассмент'), ('inappropriate', 'Неподходящий контент'), ('copyright', 'Нарушение авторских прав'), ('misleading', 'Вводящая в заблуждение информация'), ('broken_link', 'Битая ссылка'), ('duplicate', 'Дубликат'), ('spoiler', 'Спойлер без предупреждения'), ('other', 'Другое')], max_length=20),
        ),
        migrations.AddField(
            model_name="complaint",
            name="action_taken",
            field=models.CharField(blank=True, max_length=32),
        ),
        migrations.AddField(
            model_name="complaint",
            name="source_report_id",
            field=models.PositiveBigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="target_snapshot",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
