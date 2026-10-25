from datetime import datetime, timezone

from django.db import migrations, models


def preserve_snapshot(apps, schema_editor):
    Snapshot = apps.get_model('anime', 'CalendarSnapshot')
    Release = apps.get_model('anime', 'CalendarRelease')
    alias = schema_editor.connection.alias
    snapshot = Snapshot.objects.using(alias).filter(key='kodik').first()
    for entry in snapshot.entries if snapshot else []:
        # Both historical raw and current normalized snapshots are recoverable.
        anime = entry.get('anime') or {}
        sid = entry.get('id') or anime.get('id')
        date = entry.get('aired_at') or entry.get('next_episode_at')
        if not sid or not date:
            continue  # Original snapshot remains untouched, including unparseable rows.
        try:
            aired_at = datetime.fromisoformat(date.replace('Z', '+00:00'))
            if not aired_at.tzinfo:
                aired_at = aired_at.replace(tzinfo=timezone.utc)
            episode = int(entry.get('episode') or entry.get('next_episode') or 0)
            data = {**entry, 'id': int(sid), 'episode': episode, 'aired_at': aired_at.isoformat()}
            if anime:
                data.update(name=anime.get('name', ''), russian=anime.get('russian', ''),
                            english=anime.get('name', ''), image=anime.get('image') or {})
            if int(sid) <= 0 or episode < 0:
                continue
        except (ValueError, TypeError):
            continue
        Release.objects.using(alias).update_or_create(
            shikimori_id=int(sid), episode=episode, defaults={'aired_at': aired_at, 'data': data})


class Migration(migrations.Migration):
    dependencies = [('anime', '0008_anime_franchise_checked_at')]
    operations = [
        migrations.CreateModel(name='CalendarRelease', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('shikimori_id', models.PositiveIntegerField()),
            ('episode', models.PositiveIntegerField(default=0)),
            ('aired_at', models.DateTimeField(db_index=True)),
            ('data', models.JSONField(default=dict)),
            ('schedule_uncertain', models.BooleanField(default=False)),
        ], options={'constraints': [models.UniqueConstraint(
            fields=('shikimori_id', 'episode'), name='calendar_release_identity')]}),
        migrations.RunPython(preserve_snapshot, migrations.RunPython.noop),
    ]
