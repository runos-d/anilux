from django.db import migrations


def seed(apps, schema_editor):
    alias = schema_editor.connection.alias
    Anime = apps.get_model('anime', 'Anime')
    Availability = apps.get_model('anime', 'KodikAvailability')
    Library = apps.get_model('users', 'UserLibrary')
    Subscription = apps.get_model('notifications', 'EpisodeSubscription')
    available = {}
    pending = []
    announced = set(Anime.objects.using(alias).filter(status='announced').values_list('pk', flat=True))
    for anime in Anime.objects.using(alias).only('pk', 'raw_kodik_data').iterator(chunk_size=500):
        raw = anime.raw_kodik_data
        if not isinstance(raw, dict) or not raw.get('link'):
            continue
        numbers = None
        if raw.get('type') == 'anime':
            numbers = [1]
        elif raw.get('type') == 'anime-serial':
            explicit = set()
            detailed = False
            seasons = raw.get('seasons') or {}
            for season in seasons.values() if isinstance(seasons, dict) else []:
                if isinstance(season, dict) and isinstance(season.get('episodes'), dict):
                    detailed = True
                    for number, link in season['episodes'].items():
                        if str(number).isdigit() and link and 0 < int(number) <= 10000:
                            explicit.add(int(number))
            if detailed:
                numbers = sorted(explicit)
            else:
                try:
                    last = int(raw['last_episode'])
                    if 0 <= last <= 10000:
                        numbers = list(range(1, last + 1))
                except (KeyError, ValueError, TypeError):
                    pass
        if numbers is not None:
            available[anime.pk] = numbers
            pending.append(Availability(anime_id=anime.pk, episodes=numbers, last_episode=max(numbers, default=0)))
            if len(pending) >= 500:
                Availability.objects.using(alias).bulk_create(pending, ignore_conflicts=True)
                pending = []
    Availability.objects.using(alias).bulk_create(pending, ignore_conflicts=True)
    for item in Library.objects.using(alias).all().iterator(chunk_size=500):
        numbers = available.get(item.anime_id, [] if item.anime_id in announced else None)
        watched = max(item.current_episode or 0, item.episodes_watched or 0, item.real_episodes_watched or 0)
        if item.status == 'completed' and numbers is not None:
            watched = max(max(numbers, default=0), item.real_episodes_watched or 0)
        Library.objects.using(alias).filter(pk=item.pk).update(episode_baseline=numbers, watched_through=watched)
        sub, created = Subscription.objects.using(alias).get_or_create(user_id=item.user_id, anime_id=item.anime_id)
        Subscription.objects.using(alias).filter(pk=sub.pk).update(
            manually_disabled=not sub.is_active if not created else False,
            baseline_initialized=numbers is not None,
            notified_episodes=numbers or [],
            last_notified_episode=max(sub.last_notified_episode, max(numbers or [], default=0)))
    # Existing manual subscriptions outside the collection keep their active state too.
    Subscription.objects.using(alias).filter(is_active=False).update(manually_disabled=True)


class Migration(migrations.Migration):
    dependencies = [('notifications', '0006_episodenotice_alter_reminder_unique_together_and_more'),
                    ('users', '0009_userlibrary_episode_baseline_and_more')]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
