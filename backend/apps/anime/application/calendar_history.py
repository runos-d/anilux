from datetime import datetime, timezone as dt_timezone

from django.db import transaction
from django.utils import timezone

from apps.anime.infrastructure.models.read_models import CalendarRelease, CalendarSnapshot


def release_values(entry):
    sid = int(entry['id'])
    episode = int(entry.get('episode') or 0)
    aired_at = datetime.fromisoformat(entry['aired_at'].replace('Z', '+00:00'))
    if not aired_at.tzinfo:
        aired_at = aired_at.replace(tzinfo=dt_timezone.utc)
    if sid <= 0 or episode < 0:
        raise ValueError('Invalid calendar release identity')
    return sid, episode, aired_at


def merge_calendar(entries):
    releases = [(entry, release_values(entry)) for entry in entries]
    now = timezone.now()
    with transaction.atomic():
        snapshot, _ = CalendarSnapshot.objects.get_or_create(key='kodik')
        snapshot = CalendarSnapshot.objects.select_for_update().get(pk=snapshot.pk)
        seen = set()
        for entry, (sid, episode, aired_at) in releases:
            release, _ = CalendarRelease.objects.update_or_create(
                shikimori_id=sid, episode=episode,
                defaults={'aired_at': aired_at, 'data': entry, 'schedule_uncertain': False})
            from apps.notifications.models import Reminder
            Reminder.objects.filter(calendar_release=release, follow_schedule=True, is_active=True,
                available_notified_at__isnull=True).exclude(reminder_time=aired_at).update(
                    reminder_time=aired_at, updated_at=now)
            seen.add((sid, episode))
        missing = [row.pk for row in CalendarRelease.objects.filter(aired_at__gt=now)
                   .only('pk', 'shikimori_id', 'episode')
                   if (row.shikimori_id, row.episode) not in seen]
        CalendarRelease.objects.filter(pk__in=missing).update(schedule_uncertain=True)
        snapshot.entries = entries
        snapshot.save(update_fields=['entries', 'updated_at'])
    return len(releases)


def read_calendar(start=None, end=None):
    rows = CalendarRelease.objects.all()
    if start is not None:
        rows = rows.filter(aired_at__gte=start)
    if end is not None:
        rows = rows.filter(aired_at__lt=end)
    now = timezone.now()
    return [{**row.data, 'calendar_release_id': row.pk, 'aired_at': row.aired_at.isoformat(),
             'is_upcoming': row.aired_at > now, 'schedule_uncertain': row.schedule_uncertain}
            for row in rows.order_by('aired_at', 'shikimori_id', 'episode')]
