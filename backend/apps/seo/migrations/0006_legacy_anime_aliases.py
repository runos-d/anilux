import re
from django.db import migrations

def legacy_anime_slug(title: str) -> str:
    replacements = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
        "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
        "э": "e", "ю": "yu", "я": "ya",
    }
    slug = (title or "").lower()
    slug = "".join(replacements.get(char, char) for char in slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")



def populate(apps, schema_editor):
    Anime = apps.get_model('anime', 'Anime')
    Alias = apps.get_model('seo', 'SeoAlias')
    db = schema_editor.connection.alias
    batch = []
    for pk, title in Anime.objects.using(db).order_by('pk').values_list('pk', 'title_ru').iterator(chunk_size=1000):
        slug = legacy_anime_slug(title or '')
        path = '/anime/' + slug
        if slug and len(path) <= 255:
            batch.append(Alias(path=path, kind='anime', object_id=str(pk)))
        if len(batch) >= 500:
            Alias.objects.using(db).bulk_create(batch, ignore_conflicts=True)
            batch = []
    Alias.objects.using(db).bulk_create(batch, ignore_conflicts=True)

class Migration(migrations.Migration):
    dependencies = [('seo', '0005_normalize_anilux_brand'), ('anime', '0015_progress_total_episode_season')]
    operations = [migrations.RunPython(populate, migrations.RunPython.noop)]
