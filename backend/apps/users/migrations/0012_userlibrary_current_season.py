from django.db import migrations, models


def backfill_library_season(apps, schema_editor):
    UserLibrary = apps.get_model("users", "UserLibrary")
    UserEpisodeProgress = apps.get_model("anime", "UserEpisodeProgress")

    for library in UserLibrary.objects.select_related("anime").iterator():
        latest = (
            UserEpisodeProgress.objects.filter(
                user_id=library.user_id, anime_id=library.anime_id
            )
            .order_by("-season_number", "-episode_number")
            .first()
        )
        if latest is not None:
            library.current_season = latest.season_number
            library.current_episode = latest.episode_number
        else:
            last_season = getattr(library.anime, "last_season", None) or 0
            library.current_season = last_season if last_season > 0 else 1
        library.save(update_fields=["current_season", "current_episode"])


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0011_normalize_unique_user_email"),
        ("anime", "0015_progress_total_episode_season"),
    ]

    operations = [
        migrations.AddField(
            model_name="userlibrary",
            name="current_season",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(backfill_library_season, migrations.RunPython.noop),
    ]
