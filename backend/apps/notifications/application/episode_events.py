from datetime import timedelta, timezone as utc_timezone
from zoneinfo import ZoneInfo

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.anime.models import Anime, CalendarRelease, KodikAvailability
from apps.notifications.models import EpisodeNotice, EpisodeSubscription, Reminder
from apps.notifications.application.services import NotificationService


def _notice(user, anime, episode, phase, release=None, reminder=None):
    identity = f's{release.shikimori_id}' if release else (
        f's{anime.shikimori_id}' if anime.shikimori_id else f'a{anime.pk}')
    key = f'episode:{user.pk}:{identity}:{episode}:{phase}'
    receipt, _ = EpisodeNotice.objects.get_or_create(user=user, key=key)
    receipt = EpisodeNotice.objects.select_for_update().get(pk=receipt.pk)
    if receipt.processed:
        return False
    title = (anime.title_ru or anime.title_en) if anime else (
        release.data.get('russian') or release.data.get('name') or 'Аниме')
    if phase == 'available':
        heading = f'Серия {episode} доступна: {title}'
        text = f'В Kodik появилась серия {episode} аниме «{title}».'
        link = f'/anime/{anime.slug or anime.pk}/watch?episode={episode}'
    else:
        heading = f'Выход серии {episode} задерживается'
        text = f'Серия {episode} аниме «{title}» пока недоступна в Kodik. Сообщим, когда она появится.'
        link = f'/anime/{anime.slug or anime.pk}' if anime else '/anime?section=calendar'
    receipt.notification = NotificationService.create_notification(user=user,
        notification_type='episode_available' if phase == 'available' else 'episode_delayed',
        title=heading[:255], content=text, link=link, dedupe_key=key,
        enable_push=reminder.enable_push if reminder else True,
        enable_sound=reminder.enable_sound if reminder else True)
    receipt.processed = True
    receipt.save(update_fields=['notification', 'processed'])
    return receipt.notification is not None


def process_subscriptions():
    count = 0
    now = timezone.now()
    ids = list(EpisodeSubscription.objects.filter(is_active=True, anime__is_available=True,
        user__is_active=True).filter(Q(is_paused=False) | Q(paused_until__lte=now)).values_list('pk', flat=True))
    for pk in ids:
        with transaction.atomic():
            sub = EpisodeSubscription.objects.select_for_update().select_related('anime', 'user').filter(pk=pk, is_active=True).first()
            if not sub or not sub.anime.is_available or not sub.user.is_active or (sub.is_paused and (not sub.paused_until or sub.paused_until > now)):
                continue
            availability = KodikAvailability.objects.filter(anime_id=sub.anime_id).first()
            if not availability:
                continue
            from apps.users.models import UserLibrary
            from apps.users.application.library_episodes import seen_episodes
            library = UserLibrary.objects.filter(user=sub.user, anime=sub.anime).first()
            if not library:
                continue
            cutoff = library.added_at
            pending = set(availability.episodes) - set(sub.notified_episodes)
            dates = dict(CalendarRelease.objects.filter(shikimori_id=sub.anime.shikimori_id,
                episode__in=pending).values_list('episode', 'aired_at')) if sub.anime.shikimori_id else {}
            seen = seen_episodes(library)
            acknowledged = set(sub.notified_episodes) | (pending & seen)
            for episode in sorted(pending):
                released_at = dates.get(episode)
                if released_at is not None and released_at <= cutoff:
                    acknowledged.add(episode)
                elif released_at is not None and cutoff < released_at <= now:
                    if episode not in seen:
                        count += _notice(sub.user, sub.anime, episode, 'available')
                    acknowledged.add(episode)
            sub.baseline_initialized = True
            sub.notified_episodes = sorted(acknowledged)
            sub.last_notified_episode = max(sub.last_notified_episode, max(acknowledged, default=0))
            if sub.is_paused and sub.paused_until and sub.paused_until <= now:
                sub.is_paused, sub.paused_until = False, None
            sub.save()
    return count


def process_reminders(user=None, verified_shikimori_ids=None):
    now = timezone.now()
    queryset = Reminder.objects.filter(is_active=True, user__is_active=True)
    if user is not None:
        queryset = queryset.filter(user=user)
    ids = list(queryset.filter(Q(calendar_release__isnull=False) |
        Q(is_triggered=False, reminder_time__lte=now)).values_list('pk', flat=True))
    triggered = []
    for pk in ids:
        with transaction.atomic():
            reminder = Reminder.objects.select_for_update().select_related('user', 'anime', 'franchise', 'calendar_release').filter(pk=pk, is_active=True).first()
            if not reminder:
                continue
            if reminder.end_date and now > reminder.end_date:
                reminder.is_active = False
                reminder.save(update_fields=['is_active'])
                continue
            if reminder.anime and not reminder.anime.is_available:
                continue
            if reminder.calendar_release_id:
                release = reminder.calendar_release
                anime = reminder.anime or Anime.objects.filter(shikimori_id=release.shikimori_id).first()
                if anime and not anime.is_available:
                    continue
                if anime and not reminder.anime_id:
                    reminder.anime = anime
                availability = KodikAvailability.objects.filter(anime=anime).first() if anime else None
                episode = release.episode or 1
                if availability and episode in availability.episodes:
                    from .episode_verification import verified_recently, VERIFICATION_TTL
                    fresh = availability.updated_at >= now - timedelta(seconds=VERIFICATION_TTL)
                    if not fresh and release.shikimori_id not in (verified_shikimori_ids or set()) and not verified_recently(release.shikimori_id):
                        continue
                    sent = _notice(reminder.user, anime, episode, 'available', release, reminder)
                    reminder.available_notified_at = now
                    reminder.is_active = False
                    reminder.is_triggered = True
                elif reminder.reminder_time <= now and not reminder.delay_notified_at:
                    from .episode_verification import verified_recently
                    if release.shikimori_id not in (verified_shikimori_ids or set()) and not verified_recently(release.shikimori_id, after=reminder.reminder_time):
                        continue
                    sent = _notice(reminder.user, anime, episode, 'delayed', release, reminder)
                    reminder.delay_notified_at = now
                    reminder.is_triggered = True
                else:
                    sent = False
                reminder.save()
                if sent:
                    triggered.append(pk)
                continue
            if reminder.is_triggered or reminder.reminder_time > now:
                continue
            occurrence = reminder.reminder_time.isoformat()
            target_title = reminder.franchise.name if reminder.franchise_id else reminder.anime.title_ru
            target_link = (f'/franchise/{reminder.franchise.slug or reminder.franchise.pk}'
                           if reminder.franchise_id else f'/anime/{reminder.anime.slug or reminder.anime.pk}')
            notification = NotificationService.create_notification(user=reminder.user,
                notification_type='reminder_episode', title=f'⏰ Напоминание: {target_title}'[:255],
                content=f'Время посмотреть {target_title}!' + (f' {reminder.comment}' if reminder.comment else ''),
                link=target_link,
                dedupe_key=f'reminder:{pk}:{occurrence}', enable_push=reminder.enable_push,
                enable_sound=reminder.enable_sound)
            reminder.is_triggered = True
            interval = reminder.repeat_interval_days or (7 if reminder.repeat_weekly else None)
            if interval:
                local = reminder.reminder_time.astimezone(ZoneInfo(reminder.timezone_name))
                steps = max(1, (now.astimezone(local.tzinfo).date() - local.date()).days // interval)
                local += timedelta(days=steps * interval)
                while local <= now:
                    local += timedelta(days=interval)
                reminder.reminder_time = local.astimezone(utc_timezone.utc)
                reminder.is_triggered = False
                if reminder.end_date and reminder.reminder_time > reminder.end_date:
                    reminder.is_active = False
            reminder.save()
            if notification:
                triggered.append(pk)
    return triggered
