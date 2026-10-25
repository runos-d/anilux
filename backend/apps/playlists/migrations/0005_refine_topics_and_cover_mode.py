from django.db import migrations, models


def refine(apps, schema_editor):
    Topic = apps.get_model('playlists', 'PlaylistTopic')
    for slug, name in [('beginners', 'Для новичков'), ('evening', 'На один вечер'),
                       ('friends', 'Для компании'), ('cozy', 'Уютное и спокойное'),
                       ('adventure', 'Дух приключений'), ('thoughtful', 'Есть о чём подумать')]:
        Topic.objects.using(schema_editor.connection.alias).update_or_create(slug=slug, defaults={'name': name})
    Playlist = apps.get_model('playlists', 'Playlist')
    custom = []
    for playlist in Playlist.objects.using(schema_editor.connection.alias).exclude(cover_image='').only('pk', 'cover_image').iterator():
        # Retain real uploaded covers. Legacy server mosaics remain stored, but auto mode uses live posters.
        if playlist.cover_image and not playlist.cover_image.name.startswith(f'playlist_covers/playlist_{playlist.pk}_'):
            custom.append(playlist.pk)
        if len(custom) >= 500:
            Playlist.objects.using(schema_editor.connection.alias).filter(pk__in=custom).update(cover_mode='custom')
            custom.clear()
    if custom:
        Playlist.objects.using(schema_editor.connection.alias).filter(pk__in=custom).update(cover_mode='custom')


class Migration(migrations.Migration):
    dependencies = [('playlists', '0004_playlisttopic_playlist_topics_playlistlike')]
    operations = [
        migrations.AddField(model_name='playlist', name='cover_mode', field=models.CharField(max_length=10, choices=[('auto', 'Из постеров'), ('custom', 'Загруженная обложка')], default='auto')),
        migrations.RunPython(refine, migrations.RunPython.noop),
    ]
