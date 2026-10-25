from django.db import migrations, models
from django.db.models import F


def backfill_progress_total(apps, schema_editor):
    Anime = apps.get_model("anime", "Anime")
    Anime.objects.filter(progress_total__isnull=True).update(
        progress_total=F("episodes")
    )


def backfill_episode_season(apps, schema_editor):
    UserEpisodeProgress = apps.get_model("anime", "UserEpisodeProgress")
    rows = UserEpisodeProgress.objects.select_related("anime").all()
    for row in rows.iterator():
        last_season = getattr(row.anime, "last_season", None) or 0
        row.season_number = last_season if last_season > 0 else 1
        row.save(update_fields=["season_number"])


class Migration(migrations.Migration):
    dependencies = [
        ("anime", "0014_watchhistorysuppression"),
    ]

    operations = [
        migrations.AddField(
            model_name="anime",
            name="progress_total",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Всего серий для прогресса (по озвучкам)",
            ),
        ),
        migrations.RunPython(backfill_progress_total, migrations.RunPython.noop),
        migrations.AddField(
            model_name="userepisodeprogress",
            name="season_number",
            field=models.PositiveIntegerField(
                db_index=True, default=1, verbose_name="Номер сезона"
            ),
        ),
        migrations.RunPython(backfill_episode_season, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name="userepisodeprogress",
            unique_together={("user", "anime", "season_number", "episode_number")},
        ),
        migrations.AlterModelOptions(
            name="userepisodeprogress",
            options={
                "ordering": ["season_number", "episode_number"],
                "verbose_name": "Прогресс эпизода",
                "verbose_name_plural": "Прогресс эпизодов",
            },
        ),
    ]
