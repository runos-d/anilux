from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('social', '0027_repair_legacy_query_indexes')]
    operations = [
        migrations.AddField('chattheme', 'anime_card_border_radius', models.PositiveSmallIntegerField(default=12)),
        migrations.AddField('chattheme', 'playlist_card_border_radius', models.PositiveSmallIntegerField(default=12)),
    ]
