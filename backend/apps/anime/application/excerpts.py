from urllib.parse import urlsplit
from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError
from apps.anime.models import Excerpt


def available(excerpt):
    return bool(excerpt and excerpt.anime.is_available)


def excerpt_data(excerpt, *, owner=False):
    if not available(excerpt) or (not owner and not excerpt.shared):
        return None
    anime = excerpt.anime
    data = {key: getattr(excerpt, key) for key in (
        'id', 'season', 'episode', 'translation_id', 'translation_title', 'duration',
        'start', 'end', 'title', 'description', 'shared', 'created_at', 'updated_at')}
    data.update(anime_id=anime.pk, anime_title=anime.title_ru or anime.title_en,
                poster_url=anime.poster.url if anime.poster else anime.poster_url,
                player_link=excerpt.player_link,
                share_path=f'/excerpts/s/{excerpt.share_token}' if excerpt.shared else None)
    return data


def attachment_data(pk):
    return excerpt_data(Excerpt.objects.select_related('anime').filter(pk=pk).first())


@transaction.atomic
def enable_attachment(pk, user):
    excerpt = Excerpt.objects.select_for_update().select_related('anime').filter(pk=pk, author=user).first()
    if not available(excerpt):
        raise ValidationError({'excerpt_ids': 'Отрывок недоступен или принадлежит другому автору'})
    if not excerpt.shared:
        excerpt.shared = True
        excerpt.save(update_fields=['shared', 'updated_at'])
    return excerpt


def material(anime, season, episode, translation_id):
    from apps.anime.application.anime_service import anime_service
    raw = anime.raw_kodik_data or {}
    link = None
    title = ''
    if str((raw.get('translation') or {}).get('id')) == str(translation_id):
        title = (raw.get('translation') or {}).get('title', '')
        if raw.get('type') == 'anime' and season == episode == 1:
            link = raw.get('link') or anime.kodik_link
        else:
            link = ((raw.get('seasons') or {}).get(str(season), {}).get('episodes') or {}).get(str(episode))
    if not link and anime.shikimori_id:
        try:
            translations = anime_service.get_translations(anime.shikimori_id)
            translation = next((item for item in translations if str(item['id']) == str(translation_id)), None)
            if translation:
                title = translation['name']
                if translation.get('material_type') == 'anime' and season == episode == 1:
                    link = translation['kodik_link']
                else:
                    link = anime_service.get_episode_url(str(anime.shikimori_id), episode, str(season), str(translation_id))
        except Exception as error:
            from rest_framework.exceptions import APIException
            failure = APIException('Не удалось проверить серию в Kodik. Повторите сохранение позже.')
            failure.status_code = 503
            raise failure from error
    if not link:
        raise ValidationError({'episode': 'Серия и озвучка не найдены в Kodik'})
    link = 'https:' + link if link.startswith('//') else link
    parsed = urlsplit(link)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValidationError({'episode': 'Некорректная ссылка плеера'})
    return link, title
