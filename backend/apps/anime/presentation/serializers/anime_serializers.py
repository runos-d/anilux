from rest_framework import serializers
from django.conf import settings
from apps.anime.infrastructure.models.anime import (
    Anime,
    Franchise,
    Genre,
    Playlist,
    PlaylistItem,
    VoiceActor,
    DubStudio,
    Dub,
    DubRole,
    UserDubRating,
    VideoSource,
    Episode,
    Translation,
    WatchProgress,
    VideoQuality,
    AnimeUpdate,
    UserEpisodeProgress,
    UserActiveTab,
    CustomDub,
    ClipTask,
    AnimeSchedule,
    AnimeAnnouncement,
    CatalogSettings,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "slug"]


class AnimeSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    
    franchise_id = serializers.IntegerField(source='franchise.id', read_only=True)
    is_franchise = serializers.BooleanField(source='franchise.id', read_only=True)
    franchise_name = serializers.CharField(source='franchise.name', read_only=True)
    franchise_poster_image_url = serializers.SerializerMethodField()
    franchise_parts_count = serializers.IntegerField(source='franchise.entries.count', read_only=True)
    franchise_year_start = serializers.IntegerField(source='franchise.year_start', read_only=True)
    franchise_year_end = serializers.IntegerField(source='franchise.year_end', read_only=True)
    franchise_avg_score = serializers.FloatField(source='franchise.score', read_only=True)
    franchise_all_genres = serializers.JSONField(source='franchise.genres', read_only=True)
    franchise_all_posters = serializers.SerializerMethodField()
    franchise_total_duration = serializers.SerializerMethodField()

    def get_franchise_poster_image_url(self, obj):
        if obj.franchise:
            if obj.franchise.poster and hasattr(obj.franchise.poster, "url"):
                return obj.franchise.poster.url
            return obj.franchise.poster_url or None
        return None

    def get_franchise_all_posters(self, obj):
        if obj.franchise:
            return obj.franchise.all_posters
        return []

    def get_franchise_total_duration(self, obj):
        if not obj.franchise:
            return None
        total = 0
        for entry in obj.franchise.entries.all():
            if entry.total_duration:
                total += entry.total_duration
            elif entry.episodes and entry.episode_duration:
                total += entry.episodes * entry.episode_duration
        return total or None

    def get_genres(self, obj):
        genres_data = getattr(obj, "genres", []) or []
        if isinstance(genres_data, list):
            return [
                {"id": idx, "name": genre, "slug": genre.lower().replace(" ", "-")}
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data

    def get_studios(self, obj):
        studios_data = getattr(obj, "studios", []) or []
        if isinstance(studios_data, list):
            return [
                {"id": idx, "name": studio, "slug": studio.lower().replace(" ", "-")}
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        if hasattr(self, 'context') and self.context.get('request'):
            if obj.poster:
                try:
                    return obj.poster_thumbnail.url
                except Exception:
                    pass
        if obj.poster:
            try:
                return obj.poster_large.url
            except Exception:
                pass
        return obj.poster_url or ""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if int(data.get('franchise_parts_count') or 0) < 2:
            for key in ('franchise_id', 'franchise_name', 'franchise_poster_image_url',
                        'franchise_parts_count', 'franchise_year_start', 'franchise_year_end',
                        'franchise_avg_score', 'franchise_all_genres', 'franchise_all_posters',
                        'franchise_total_duration'):
                data[key] = None if key not in ('franchise_all_genres', 'franchise_all_posters') else []
            data['is_franchise'] = False
        return data

    class Meta:
        model = Anime
        fields = [
            "id", "slug", "title_ru", "title_en", "title_jp",
            "description", "year", "release_date", "release_date_string",
            "status", "kind", "episodes", "progress_total", "episode_duration", "total_duration", "score",
            "poster_url", "poster", "poster_image_url",
            "genres", "studios",
            "movies", "ovas", "movie_count", "ova_count", "total_items",
            "created_at", "updated_at",
            "shikimori_id", "data_source",
            "franchise_id", "is_franchise", "franchise_order",
            "franchise_name",
            "franchise_poster_image_url",
            "franchise_parts_count",
            "franchise_year_start",
            "franchise_year_end",
            "franchise_avg_score",
            "franchise_all_genres",
            "franchise_all_posters",
            "franchise_total_duration",
            "download_links",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AnimeListSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    
    franchise_id = serializers.IntegerField(source='franchise.id', read_only=True)
    is_franchise = serializers.BooleanField(source='franchise.id', read_only=True)
    franchise_name = serializers.CharField(source='franchise.name', read_only=True)
    franchise_slug = serializers.CharField(source='franchise.slug', read_only=True)
    franchise_poster_image_url = serializers.SerializerMethodField()
    franchise_parts_count = serializers.IntegerField(source='franchise.entries.count', read_only=True)
    franchise_year_start = serializers.IntegerField(source='franchise.year_start', read_only=True)
    franchise_year_end = serializers.IntegerField(source='franchise.year_end', read_only=True)
    franchise_avg_score = serializers.FloatField(source='franchise.score', read_only=True)
    franchise_all_genres = serializers.JSONField(source='franchise.genres', read_only=True)
    franchise_all_posters = serializers.SerializerMethodField()
    franchise_total_duration = serializers.SerializerMethodField()

    def get_franchise_poster_image_url(self, obj):
        if obj.franchise:
            if obj.franchise.poster and hasattr(obj.franchise.poster, "url"):
                return obj.franchise.poster.url
            return obj.franchise.poster_url or None
        return None

    def get_franchise_all_posters(self, obj):
        if obj.franchise:
            return obj.franchise.all_posters
        return []

    def get_franchise_total_duration(self, obj):
        if not obj.franchise:
            return None
        total = 0
        for entry in obj.franchise.entries.all():
            if entry.total_duration:
                total += entry.total_duration
            elif entry.episodes and entry.episode_duration:
                total += entry.episodes * entry.episode_duration
        return total or None

    def get_genres(self, obj):
        genres_data = getattr(obj, "genres", []) or []
        if isinstance(genres_data, list):
            return [
                {"id": idx, "name": genre, "slug": genre.lower().replace(" ", "-")}
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data

    def get_studios(self, obj):
        studios_data = getattr(obj, "studios", []) or []
        if isinstance(studios_data, list):
            return [
                {"id": idx, "name": studio, "slug": studio.lower().replace(" ", "-")}
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        if hasattr(self, 'context') and self.context.get('request'):
            if obj.poster:
                try:
                    return obj.poster_thumbnail.url
                except Exception:
                    pass
        if obj.poster:
            try:
                return obj.poster_large.url
            except Exception:
                pass
        return obj.poster_url or ""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['description'] = (data.get('description') or '')[:240]
        data['franchise_all_posters'] = (data.get('franchise_all_posters') or [])[:4]
        if int(data.get('franchise_parts_count') or 0) < 2:
            for key in ('franchise_id', 'franchise_name', 'franchise_slug',
                        'franchise_poster_image_url', 'franchise_parts_count',
                        'franchise_year_start', 'franchise_year_end', 'franchise_avg_score',
                        'franchise_total_duration'):
                data[key] = None
            data['franchise_all_genres'] = []
            data['franchise_all_posters'] = []
            data['is_franchise'] = False
        return data

    class Meta:
        model = Anime
        fields = [
            "id", "slug", "title_ru", "title_en", "title_jp",
            "description", "year", "status", "kind", "episodes", "progress_total", "episode_duration", "total_duration", "score",
            "poster_url", "poster_image_url",
            "genres", "studios", "is_available",
            "franchise_id", "is_franchise",
            "franchise_name", "franchise_slug",
            "franchise_poster_image_url",
            "franchise_parts_count",
            "franchise_year_start",
            "franchise_year_end",
            "franchise_avg_score",
            "franchise_all_genres",
            "franchise_all_posters",
            "franchise_total_duration",
        ]


class AnimeDetailSerializer(serializers.ModelSerializer):
    genres = serializers.SerializerMethodField()
    studios = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    franchise_id = serializers.SerializerMethodField()
    is_franchise = serializers.SerializerMethodField()

    def get_franchise_id(self, obj):
        try:
            return obj.franchise_id if obj.franchise_id and obj.franchise.entries.count() >= 2 else None
        except Exception:
            return None

    def get_is_franchise(self, obj):
        try:
            return bool(obj.franchise_id and obj.franchise.entries.count() >= 2)
        except Exception:
            return False

    kodik_link = serializers.CharField(
        read_only=True, allow_null=True, allow_blank=True
    )
    kodik_id = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    quality = serializers.CharField(read_only=True, allow_null=True, allow_blank=True)
    screenshots = serializers.SerializerMethodField()
    seasons = serializers.JSONField(read_only=True, allow_null=True)
    last_season = serializers.IntegerField(read_only=True, allow_null=True)
    last_episode = serializers.IntegerField(read_only=True, allow_null=True)
    seasons_count = serializers.SerializerMethodField()
    translations = serializers.JSONField(read_only=True, allow_null=True)

    def get_genres(self, obj):
        genres_data = getattr(obj, "genres", []) or []
        if isinstance(genres_data, list):
            return [
                {"id": idx, "name": genre, "slug": genre.lower().replace(" ", "-")}
                for idx, genre in enumerate(genres_data)
            ]
        return genres_data

    def get_studios(self, obj):
        studios_data = getattr(obj, "studios", []) or []
        if isinstance(studios_data, list):
            return [
                {"id": idx, "name": studio, "slug": studio.lower().replace(" ", "-")}
                for idx, studio in enumerate(studios_data)
            ]
        return studios_data

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            try:
                return obj.poster.url
            except Exception:
                pass
        return obj.poster_url or ""

    def get_seasons_count(self, obj):
        seasons_data = getattr(obj, "seasons", {}) or {}
        return len(seasons_data) if seasons_data else 1

    def get_translations(self, obj):
        translations_data = getattr(obj, "translations", []) or []
        return translations_data

    def get_screenshots(self, obj):
        from apps.anime.infrastructure.clients.kodik_config import KODIK_SCREENSHOTS_BASE, KODIK_OLD_DOMAINS

        screenshots = getattr(obj, "screenshots", []) or []
        if not screenshots:
            return []

        def normalize_screenshot_url(url: str) -> str:
            if not url:
                return url
            if KODIK_SCREENSHOTS_BASE in url:
                return url
            for old_domain in KODIK_OLD_DOMAINS:
                if old_domain in url:
                    path = url.split(old_domain)[-1]
                    return f"{KODIK_SCREENSHOTS_BASE}{path}"
            return url

        if isinstance(screenshots, list) and screenshots:
            first = screenshots[0]
            if isinstance(first, str):
                return [{"url": normalize_screenshot_url(url)} for url in screenshots]
            elif isinstance(first, dict):
                return [
                    {"url": normalize_screenshot_url(s.get("url", ""))}
                    for s in screenshots
                ]
        return []
    
    class Meta:
        model = Anime
        fields = [
            "id",
            "slug",
            "title_ru",
            "title_en",
            "title_jp",
            "description",
            "year",
            "release_date",
            "release_date_string",
            "status",
            "kind",
            "episodes",
            "progress_total",
            "score",
            "poster_url",
            "poster",
            "poster_image_url",
            "genres",
            "studios",
            "movies",
            "ovas",
            "movie_count",
            "ova_count",
            "total_items",
            "created_at",
            "updated_at",
            "data_source",
            "shikimori_id",
            "kodik_link",
            "kodik_id",
            "quality",
            "screenshots",
            "seasons",
            "last_season",
            "last_episode",
            "seasons_count",
            "translations",
            "franchise_id",
            "is_franchise",
            "franchise_order",
            "download_links",
            "episode_duration",
            "total_duration",
        ]
        read_only_fields = ["created_at", "updated_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    poster_image_url = serializers.SerializerMethodField()
    genres_display = serializers.SerializerMethodField()
    genres = serializers.SerializerMethodField()
    slug = serializers.SlugField(read_only=True)
    slug_en = serializers.SerializerMethodField()
    
    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        if not obj.poster_url:
            return "/placeholder-anime.jpg"
        if obj.poster_url.startswith("/media"):
            return f"{settings.SITE_URL}{obj.poster_url}"
        return obj.poster_url
    
    def get_genres(self, obj):
        if not obj.genres:
            return []
        if isinstance(obj.genres, list):
            return obj.genres
        return []
    
    def get_genres_display(self, obj):
        genres = self.get_genres(obj)
        if not genres:
            return ""
        return ", ".join(genres)
    
    def get_slug_en(self, obj):
        import re

        title = obj.title_en or obj.title_ru
        if not title:
            return obj.slug or ""
        
        slug = title.lower()
        replacements = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
            "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
            "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        
        slug = re.sub(r"[^a-z0-9\s-]", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        slug = slug.replace(" ", "-")
        
        return slug

    class Meta:
        model = AnimeAnnouncement
        fields = [
            "id",
            "slug",
            "slug_en",
            "title_ru",
            "title_en",
            "release_date",
            "status",
            "description",
            "score",
            "rating",
            "type",
            "episodes",
            "studio",
            "genres",
            "genres_display",
            "poster_url",
            "poster_image_url",
            "next_episode_date",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class FranchiseEntrySerializer(serializers.ModelSerializer):
    poster_image_url = serializers.SerializerMethodField()
    anime_slug = serializers.SerializerMethodField()

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        return obj.poster_url or ""

    def get_anime_slug(self, obj):
        return obj.slug or str(obj.pk)

    class Meta:
        model = Anime
        fields = [
            "id",
            "slug",
            "title_ru",
            "title_en",
            "title_jp",
            "kind",
            "episodes",
            "episode_duration",
            "total_duration",
            "genres",
            "year",
            "score",
            "status",
            "poster_url",
            "poster_image_url",
            "anime_slug",
            "franchise_order",
            "kodik_link",
        ]


class FranchiseSerializer(serializers.ModelSerializer):
    entries = serializers.SerializerMethodField()
    poster_image_url = serializers.SerializerMethodField()
    parts_count = serializers.SerializerMethodField()
    year_range = serializers.SerializerMethodField()
    avg_score = serializers.SerializerMethodField()
    all_genres = serializers.SerializerMethodField()
    all_posters = serializers.SerializerMethodField()

    def _entries(self, obj):
        cache = getattr(self, '_entries_cache', None)
        if cache is None:
            cache = self._entries_cache = {}
        if obj.pk not in cache:
            supplied = self.context.get('entries_by_franchise')
            if hasattr(obj, '_visible_entries'):
                cache[obj.pk] = obj._visible_entries
            elif supplied is not None:
                cache[obj.pk] = list(supplied.get(obj.pk, []))
            else:
                from apps.seo.service import visible_anime
                cache[obj.pk] = list(
                    visible_anime().filter(franchise=obj).order_by('franchise_order', 'pk')
                )
        return cache[obj.pk]

    def get_entries(self, obj):
        return [entry.pk for entry in self._entries(obj)]

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        if obj.poster_url:
            return obj.poster_url
        first_entry = next((entry for entry in self._entries(obj) if entry.poster_image_url), None)
        if first_entry:
            if first_entry.poster and hasattr(first_entry.poster, "url"):
                return first_entry.poster.url
            return first_entry.poster_url
        return ""

    def get_parts_count(self, obj):
        return len(self._entries(obj))

    def get_year_range(self, obj):
        entries = self._entries(obj)
        years = [e.year for e in entries if e.year]
        if not years:
            return "-"
        year_start = min(years)
        year_end = max(years)
        if year_start == year_end:
            return str(year_start)
        return f"{year_start} – {year_end}"

    def get_avg_score(self, obj):
        if obj.score:
            return round(obj.score, 1)
        entries = self._entries(obj)
        scores = [e.score for e in entries if e.score]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    def get_all_genres(self, obj):
        if obj.genres:
            return obj.genres
        entries = self._entries(obj)
        genres = set()
        for entry in entries:
            if entry.genres:
                genres.update(entry.genres)
        return list(genres)

    def get_all_posters(self, obj):
        entries = self._entries(obj)
        posters = []
        for entry in entries:
            if entry.poster and hasattr(entry.poster, "url"):
                posters.append(entry.poster.url)
            elif entry.poster_url:
                posters.append(entry.poster_url)
        return posters

    def to_representation(self, obj):
        data = super().to_representation(obj)
        entries = self._entries(obj)
        years = [entry.year for entry in entries if entry.year]
        scores = [entry.score for entry in entries if entry.score is not None]
        genres = sorted({genre for entry in entries for genre in (entry.genres or []) if isinstance(genre, str)})
        posters = [entry.poster_image_url for entry in entries if entry.poster_image_url]
        count = len(entries)
        remainder = count % 100
        if count % 10 == 1 and remainder != 11:
            parts_label = 'части'
        elif count % 10 in (2, 3, 4) and remainder not in (12, 13, 14):
            parts_label = 'частей'
        else:
            parts_label = 'частей'
        year_text = (f' с {min(years)} по {max(years)} год' if years and min(years) != max(years)
                     else f' {years[0]} года' if years else '')
        fallback_description = (f'«{obj.name}» — франшиза из {count} {parts_label}{year_text}. '
                                'Части собраны в порядке просмотра; для каждой указаны формат, год и число серий.')
        data.update(entries=[entry.pk for entry in entries], parts_count=count,
            year_start=min(years) if years else None, year_end=max(years) if years else None,
            year_range=str(min(years)) if years and min(years) == max(years) else f'{min(years)} – {max(years)}' if years else '-',
            avg_score=round(sum(scores) / len(scores), 1) if scores else None,
            score=round(sum(scores) / len(scores), 1) if scores else None,
            all_genres=genres, all_posters=posters, poster_image_url=posters[0] if posters else '',
            poster_url=posters[0] if posters else '',
            description=(obj.description or '').strip() or fallback_description)
        return data

    class Meta:
        model = Franchise
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "poster_url",
            "poster_image_url",
            "score",
            "year_start",
            "year_end",
            "entries",
            "parts_count",
            "year_range",
            "avg_score",
            "all_genres",
            "all_posters",
            "created_at",
            "updated_at",
        ]


class ClipTaskSerializer(serializers.ModelSerializer):
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    download_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    def get_download_url(self, obj):
        return obj.download_url or ""
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            return obj.thumbnail.url
        return None

    class Meta:
        model = ClipTask
        fields = [
            'id',
            'task_type',
            'anime',
            'anime_title',
            'episode',
            'season',
            'start_time',
            'end_time',
            'timestamp',
            'label',
            'quality',
            'status',
            'result_file',
            'download_url',
            'thumbnail_url',
            'duration',
            'file_size',
            'error_message',
            'created_at',
            'started_at',
            'completed_at',
        ]
        read_only_fields = ['status', 'result_file', 'error_message', 'created_at', 'started_at', 'completed_at']


class ClipTaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClipTask
        fields = [
            'anime',
            'episode',
            'season',
            'start_time',
            'end_time',
            'timestamp',
            'label',
            'quality',
            'task_type',
            'format',
        ]
    
    def validate(self, data):
        if data.get('task_type') == 'clip':
            if 'start_time' not in data or 'end_time' not in data:
                raise serializers.ValidationError({
                    'start_time': 'Требуется для видео фрагмента',
                    'end_time': 'Требуется для видео фрагмента'
                })
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError({
                    'end_time': 'Время конца должно быть больше времени начала'
                })
        
        elif data.get('task_type') == 'screenshot':
            if 'timestamp' not in data:
                raise serializers.ValidationError({
                    'timestamp': 'Требуется для скриншота'
                })
            if data['timestamp'] < 0:
                raise serializers.ValidationError({
                    'timestamp': 'Время не может быть отрицательным'
                })
        
        return data


class AnimeScheduleSerializer(serializers.ModelSerializer):
    poster_image_url = serializers.SerializerMethodField()
    title_en = serializers.CharField(source='title', read_only=True)
    title_jp = serializers.CharField(source='title', read_only=True)
    kind = serializers.CharField(default='tv', read_only=True)
    genres = serializers.ListField(default=list, read_only=True)
    studios = serializers.ListField(default=list, read_only=True)
    description = serializers.SerializerMethodField()
    release_date = serializers.SerializerMethodField()
    release_date_string = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    shikimori_id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.mal_id or obj.id

    def get_shikimori_id(self, obj):
        return obj.mal_id

    def get_status(self, obj):
        return 'announced'

    def get_description(self, obj):
        return ''

    def get_release_date(self, obj):
        return None

    def get_release_date_string(self, obj):
        return ''

    def get_poster_image_url(self, obj):
        if obj.poster and hasattr(obj.poster, "url"):
            return obj.poster.url
        return obj.poster_url or ""

    def get_anime_slug(self, obj):
        import re
        
        title = obj.title_ru or obj.title
        if not title:
            return ""
        
        slug = title.lower()
        replacements = {
            "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
            "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
            "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
            "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
            "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
            "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
            "э": "e", "ю": "yu", "я": "ya",
        }
        for ru, lat in replacements.items():
            slug = slug.replace(ru, lat)
        
        slug = re.sub(r"[^a-z0-9]", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        slug = slug.strip("-")
        
        return slug

    class Meta:
        model = AnimeSchedule
        fields = [
            "id",
            "mal_id",
            "shikimori_id",
            "title_ru",
            "title",
            "title_en",
            "title_jp",
            "status",
            "airing",
            "broadcast_day",
            "episodes",
            "score",
            "year",
            "poster_url",
            "poster_image_url",
            "kind",
            "genres",
            "studios",
            "description",
            "release_date",
            "release_date_string",
            "created_at",
            "updated_at",
            "anime_slug",  
        ]


class CatalogSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogSettings
        fields = ["id", "group_franchises", "updated_at"]
