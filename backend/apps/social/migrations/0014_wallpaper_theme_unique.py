from django.db import migrations, models
from django.db.models import Count, Max


def dedupe(apps, schema_editor):
    for model_name, field in (
        ('ChatWallpaper', 'chat'),
        ('ChatWallpaper', 'private_chat'),
        ('ChatTheme', 'chat'),
        ('ChatTheme', 'private_chat'),
    ):
        model = apps.get_model('social', model_name)
        duplicates = (
            model.objects.filter(**{f'{field}__isnull': False})
            .values('user_id', field)
            .annotate(keep=Max('id'), total=Count('id'))
            .filter(total__gt=1)
        )
        for row in duplicates:
            model.objects.filter(
                user_id=row['user_id'], **{field: row[field]}
            ).exclude(id=row['keep']).delete()


class Migration(migrations.Migration):
    dependencies = [
        # зависит от сгенерированной ранее миграции схемы (News/Achievement/
        # code), чтобы не было двух leaf-узлов в графе
        ("social", "0013_achievement_icon_svg_achievement_is_active_and_more"),
    ]

    operations = [
        migrations.RunPython(dedupe, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="chatwallpaper",
            constraint=models.UniqueConstraint(
                fields=("user", "chat"), name="uniq_wallpaper_user_chat"
            ),
        ),
        migrations.AddConstraint(
            model_name="chatwallpaper",
            constraint=models.UniqueConstraint(
                fields=("user", "private_chat"), name="uniq_wallpaper_user_pchat"
            ),
        ),
        migrations.AddConstraint(
            model_name="chattheme",
            constraint=models.UniqueConstraint(
                fields=("user", "chat"), name="uniq_theme_user_chat"
            ),
        ),
        migrations.AddConstraint(
            model_name="chattheme",
            constraint=models.UniqueConstraint(
                fields=("user", "private_chat"), name="uniq_theme_user_pchat"
            ),
        ),
    ]
