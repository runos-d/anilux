# Каталог: быстрый ORDER BY score при стандартных фильтрах списка аниме.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("anime", "0003_remove_anilist_id"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="anime",
            index=models.Index(
                fields=["is_available", "has_cyrillic", "-score"],
                name="anime_anime_is_avai_8585e2_idx",
            ),
        ),
    ]
