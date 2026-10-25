from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("anime", "0013_anime_franchise_manual_catalogvisibility_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WatchHistorySuppression",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("hidden_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("anime", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watch_history_suppressions", to="anime.anime")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watch_history_suppressions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Скрытая запись истории просмотров",
                "verbose_name_plural": "Скрытые записи истории просмотров",
            },
        ),
        migrations.AddConstraint(
            model_name="watchhistorysuppression",
            constraint=models.UniqueConstraint(fields=("user", "anime"), name="unique_watch_history_suppression"),
        ),
        migrations.AddIndex(
            model_name="watchhistorysuppression",
            index=models.Index(fields=["user", "hidden_at"], name="anime_watch_user_id_7fa170_idx"),
        ),
    ]
