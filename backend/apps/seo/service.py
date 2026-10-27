import re
import math
from collections import Counter
from html import unescape
from dataclasses import dataclass, field
from string import Formatter
from urllib.parse import quote, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q, Max, Count
from django.db.models.functions import Length
from django.utils.text import slugify
from django.utils.html import strip_tags

from apps.anime.infrastructure.models.anime import Anime, Franchise, Genre
from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set
from apps.anime.application.catalog_visibility import hidden_values, is_hidden_value, visible_anime
from apps.social.application.post_access import readable_posts
from apps.social.infrastructure.models.social import Post
from apps.playlists.infrastructure.models.playlists import Playlist
from .models import SEO_PATH_MAX_LENGTH, SiteSeoSettings, SeoCollection, SeoOverride, SeoAlias
from .navigation import site_navigation
from config import feature_flags

PAGE_SIZE = 24
MIN_TITLES = 5
MIN_FRANCHISE_PARTS = 2
MIN_PROFILE_BIO_LENGTH = 80
MIN_POST_TEXT_LENGTH = 160
MIN_PLAYLIST_ITEMS = 5
MIN_PLAYLIST_DESCRIPTION_LENGTH = 60
SEASONS = {'winter': ('Зима', (1, 2, 3)), 'spring': ('Весна', (4, 5, 6)),
           'summer': ('Лето', (7, 8, 9)), 'autumn': ('Осень', (10, 11, 12))}
KINDS = dict(Anime.KIND_CHOICES)
STATUSES = dict(Anime.STATUS_CHOICES)
KIND_LABELS = {
    'tv': 'ТВ-сериал', 'movie': 'Аниме-фильм', 'ova': 'OVA', 'ona': 'ONA',
    'special': 'Спецвыпуск', 'music': 'Музыкальное аниме', 'franchise': 'Франшиза',
}
STATUS_LABELS = {
    'ongoing': 'Онгоинг', 'finished': 'Завершён', 'released': 'Вышел',
    'announced': 'Анонсирован', 'canceled': 'Отменён',
}
TYPE_PAGE_NAMES = {
    'tv': 'Аниме-сериалы', 'movie': 'Полнометражные аниме', 'ova': 'OVA-аниме',
    'ona': 'ONA-аниме', 'special': 'Спецвыпуски аниме', 'music': 'Музыкальные аниме',
}
STATUS_PAGE_NAMES = {
    'ongoing': 'Аниме-онгоинги', 'finished': 'Завершённые аниме',
    'announced': 'Анонсированные аниме', 'canceled': 'Отменённые аниме',
}
FIELDS = {'name', 'site', 'count', 'summary', 'page'}


def plural_ru(number, one, few, many):
    number = abs(int(number or 0))
    if number % 10 == 1 and number % 100 != 11:
        return one
    if number % 10 in (2, 3, 4) and number % 100 not in (12, 13, 14):
        return few
    return many


def count_phrase(number, one, few, many):
    return f'{number} {plural_ru(number, one, few, many)}'


def episode_phrase(number):
    return count_phrase(number, 'серия', 'серии', 'серий')


def part_phrase(number):
    return count_phrase(number, 'часть', 'части', 'частей')


def _fallback_slug(value):
    transliteration = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    return slugify(''.join(transliteration.get(char, char) for char in clean_text(value).lower()))


def genre_catalog(qs=None):
    from django.core.cache import cache
    try:
        revision = cache.get('catalog:revision', 0)
    except Exception:
        revision = 0
    from django.db import connection
    database = connection.settings_dict.get('NAME', 'default')
    key = f'seo:genre-catalog:v2:{database}:{revision}'
    cached = safe_cache_get(key)
    if cached is not None:
        return cached
    qs = qs if qs is not None else visible_anime()
    names = set()
    for values in qs.order_by().values_list('genres', flat=True).iterator(chunk_size=2000):
        if isinstance(values, list):
            names.update(clean_text(value) for value in values if clean_text(value))
    configured = dict(Genre.objects.filter(name__in=names).values_list('name', 'slug'))
    used = set()
    catalog = []
    for name in sorted(names, key=str.casefold):
        base = configured.get(name) or _fallback_slug(name)
        if not base:
            continue
        slug_value, suffix = base, 2
        while slug_value in used:
            slug_value, suffix = f'{base}-{suffix}', suffix + 1
        used.add(slug_value)
        catalog.append({'name': name, 'slug': slug_value})
    safe_cache_set(key, catalog, 300)
    return catalog


def genre_name(slug_value, qs=None):
    return next((row['name'] for row in genre_catalog(qs) if row['slug'] == slug_value), None)


def clean_text(value, limit=None):
    value = unescape(str(value or ''))
    value = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', '', value, flags=re.I | re.S)
    value = strip_tags(value)
    value = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2066-\u2069\ufeff]', '', value)
    value = re.sub(r'\s+', ' ', value).strip()
    if limit and len(value) > limit:
        shortened = value[:limit - 1]
        value = (shortened.rsplit(' ', 1)[0] if ' ' in shortened else shortened).rstrip(' ,.;:--') + '…'
    return value


def validate_templates(templates):
    if not isinstance(templates, dict):
        raise ValidationError('Шаблоны должны быть объектом JSON.')
    try:
        for kind, values in templates.items():
            if kind not in {'home', 'catalog', 'collection', 'franchise_directory', 'anime', 'franchise', 'profile', 'post', 'playlist'} or not isinstance(values, dict):
                raise ValueError('Неизвестный тип страницы')
            for key, value in values.items():
                if key not in {'title', 'description', 'h1'} or not isinstance(value, str):
                    raise ValueError('Ожидались текстовые title, description, h1')
                for _, name, spec, conversion in Formatter().parse(value):
                    if name is not None and (name not in FIELDS or spec or conversion):
                        raise ValueError('Разрешены только простые подстановки: ' + ', '.join(sorted(FIELDS)))
    except (ValueError, TypeError) as exc:
        raise ValidationError(str(exc))


def site_config(request):
    config = SiteSeoSettings.objects.first()
    name = config.site_name if config else settings.SEO_SITE_NAME
    origin = (config.public_origin if config else settings.SEO_PUBLIC_ORIGIN).rstrip('/')
    enabled = config.indexing_enabled if config else settings.SEO_INDEXING_ENABLED
    parsed = urlsplit(origin)
    public = bool(enabled and parsed.scheme == 'https' and parsed.hostname and
                  parsed.hostname not in {'localhost', '127.0.0.1', 'backend', 'testserver'} and
                  not parsed.hostname.endswith(('.local', '.test', '.localhost')))
    return name, origin or request.build_absolute_uri('/').rstrip('/'), public, config


def anime_path(anime):
    prefix = f'/anime/{anime.pk}-'
    slug = anime.slug or 'anime'
    return prefix + slug[:SEO_PATH_MAX_LENGTH - len(prefix)]


def franchise_path(franchise):
    unique_slug = franchise.slug and not Franchise.objects.filter(slug=franchise.slug).exclude(pk=franchise.pk).exists()
    slug_path = f'/franchise/{franchise.slug}' if unique_slug else ''
    return slug_path if slug_path and len(slug_path) <= SEO_PATH_MAX_LENGTH else f'/franchise/{franchise.pk}'


def profile_path(user):
    return '/@' + quote(user.nickname, safe='') if user.nickname else f'/profile/{user.pk}'


def filter_query(filters, validate=False):
    if not isinstance(filters, dict) or not filters or set(filters) - {'year', 'genre', 'season', 'kind', 'status'}:
        raise ValidationError('Нужны непустые условия year/genre/season/kind/status.')
    q = Q()
    for key, value in filters.items():
        if key == 'year':
            if not isinstance(value, int) or not 1900 <= value <= 2200:
                raise ValidationError('Некорректный год.')
            q &= Q(year=value)
        elif key == 'genre':
            name = genre_name(value) if isinstance(value, str) else None
            if name is None or is_hidden_value('genre', name):
                raise ValidationError('Жанр не найден.')
            q &= Q(genres__contains=[name])
        elif key == 'season':
            if not isinstance(value, str) or value not in SEASONS or 'year' not in filters:
                raise ValidationError('Сезон winter/spring/summer/autumn требует год.')
            q &= Q(release_date__month__in=SEASONS[value][1])
        elif key in ('kind', 'status'):
            if not isinstance(value, str) or value not in (KINDS if key == 'kind' else STATUSES):
                raise ValidationError('Неизвестный тип или статус.')
            if key == 'kind' and is_hidden_value('kind', value):
                raise ValidationError('Тип недоступен.')
            q &= Q(**{key + '__in': ['finished', 'released']}) if key == 'status' and value == 'finished' else Q(**{key: value})
    return q


@dataclass
class Page:
    path: str
    kind: str = 'utility'
    name: str = 'Страница'
    text: str = ''
    status: int = 200
    indexable: bool = False
    items: list = field(default_factory=list)
    related: list = field(default_factory=list)
    crumbs: list = field(default_factory=list)
    facts: list = field(default_factory=list)
    count: int = 0
    number: int = 1
    pages: int = 1
    page_size: int = PAGE_SIZE
    image: str = ''
    modified: object = None
    schema: list = field(default_factory=list)
    redirect: str = ''
    title: str = ''
    description: str = ''
    h1: str = ''
    canonical: str = ''
    robots: str = 'noindex,follow'
    site: str = ''
    first_url: str = ''
    previous_url: str = ''
    next_url: str = ''


def card(anime):
    return {'name': anime.title_ru or anime.title_en, 'path': anime_path(anime),
            'id': anime.pk, 'slug': anime.slug, 'status': anime.status, 'score': anime.score,
            'episodes': anime.episodes, 'genres': anime.genres, 'type': anime.kind,
            'image': anime.poster_image_url, 'year': anime.year, 'kind': KIND_LABELS.get(anime.kind, anime.kind),
            'season': next((name for name, (_, months) in SEASONS.items() if anime.release_date and anime.release_date.month in months), None)}


def franchise_card(franchise, count=None, fallback_image=''):
    count = count if count is not None else getattr(franchise, '_seo_parts_count', 0)
    image = franchise.poster_image_url
    image = image or fallback_image
    return {
        'name': franchise.name,
        'path': franchise_path(franchise),
        'id': franchise.pk,
        'slug': franchise.slug,
        'image': image,
        'year': franchise.year_start,
        'year_end': franchise.year_end,
        'kind': f'Франшиза · {part_phrase(count)}',
        'parts_count': count,
        'score': franchise.score,
        'genres': franchise.genres if isinstance(franchise.genres, list) else [],
    }


def paginate_franchises(page, queryset, number):
    page.page_size = 48
    paginator = Paginator(queryset, page.page_size)
    try:
        selected = paginator.page(number)
    except EmptyPage:
        page.status, page.indexable, page.name = 404, False, 'Страница не найдена'
        return
    page.count, page.number, page.pages = paginator.count, number, paginator.num_pages
    page.modified = queryset.aggregate(value=Max('updated_at'))['value']
    rows = list(selected)
    fallback_images = {}
    for franchise_id, poster_url in (visible_anime().filter(franchise_id__in=[row.pk for row in rows])
                                     .exclude(poster_url='').order_by('franchise_id', 'franchise_order', 'pk')
                                     .values_list('franchise_id', 'poster_url')):
        fallback_images.setdefault(franchise_id, poster_url)
    page.items = [franchise_card(franchise, franchise._seo_parts_count, fallback_images.get(franchise.pk, ''))
                  for franchise in rows]
    page.indexable = page.count > 0


def refine_collection(queryset, query, user=None):
    if not query:
        return queryset
    search = clean_text(query.get('search', ''))[:200]
    for word in search.split():
        queryset = queryset.filter(Q(title_ru__icontains=word) | Q(title_en__icontains=word) | Q(slug__icontains=word))
    for parameter, field in [('type', 'kind'), ('status', 'status')]:
        values = [value for value in query.get(parameter, '').split(',') if value]
        if values:
            if parameter == 'type' and any(is_hidden_value('kind', value) for value in values):
                return queryset.none()
            if parameter == 'status' and 'finished' in values and 'released' not in values:
                values.append('released')
            queryset = queryset.filter(**{field + '__in': values})
    genres = [value for value in query.get('genres', '').split(',') if value]
    if genres:
        if any(is_hidden_value('genre', value) for value in genres):
            return queryset.none()
        conditions = [Q(genres__contains=[value]) for value in genres]
        selected = conditions[0]
        for condition in conditions[1:]:
            selected = selected & condition if query.get('genre_logic') == 'AND' else selected | condition
        queryset = queryset.filter(selected)
    for parameter, field in [('year', 'year'), ('score', 'score'), ('episodes', 'episodes')]:
        for suffix, lookup in [('from', 'gte'), ('to', 'lte')]:
            value = query.get(f'{parameter}_{suffix}')
            if value:
                try:
                    number = float(value)
                    if math.isfinite(number):
                        queryset = queryset.filter(**{f'{field}__{lookup}': number})
                except (ValueError, TypeError):
                    pass
    if query.get('show_only_franchises') == 'true':
        queryset = queryset.filter(franchise__isnull=False)
    excluded = [value for value in query.get('excluded_library_statuses', '').split(',') if value]
    if excluded and user and user.is_authenticated:
        from apps.users.infrastructure.models.users import UserLibrary
        condition = Q(user=user, status__in=excluded)
        if 'favorite' in excluded:
            condition |= Q(user=user, is_favorite=True)
        queryset = queryset.exclude(pk__in=UserLibrary.objects.filter(condition).values('anime_id'))
    ordering = query.get('ordering', '-score')
    if ordering not in {'score', '-score', 'year', '-year', 'title_ru', '-title_ru', 'episodes', '-episodes'}:
        ordering = '-score'
    if query.get('shuffle') == 'true':
        from django.db.models import CharField, Value
        from django.db.models.functions import Cast, Concat, MD5
        seed = query.get('shuffle_seed', 'collection')[:100]
        return queryset.annotate(_shuffle=MD5(Concat(Cast('pk', CharField()), Value(seed)))).order_by('_shuffle', 'pk')
    return queryset.order_by(ordering, 'pk')


def paginate(page, queryset, number, query=None, user=None, minimum=MIN_TITLES):
    if query is not None:
        queryset = refine_collection(queryset, query, user)
        try:
            page.page_size = max(1, min(int(query.get('page_size', PAGE_SIZE)), 100))
        except (ValueError, TypeError):
            page.page_size = PAGE_SIZE
    paginator = Paginator(queryset, page.page_size)
    try:
        selected = paginator.page(number)
    except EmptyPage:
        page.status, page.indexable, page.name = 404, False, 'Страница не найдена'
        return
    page.count, page.number, page.pages = paginator.count, number, paginator.num_pages
    modified = queryset.aggregate(value=Max('updated_at'))['value']
    page.modified = max(filter(None, [page.modified, modified]), default=None)
    page.items = [card(anime) for anime in selected]
    page.indexable = page.count >= minimum


def public_posts():
    return readable_posts(Post.objects.all(), AnonymousUser()).filter(author__is_active=True)


def indexable_profiles():
    return (get_user_model().objects.filter(is_active=True)
            .annotate(_seo_bio_length=Length('bio'))
            .filter(_seo_bio_length__gte=MIN_PROFILE_BIO_LENGTH))


def indexable_posts():
    return (public_posts().annotate(_seo_text_length=Length('text'))
            .filter(_seo_text_length__gte=MIN_POST_TEXT_LENGTH))


def indexable_playlists():
    return (Playlist.objects.filter(visibility='public', user__is_active=True)
            .annotate(_seo_description_length=Length('description'),
                      _seo_item_count=Count('items', filter=Q(items__anime__in=visible_anime()), distinct=True))
            .filter(_seo_description_length__gte=MIN_PLAYLIST_DESCRIPTION_LENGTH,
                    _seo_item_count__gte=MIN_PLAYLIST_ITEMS))


def error_page(path, status=404):
    return Page(path, name='Страница не найдена' if status == 404 else 'Войдите в аккаунт', status=status)


def resolve(path, number=1, query=None, user=None):
    page = Page(path)
    qs = visible_anime().select_related('franchise').order_by('-score', 'pk')
    if path == '/':
        page.kind, page.name, page.indexable = 'home', 'Аниме онлайн: новинки, каталог и франшизы', True
        page.text = ('Находите аниме для просмотра по жанру, году и формату. В каталоге собраны новые серии, '
                     'полнометражные фильмы и франшизы с частями в правильном порядке.')
        page.items = [card(a) for a in qs[:12]]
        page.modified = qs.aggregate(value=Max('updated_at'))['value']
    elif path == '/anime/browse':
        page.kind, page.name, page.indexable = 'collection', 'Подборки аниме', True
        year_counts, genre_counts, season_counts = Counter(), Counter(), Counter()
        kinds, statuses = set(), set()
        for year, release_date, kind, status, genres in qs.order_by().values_list(
            'year', 'release_date', 'kind', 'status', 'genres'
        ).iterator(chunk_size=2000):
            if year:
                year_counts[year] += 1
                if release_date:
                    season = next((key for key, (_, months) in SEASONS.items() if release_date.month in months), None)
                    if season:
                        season_counts[(year, season)] += 1
            if kind:
                kinds.add(kind)
            if status:
                statuses.add(status)
            if isinstance(genres, list):
                genre_counts.update({clean_text(name) for name in genres if clean_text(name)})
        years = sorted(year_counts, reverse=True)
        blocked_genres = hidden_values('genre')
        blocked_kinds = hidden_values('kind')
        page.related += [
            {'path': f'/anime/year/{year}', 'name': f'{year} год'}
            for year in years
        ]
        genre_slugs = {row['name']: row['slug'] for row in genre_catalog(qs)}
        page.related += [
            {
                'path': f'/anime/genre/{genre_slugs[name]}',
                'name': name,
            }
            for name in sorted(genre_counts)
            if name.casefold() not in blocked_genres and name in genre_slugs
        ]
        page.related += [
            {'path': f'/anime/season/{year}/{season}', 'name': f'{label} {year}'}
            for year in years
            for season, (label, _) in SEASONS.items()
            if season_counts[(year, season)]
        ]
        page.related += [
            {'path': f'/anime/type/{key}', 'name': KIND_LABELS.get(key, label)}
            for key, label in KINDS.items()
            if key in kinds and key != 'franchise' and key.casefold() not in blocked_kinds
        ]
        page.related += [
            {'path': f'/anime/status/{key}', 'name': STATUS_LABELS.get(key, label)}
            for key, label in STATUSES.items() if key in statuses and key != 'released'
        ]
        if 'released' in statuses and 'finished' not in statuses:
            page.related.append({'path': '/anime/status/finished', 'name': STATUS_LABELS['finished']})
        page.related.append({'path': '/anime/franchises', 'name': 'Франшизы и порядок просмотра'})
        for collection in SeoCollection.objects.filter(enabled=True).order_by('name'):
            try:
                if qs.filter(filter_query(collection.filters)).exists():
                    page.related.append({'path': f'/anime/collection/{collection.slug}', 'name': collection.name})
            except ValidationError:
                continue
        page.count = len(page.related)
        page.page_size = max(page.count, 1)
        page.modified = max(filter(None, [
            qs.aggregate(value=Max('updated_at'))['value'],
            SeoCollection.objects.filter(enabled=True).aggregate(value=Max('updated_at'))['value'],
        ]), default=None)
        page.text = ('Выберите готовый раздел каталога: аниме по жанрам, годам, сезонам, форматам и статусам. '
                     'Каждая ссылка ведёт на отдельную подборку без случайных сочетаний фильтров.')
    elif path == '/anime/franchises':
        franchises = (Franchise.objects.filter(entries__in=qs)
                       .annotate(_seo_parts_count=Count('entries', filter=Q(entries__in=qs), distinct=True))
                       .filter(_seo_parts_count__gte=MIN_FRANCHISE_PARTS)
                       .order_by('name', 'pk'))
        page.kind, page.name = 'franchise_directory', 'Франшизы аниме'
        paginate_franchises(page, franchises, number)
        page.text = (f'В каталоге {count_phrase(page.count, "франшиза", "франшизы", "франшиз")} из двух и более частей. '
                     'Откройте нужную серию, чтобы посмотреть порядок частей, годы выхода и доступные эпизоды.')
    elif path == '/anime':
        page.kind, page.name = 'catalog', 'Каталог аниме'
        paginate(page, qs.exclude(status='announced'), number)
        page.text = (f'В каталоге {count_phrase(page.count, "аниме", "аниме", "аниме")}: сериалы, фильмы, OVA, ONA и спецвыпуски. '
                     'Используйте поиск и фильтры, чтобы подобрать историю по жанру, году, статусу или числу серий.')
    elif path == '/anime/status/released':
        page.redirect = '/anime/status/finished'
    elif match := re.fullmatch(r'/anime/(year|genre|type|status)/([^/]+)', path):
        facet, value = match.groups()
        filters = {'type': 'kind'}.get(facet, facet)
        if facet == 'year':
            if not value.isdigit():
                return error_page(path)
            value = int(value)
            page.name = f'Аниме {value} года'
        elif facet == 'genre':
            genre = genre_name(value, qs)
            if not genre:
                return error_page(path)
            page.name = f'Аниме жанра «{genre}»'
        else:
            label = (KIND_LABELS if facet == 'type' else STATUS_LABELS).get(value)
            if not label:
                return error_page(path)
            page.name = (TYPE_PAGE_NAMES.get(value, f'Аниме формата {label}') if facet == 'type'
                         else STATUS_PAGE_NAMES.get(value, f'Аниме: {label}'))
        page.kind = 'collection'
        try:
            selected = qs.filter(filter_query({filters: value}))
        except ValidationError:
            return error_page(path)
        if not selected.exists():
            return error_page(path)
        paginate(page, selected, number, query, user)
        if facet == 'year':
            page.text = (f'Собрали {count_phrase(page.count, "аниме", "аниме", "аниме")} {value} года: сериалы, фильмы и короткие форматы. '
                         'Список можно уточнить по жанру, рейтингу, статусу и числу серий.')
        elif facet == 'genre':
            page.text = (f'В подборке {count_phrase(page.count, "аниме", "аниме", "аниме")} жанра «{genre}». '
                         'Сравнивайте годы, форматы и оценки, а затем открывайте страницу тайтла или всей франшизы.')
        elif facet == 'type':
            page.text = (f'{KIND_LABELS[value]}: {count_phrase(page.count, "тайтл", "тайтла", "тайтлов")} в открытом каталоге. '
                         'Отфильтруйте список по году, жанру, статусу или рейтингу.')
        else:
            page.text = (f'{STATUS_LABELS[value]}: {count_phrase(page.count, "тайтл", "тайтла", "тайтлов")}. '
                         'В карточках указаны год, формат и рейтинг; у сериалов доступны страницы просмотра.')
    elif match := re.fullmatch(r'/anime/season/(\d{4})/(winter|spring|summer|autumn)', path):
        year, season = match.groups()
        page.kind, page.name = 'collection', f'{SEASONS[season][0]} {year}: аниме сезона'
        selected = qs.filter(filter_query({'year': int(year), 'season': season}))
        if not selected.exists():
            return error_page(path)
        paginate(page, selected, number, query, user)
        page.text = (f'{SEASONS[season][0]} {year}: {count_phrase(page.count, "аниме", "аниме", "аниме")} с премьерой в этом сезоне. '
                     'В подборке можно сравнить форматы, жанры, рейтинги и число серий.')
    elif match := re.fullmatch(r'/anime/collection/([\w-]+)', path):
        collection = SeoCollection.objects.filter(slug=match[1], enabled=True).first()
        if not collection:
            return error_page(path)
        try:
            selected = qs.filter(filter_query(collection.filters))
        except ValidationError:
            return error_page(path)
        page.kind, page.name, page.modified = 'collection', collection.name, collection.updated_at
        paginate(page, selected, number, query, user)
        page.text = (f'В подборку «{page.name}» вошли {count_phrase(page.count, "тайтл", "тайтла", "тайтлов")}. '
                     'Список обновляется вместе с каталогом и учитывает только доступные аниме.')
    elif match := re.fullmatch(r'/(?:anime/)?franchise/([^/]+)', path):
        token = match[1]
        franchise = Franchise.objects.filter(**({'pk': token} if token.isdigit() else {'slug': token})).order_by('pk').first()
        if not franchise:
            return error_page(path)
        selected = qs.filter(franchise=franchise).order_by('franchise_order', 'pk')
        if not selected.exists():
            return error_page(path)
        if selected.count() == 1:
            page.redirect = anime_path(selected.first())
            return page
        page.path = franchise_path(franchise)
        page.kind, page.name = 'franchise', franchise.name
        paginate(page, selected, number, minimum=MIN_FRANCHISE_PARTS)
        years = [value for value in selected.values_list('year', flat=True) if value]
        span = (f' с {min(years)} по {max(years)} год' if years and min(years) != max(years)
                else f' {years[0]} года' if years else '')
        formats = ', '.join(dict.fromkeys(KIND_LABELS.get(value, value) for value in selected.values_list('kind', flat=True)))
        page.text = (f'Франшиза «{franchise.name}» объединяет {part_phrase(page.count)}{span}. '
                     f'Ниже части расположены по порядку; в подборке есть {formats.lower() if formats else "разные форматы"}.')
        page.modified = selected.order_by('-updated_at').values_list('updated_at', flat=True).first()
    elif path in {'/anime/ongoings', '/anime/announcements', '/anime/calendar', '/anime/watching'}:
        page.redirect = '/anime?section=' + {'/anime/ongoings': 'ongoings', '/anime/announcements': 'announcements', '/anime/calendar': 'calendar', '/anime/watching': 'currently_watching'}[path]
    elif match := re.fullmatch(r'/anime/([^/]+)(/watch)?', path):
        token, watch = match.groups()
        canonical_id = re.fullmatch(r'(\d+)-.+', token)
        exact_id = Anime.objects.filter(slug=token).values_list('pk', flat=True).first() if not token.isdigit() else None
        if exact_id is not None:
            anime = qs.filter(pk=exact_id).first()
        else:
            anime = qs.filter(pk=canonical_id[1] if canonical_id else token).first() if canonical_id or token.isdigit() else None
        if not anime:
            return error_page(path)
        page.path, page.kind, page.name = anime_path(anime), 'anime', anime.title_ru or anime.title_en
        page.indexable, page.modified, page.image = True, anime.updated_at, anime.poster_image_url
        description = clean_text(anime.description)
        franchise = anime.franchise if anime.franchise and qs.filter(franchise=anime.franchise).count() >= MIN_FRANCHISE_PARTS else None
        if franchise:
            context = f'Тайтл входит во франшизу «{franchise.name}»; на странице франшизы части собраны по порядку.'
        else:
            context = 'Это самостоятельный тайтл, не привязанный к франшизе в каталоге.'
        page.text = f'{description} {context}'.strip() if description else f'«{page.name}»: основные сведения, серии и варианты просмотра. {context}'
        page.facts = [str(v) for v in [anime.year, KIND_LABELS.get(anime.kind), STATUS_LABELS.get(anime.status),
                      episode_phrase(anime.episodes) if anime.episodes else None] if v]
        if anime.year:
            page.related.append({'path': f'/anime/year/{anime.year}', 'name': f'Аниме {anime.year} года'})
        genre_paths = {row['name']: row['slug'] for row in genre_catalog(qs)}
        for genre in anime.genres if isinstance(anime.genres, list) else []:
            if is_hidden_value('genre', genre) or genre not in genre_paths:
                continue
            page.related.append({'path': f'/anime/genre/{genre_paths[genre]}', 'name': genre})
        if not is_hidden_value('kind', anime.kind):
            page.related.append({'path': f'/anime/type/{anime.kind}', 'name': KIND_LABELS.get(anime.kind, anime.kind)})
        status_path = 'finished' if anime.status == 'released' else anime.status
        page.related.append({'path': f'/anime/status/{status_path}', 'name': STATUS_LABELS.get(status_path, status_path)})
        if franchise:
            page.related.append({'path': franchise_path(franchise), 'name': franchise.name})
        schema = {'@type': 'Movie' if anime.kind == 'movie' else 'TVSeries', 'name': page.name,
                  'description': page.text, 'genre': anime.genres}
        if anime.release_date:
            schema['datePublished'] = anime.release_date.isoformat()
        if anime.episodes and anime.kind != 'movie':
            schema['numberOfEpisodes'] = anime.episodes
        page.schema.append(schema)
        if watch:
            page.indexable = False
            page.path += '/watch'
            page.canonical = anime_path(anime)
            page.schema = []
    elif match := re.fullmatch(r'/(?:profile/)?@([^/]+)|/profile/(\d+)', path):
        nickname, pk = match.groups()
        users = get_user_model().objects.filter(is_active=True)
        user = users.filter(pk=pk).first() if pk else users.filter(nickname=nickname).first()
        if not user:
            return error_page(path)
        page.path, page.kind, page.name = profile_path(user), 'profile', user.display_name or user.nickname or user.username
        page.text = clean_text(user.bio) or f'Публичный профиль {page.name}.'
        page.indexable = len(clean_text(user.bio)) >= MIN_PROFILE_BIO_LENGTH
        
        page.related = [{'path': f'/post/{p.public_id}', 'name': p.title or clean_text(p.text, 70) or 'Пост'} for p in public_posts().filter(author=user).order_by('-created_at')[:10]]
        page.related += [{'path': f'/playlist/{p.pk}', 'name': p.title} for p in Playlist.objects.filter(user=user, visibility='public')[:10]]
    elif match := re.fullmatch(r'/post/(\d+)', path):
        token = match[1]
        post = public_posts().filter(pk=token).select_related('author').first()
        if not post:
            post = public_posts().filter(public_id=token).select_related('author').first()
        if not post:
            return error_page(path)
        page.path, page.kind, page.name = f'/post/{post.public_id}', 'post', post.title or clean_text(post.text, 80) or 'Публичный пост'
        page.text, page.modified = clean_text(post.text), post.edited_at or post.published_at or post.created_at
        page.indexable = len(page.text) >= MIN_POST_TEXT_LENGTH
        page.related = [{'path': profile_path(post.author), 'name': post.author.display_name or post.author.nickname or post.author.username}]
        page.schema.append({'@type': 'Article', 'headline': page.name, 'articleBody': page.text,
                            'datePublished': (post.published_at or post.created_at).isoformat(),
                            'dateModified': page.modified.isoformat(),
                            'author': {'@type': 'Person', 'name': page.related[0]['name'], 'url': page.related[0]['path']}})
    elif match := re.fullmatch(r'/playlist/(\d{8})', path):
        playlist = Playlist.objects.filter(pk=match[1], visibility='public', user__is_active=True).select_related('user').first()
        if not playlist:
            return error_page(path)
        page.kind, page.name = 'playlist', playlist.title
        page.modified, page.text = playlist.updated_at, clean_text(playlist.description)
        selected = qs.filter(playlistitem__playlist=playlist).order_by('playlistitem__position', 'pk')
        paginate(page, selected, number)
        page.indexable = (page.status == 200 and page.count >= MIN_PLAYLIST_ITEMS and
                          len(page.text) >= MIN_PLAYLIST_DESCRIPTION_LENGTH)
        page.related = [{'path': profile_path(playlist.user), 'name': 'Автор плейлиста'}]
    elif path == '/subscription':
        page.redirect = '/donate'
    elif path in {'/public-playlists', '/my-playlists'}:
        page.path = '/playlists'
        page.redirect = '/playlists?tab=public' if path == '/public-playlists' else '/playlists'
    elif match := re.fullmatch(r'/people/([^/]+)', path):
        if not feature_flags.FEATURE_DUBS_ENABLED:
            return error_page(path)
        from apps.dubs.infrastructure.models.dubs import Person
        try:
            person = Person.objects.filter(pk=match[1]).first()
        except (ValueError, TypeError, ValidationError):
            person = None
        person = person or Person.objects.filter(slug=match[1]).first()
        if not person:
            return error_page(path)
        page.name, page.text, page.modified = person.name, clean_text(person.description), person.updated_at
        page.path = f'/people/{person.pk}'
        page.related = [{'path': anime_path(a), 'name': a.title_ru} for a in qs.filter(related_people=person)[:12]]
    elif match := re.fullmatch(r'/announcements/([^/]+)', path):
        from apps.anime.infrastructure.models.anime import AnimeAnnouncement, CatalogHideRule
        token = match[1]
        announcement = AnimeAnnouncement.objects.filter(**({'pk': token} if token.isdigit() else {'slug': token})).order_by('pk').first()
        if not announcement:
            return error_page(path)
        if announcement.shikimori_id and Anime.objects.filter(shikimori_id=announcement.shikimori_id).exclude(pk__in=visible_anime().values('pk')).exists():
            return error_page(path)
        for rule in CatalogHideRule.objects.all():
            blocked = (rule.rule_type == 'title' and rule.value.casefold() in (announcement.title_ru or announcement.title_en or '').casefold())
            blocked |= rule.rule_type == 'genre' and rule.value in (announcement.genres or [])
            blocked |= rule.rule_type == 'kind' and rule.value.casefold() == (announcement.type or '').casefold()
            blocked |= rule.rule_type == 'studio' and rule.value.casefold() in (announcement.studio or '').casefold()
            if blocked:
                return error_page(path)
        unique_slug = announcement.slug and not AnimeAnnouncement.objects.filter(slug=announcement.slug).exclude(pk=announcement.pk).exists()
        page.path = f'/announcements/{announcement.slug if unique_slug else announcement.pk}'
        page.name = announcement.title_ru or announcement.title_en or 'Анонс аниме'
        page.text, page.image, page.modified = clean_text(announcement.description), announcement.poster_url or '', announcement.created_at
    elif path == '/contacts':
        page.kind, page.name, page.indexable = 'information', 'Контакты', True
        page.text = 'По вопросам работы сайта, сотрудничества и прав на материалы напишите администрации: ' + site_navigation()['email']
    elif path == '/ideas':
        page.kind, page.name, page.indexable = 'information', 'Идеи и предложения', True
        page.text = ('Открытая доска развития AniLux: предлагайте новые функции, сообщайте об ошибках '
                     'и следите за тем, как записи переходят от рассмотрения к выпуску.')
    elif document := next((item for item in site_navigation()['documents'] if item['path'] == path), None):
        page.kind, page.name, page.text = 'information', document['name'], document['text']
        page.indexable = document.get('published', False)
    elif path in {'/login', '/register', '/confirm-email', '/reset-password', '/oauth/callback',
                  '/app', '/donate', '/add-anime', '/people', '/profile', '/feed', '/news', '/roulette',
                  '/chats', '/chats/groups', '/chats/create-group', '/playlists', '/playlists/create',
                  '/my-playlists', '/public-playlists', '/library', '/history', '/stats', '/notifications',
                  '/notifications/settings', '/settings', '/achievements', '/excerpts'}:
        page.name = {
            '/login': 'Вход', '/register': 'Регистрация', '/app': 'Приложение AniLux',
            '/confirm-email': 'Подтверждение почты', '/reset-password': 'Восстановление пароля',
            '/oauth/callback': 'Вход через внешний сервис',
            '/donate': 'Поддержать проект', '/add-anime': 'Добавить аниме', '/people': 'Люди',
            '/profile': 'Мой профиль', '/feed': 'Лента сообщества', '/news': 'Новости',
            '/chats': 'Чаты', '/chats/groups': 'Группы', '/chats/create-group': 'Создать группу',
            '/playlists': 'Плейлисты аниме', '/playlists/create': 'Создать плейлист',
            '/my-playlists': 'Мои плейлисты', '/public-playlists': 'Публичные плейлисты аниме',
            '/library': 'Моя библиотека аниме', '/history': 'История просмотров', '/stats': 'Статистика просмотров',
            '/notifications': 'Уведомления', '/notifications/settings': 'Настройки уведомлений',
            '/settings': 'Настройки', '/support': 'Помощь и поддержка',
            '/achievements': 'Достижения', '/excerpts': 'Отрывки аниме', '/roulette': 'Рулетка аниме',
        }[path]
        page.text = {
            '/app': 'Приложение AniLux для Android, Windows и Linux. Каталог аниме, библиотека и общение на телефоне и компьютере.',
            '/donate': 'Поддержите развитие AniLux и помогите проекту работать и становиться лучше.',
            '/public-playlists': 'Публичные плейлисты аниме от сообщества AniLux. Выбирайте подборки по темам и находите новые истории.',
            '/people': 'Актёры озвучивания, сейю и участники создания аниме. Биографии и связанные тайтлы.',
            '/roulette': 'Колесо выбора аниме с настраиваемыми шансами, пресетами и исключением просмотренных тайтлов.',
        }.get(path, f'{page.name} в AniLux. Войдите в аккаунт, чтобы пользоваться возможностями раздела.')
        if path == '/playlists' and query and query.get('tab') in {'public', 'my', 'favorites'}:
            page.name = {'public': 'Публичные плейлисты аниме', 'my': 'Мои плейлисты', 'favorites': 'Избранные плейлисты'}[query['tab']]
            page.text = ('Публичные плейлисты аниме от сообщества AniLux. Выбирайте подборки по темам и находите новые истории.'
                         if query['tab'] == 'public' else f'{page.name} в AniLux. Сохраняйте аниме и управляйте своими подборками.')
    elif re.fullmatch(r'/(?:profile|admin(?:/[^?]*)?|moderation|feed|news|chats(?:/[^?]*)?|playlists(?:/[^?]*)?|my-playlists|public-playlists|library|history|stats|notifications(?:/[^?]*)?|settings|achievements|excerpts(?:/[^?]*)?|playlist/shared/[^/]+)', path):
        page.name = ('Управление сайтом' if path.startswith('/admin') or path == '/moderation' else
                     'Чат' if path.startswith('/chats/') else
                     'Отрывок аниме' if path.startswith('/excerpts/') else
                     'Редактировать плейлист' if path.startswith('/playlists/') else 'Войдите в аккаунт')
        
    else:
        alias = SeoAlias.objects.filter(path=path).first()
        if alias:
            if alias.kind == 'anime':
                obj = qs.filter(pk=alias.object_id).first()
                page.redirect = anime_path(obj) if obj else ''
            elif alias.kind == 'franchise':
                obj = Franchise.objects.filter(pk=alias.object_id, entries__in=qs).first()
                page.redirect = franchise_path(obj) if obj else ''
            if page.redirect:
                return page
        return error_page(path)
    if page.path != path and not page.canonical and not page.redirect:
        page.redirect = page.path
    return page


def build_page(request, path, query):
    site, origin, enabled, config = site_config(request)
    raw_page = query.get('page', '1')
    if not re.fullmatch(r'[1-9][0-9]{0,6}', raw_page) or len(query.getlist('page')) > 1:
        page = error_page(path)
    else:
        page = resolve(path, int(raw_page), query, getattr(request, "user", None))
    if (page.number == 1 and raw_page != '1' and not page.redirect and
            page.kind not in {'catalog', 'collection', 'franchise_directory', 'franchise', 'playlist'}):
        page = error_page(path)
    if page.status == 404:
        alias = SeoAlias.objects.filter(path=path).first()
        if alias:
            obj = (visible_anime() if alias.kind == 'anime' else Franchise.objects.filter(entries__in=visible_anime())).filter(pk=alias.object_id).first()
            if obj:
                page.redirect = anime_path(obj) if alias.kind == 'anime' else franchise_path(obj)
    page.site = site
    override = SeoOverride.objects.filter(path=page.path).first() if page.status == 200 and page.kind != 'utility' else None
    if override and override.text and page.kind in {'home', 'catalog', 'collection', 'franchise'}:
        page.text = clean_text(override.text)
    page.modified = max(filter(None, [page.modified, override.updated_at if override else None, config.updated_at if config else None]), default=None)
    page.h1 = page.name
    page.title = page.name if page.name.casefold() == site.casefold() else f'{page.name} | {site}'
    page.description = clean_text(page.text or f'{page.name} — раздел сайта {site}.', 180)
    if page.kind == 'home':
        page.title = f'Аниме онлайн: каталог, новинки и франшизы | {site}'
    elif page.kind == 'catalog':
        page.title = site if page.name.casefold() == site.casefold() else f'Каталог аниме — смотреть онлайн | {site}'
    elif page.kind == 'collection':
        page.title = (f'Подборки аниме по жанрам, годам и сезонам | {site}'
                      if page.path == '/anime/browse' else f'{page.name} — список аниме | {site}')
    elif page.kind == 'franchise_directory':
        page.title = f'Франшизы аниме: все части и порядок просмотра | {site}'
    elif page.kind == 'franchise':
        page.title = f'{page.name}: порядок просмотра и все части | {site}'
    if page.kind == 'anime':
        announced = STATUS_LABELS['announced'] in page.facts
        kind = next((key for key, label in KIND_LABELS.items() if label in page.facts), '')
        intent = 'дата выхода и описание' if announced else ('смотреть аниме-фильм онлайн' if kind == 'movie' else 'смотреть аниме онлайн')
        page.title = f'{page.name} — {intent} | {site}'
        lead = f'Дата выхода и описание аниме «{page.name}».' if announced else f'«{page.name}» — смотреть онлайн.'
        facts = ', '.join(page.facts)
        page.description = clean_text(f'{lead} {facts + ". " if facts else ""}{page.text}', 180)
    context = {'name': page.name, 'site': site, 'count': page.count,
               'summary': clean_text(page.text, 180), 'page': page.number}
    templates = (config.templates if config else {}).get(page.kind, {})
    for key in ('title', 'description', 'h1'):
        value = templates.get(key)
        if value:
            try:
                validate_templates({page.kind: {key: value}})
                setattr(page, key, clean_text(value.format_map(context)))
            except (ValidationError, ValueError, KeyError):
                pass
        if override and getattr(override, key):
            setattr(page, key, clean_text(getattr(override, key)))
    page.title = clean_text(page.title, 250)
    page.description = clean_text(page.description, 320)
    page.h1 = clean_text(page.h1, 250)
    if page.number > 1:
        page.title += f' — страница {page.number}'
        page.h1 += f' — страница {page.number}'
        page.description += f' Страница {page.number} из {page.pages}.'
    extras = {key for key in query if key != 'page' and not key.startswith('utm_') and key not in {'gclid', 'yclid'}}
    canonical_path = page.canonical or page.path
    page.canonical = origin + canonical_path + (f'?page={page.number}' if page.number > 1 and not extras else '')
    if page.redirect and 'page' in query and page.number > 1 and '?' not in page.redirect:
        page.redirect += f'?page={page.number}'
    def page_url(number):
        parameters = query.copy()
        allowed = {'page', 'directory_page', 'search', 'genres', 'genre_logic', 'type', 'status', 'year_from', 'year_to',
                   'score_from', 'score_to', 'episodes_from', 'episodes_to', 'page_size', 'ordering', 'shuffle',
                   'shuffle_seed', 'show_only_franchises', 'excluded_library_statuses'}
        for key in list(parameters):
            if key not in allowed:
                parameters.pop(key, None)
        parameters.pop('page', None)
        if number > 1:
            parameters['page'] = str(number)
        encoded = parameters.urlencode()
        return page.path + ('?' + encoded if encoded else '')
    if page.kind in {'catalog', 'collection', 'franchise_directory', 'franchise', 'playlist'}:
        page.first_url = page_url(1)
        page.previous_url = page_url(page.number - 1) if page.number > 1 else ''
        page.next_url = page_url(page.number + 1) if page.number < page.pages else ''
    
    
    extras = {key for key in query if key != 'page' and not key.startswith('utm_') and key not in {'gclid', 'yclid'}}
    page.indexable = bool(page.indexable and enabled and not extras and not (override and override.noindex) and page.status == 200)
    page.robots = 'index,follow' if page.indexable else 'noindex,follow'
    if page.status != 200:
        page.schema, page.items, page.related, page.image, page.text, page.canonical = [], [], [], '', '', ''
    if page.kind == 'utility' and re.search(r'/(?:shared|invite|s)/', path):
        page.path = '/login'
        page.first_url = page.previous_url = page.next_url = ''
        page.canonical = origin + '/login'
    page.crumbs = [{'path': '/', 'name': 'Главная'}]
    if path != '/':
        if page.kind in {'anime', 'collection', 'catalog', 'franchise_directory', 'franchise'}:
            page.crumbs.append({'path': '/anime', 'name': 'Каталог аниме'})
        if page.path != '/anime':
            page.crumbs.append({'path': page.path, 'name': page.h1})
    if page.kind in {'home', 'catalog'}:
        page.related += discovery_links(qs=visible_anime())
    elif page.kind in {'collection', 'franchise_directory', 'franchise'} and page.path != '/anime/browse':
        page.related += [{'path': '/anime', 'name': 'Каталог аниме'}, {'path': '/anime/browse', 'name': 'Все подборки'},
                         {'path': '/anime/franchises', 'name': 'Франшизы аниме'}]
        for year in sorted({item['year'] for item in page.items if item.get('year')}, reverse=True)[:8]:
            page.related.append({'path': f'/anime/year/{year}', 'name': f'Аниме {year} года'})
        seasons = sorted({(item['year'], item['season']) for item in page.items if item.get('year') and item.get('season')})
        page.related += [{'path': f'/anime/season/{year}/{season}', 'name': f'{SEASONS[season][0]} {year}'} for year, season in seasons[:8]]
    page.image = absolute_url(origin, page.image)
    if page.status == 200 and page.kind != 'utility':
        if page.items and page.kind not in {'home', 'catalog'}:
            page.schema.append({'@type': 'CollectionPage', 'name': page.h1, 'description': page.description,
                'mainEntity': {'@type': 'ItemList', 'numberOfItems': len(page.items),
                    'itemListElement': [{'@type': 'ListItem', 'position': (page.number - 1) * page.page_size + i,
                                         'name': item['name'], 'url': origin + item['path']} for i, item in enumerate(page.items, 1)]}})
        if page.kind == 'home':
            organization_id = origin + '/#organization'
            page.schema.extend([
                {'@type': 'WebSite', '@id': origin + '/#website', 'name': site,
                 'url': origin + '/', 'inLanguage': 'ru-RU',
                 'publisher': {'@id': organization_id}},
                {'@type': 'Organization', '@id': organization_id, 'name': site,
                 'url': origin + '/',
                 'logo': {'@type': 'ImageObject', 'url': origin + '/pwa/icon-512.png',
                          'width': 512, 'height': 512}},
            ])
        if page.kind == 'catalog':
            page.schema.append({'@type': 'CollectionPage', 'name': page.h1, 'description': page.description})
        if page.kind == 'information':
            page.schema.append({'@type': 'ContactPage' if page.path == '/contacts' else 'WebPage',
                                'name': page.h1, 'description': page.description})
        page.schema.append({'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': crumb['name'], 'item': origin + crumb['path']}
            for i, crumb in enumerate(page.crumbs, 1)]})
        for i, schema in enumerate(page.schema):
            schema['@context'] = 'https://schema.org'
            schema.setdefault('@id', page.canonical + f'#schema-{i}')
            schema.setdefault('url', page.canonical)
            if page.image and schema['@type'] in {'Movie', 'TVSeries', 'Article'}:
                schema['image'] = page.image
            if schema.get('author'):
                schema['author']['url'] = origin + schema['author']['url']
    return page


def absolute_url(origin, url):
    if not url:
        return ''
    parsed = urlsplit(str(url))
    if parsed.scheme in ('https', 'http') and parsed.netloc:
        return str(url)
    return origin + str(url) if str(url).startswith('/') and not str(url).startswith('//') else ''


def discovery_links(qs):
    from django.core.cache import cache
    try:
        revision = cache.get('catalog:revision', 0)
    except Exception:
        revision = 0
    cache_key = f'seo:discovery-links:v1:{revision}'
    cached = safe_cache_get(cache_key)
    if cached is not None:
        return cached
    years = qs.exclude(year=None).order_by('-year').values_list('year', flat=True).distinct()[:8]
    links = [{'path': '/anime/browse', 'name': 'Все подборки'},
             {'path': '/anime/franchises', 'name': 'Франшизы и порядок просмотра'}]
    links += [{'path': '/anime?section=catalog', 'name': 'Фильтры и перемешивание каталога'}]
    links += [{'path': f'/anime/year/{year}', 'name': f'Аниме {year} года'} for year in years]
    links += [{'path': f"/anime/genre/{row['slug']}", 'name': row['name']} for row in genre_catalog(qs)[:12]]
    kinds = set(qs.order_by().values_list('kind', flat=True).distinct())
    statuses = set(qs.order_by().values_list('status', flat=True).distinct())
    links += [{'path': f'/anime/type/{key}', 'name': KIND_LABELS.get(key, label)}
              for key, label in KINDS.items() if key in kinds and key != 'franchise']
    links += [{'path': f'/anime/status/{key}', 'name': STATUS_LABELS.get(key, label)}
              for key, label in STATUSES.items() if key in statuses and key != 'released']
    if 'released' in statuses and 'finished' not in statuses:
        links.append({'path': '/anime/status/finished', 'name': STATUS_LABELS['finished']})
    links += [{'path': f'/anime/collection/{c.slug}', 'name': c.name} for c in SeoCollection.objects.filter(enabled=True)[:30]]
    safe_cache_set(cache_key, links, 300)
    return links
