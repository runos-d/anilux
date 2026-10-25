from rest_framework import serializers
import os
from django.db import transaction
from apps.playlists.topics import TOPIC_BY_SLUG
from apps.playlists.application import synchronize_anime_items
from apps.playlists.models import PlaylistTopic
from django.conf import settings
from apps.playlists.infrastructure.models.playlists import Playlist, PlaylistItem, FavoriteAnime, FavoritePlaylist, PlaylistShareLink
from apps.anime.infrastructure.models.anime import Anime


def get_full_url(url):
    if not url:
        return None
    if url.startswith('https://') or url.startswith('http://'):
        return url
    base_url = getattr(settings, 'SITE_URL', os.environ.get('SITE_URL'))
    if url.startswith('/media/media/'):
        url = url.replace('/media/media/', '/media/')
    return f"{base_url}{url if url.startswith('/') else '/' + url}"


class NestedPlaylistSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_is_premium = serializers.BooleanField(source='user.is_premium', read_only=True)
    items_count = serializers.SerializerMethodField()
    cover_urls = serializers.SerializerMethodField()
    cover_image = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'title', 'description', 'cover_image', 'cover_urls',
            'user_id', 'user_username', 'user_is_premium', 'items_count', 'visibility',
            'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_items_count(self, obj):
        return getattr(obj, 'items_count_ann', None) if hasattr(obj, 'items_count_ann') else obj.items.count()

    def get_cover_image(self, obj):
        return get_full_url(obj.cover_image.url) if obj.cover_mode == 'custom' and obj.cover_image else None

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned


class PlaylistItemSerializer(serializers.ModelSerializer):
    item_type = serializers.CharField(read_only=True)
    is_nested_playlist = serializers.BooleanField(read_only=True)
    user_watch_progress = serializers.SerializerMethodField()
    
    anime = serializers.IntegerField(source='anime.id', read_only=True, allow_null=True, default=None)
    anime_id = serializers.IntegerField(source='anime.id', read_only=True, allow_null=True, default=None)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True, allow_null=True, default=None)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True, allow_null=True, default=None)
    anime_slug = serializers.CharField(source='anime.slug', read_only=True, allow_null=True, default=None)
    anime_poster = serializers.SerializerMethodField()
    anime_poster_url = serializers.CharField(source='anime.poster_url', read_only=True, allow_null=True, default=None)
    anime_year = serializers.IntegerField(source='anime.year', read_only=True, allow_null=True, default=None)
    anime_score = serializers.FloatField(source='anime.score', read_only=True, allow_null=True, default=None)
    anime_status = serializers.CharField(source='anime.status', read_only=True, allow_null=True, default=None)
    anime_kind = serializers.CharField(source='anime.kind', read_only=True, allow_null=True, default=None)
    anime_genres = serializers.ListField(source='anime.genres', read_only=True, allow_null=True, default=None)
    anime_episodes = serializers.IntegerField(source='anime.episodes', read_only=True, allow_null=True, default=None)
    anime_episode_duration = serializers.IntegerField(source='anime.episode_duration', read_only=True, allow_null=True, default=None)
    anime_total_duration = serializers.IntegerField(source='anime.total_duration', read_only=True, allow_null=True, default=None)
    
    nested_playlist_data = serializers.SerializerMethodField()

    class Meta:
        model = PlaylistItem
        fields = [
            'id', 'item_type', 'is_nested_playlist',
            'anime', 'anime_id', 'anime_title', 'anime_title_en', 'anime_slug',
            'anime_poster', 'anime_poster_url', 'anime_year', 'anime_score',
            'anime_status', 'anime_kind', 'anime_genres',
            'anime_episodes', 'anime_episode_duration', 'anime_total_duration',
            'nested_playlist_data',
            'position', 'notes', 'added_at', 'created_at', 'user_watch_progress'
        ]
        read_only_fields = ['id', 'added_at', 'created_at']

    def get_anime_poster(self, obj):
        if not obj.anime:
            return None
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url or None

    def get_nested_playlist_data(self, obj):
        if not obj.nested_playlist:
            return None
        return NestedPlaylistSerializer(obj.nested_playlist, context=self.context).data

    def get_user_watch_progress(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        cache = self.context.get('user_library_cache')
        if cache is not None:
            lib = cache.get(obj.anime_id)
        else:
            try:
                from apps.users.infrastructure.models.users import UserLibrary
                lib = UserLibrary.objects.filter(user=request.user, anime=obj.anime).first()
            except Exception:
                lib = None
        if lib:
            return {
                'current_episode': lib.current_episode,
                'episodes_watched': lib.effective_episodes_watched,
                'status': lib.status,
                'progress_percentage': lib.get_progress_percentage(),
            }
        return None


class TopicSelectionMixin:
    def validate_topics(self, values):
        slugs = [topic.slug for topic in values]
        if self.instance and set(slugs) == set(self.instance.topics.values_list('slug', flat=True)):
            return values
        if len(slugs) > 2 or any(slug not in TOPIC_BY_SLUG for slug in slugs):
            raise serializers.ValidationError('Выберите до двух тематик из предложенного списка')
        groups = [TOPIC_BY_SLUG[slug]['group'] for slug in slugs]
        if len(set(groups)) != len(groups):
            raise serializers.ValidationError('Выберите по одной тематике в каждой группе')
        return values


class SelectionEntrySerializer(serializers.Serializer):
    anime_id = serializers.IntegerField(min_value=1)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=5000)


class PlaylistSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    user_is_premium = serializers.BooleanField(source='user.is_premium', read_only=True)

    items = PlaylistItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()

    cover_image = serializers.SerializerMethodField()
    cover_urls = serializers.SerializerMethodField()

    is_favorited = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()

    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    topics = serializers.SlugRelatedField(many=True, slug_field='slug', read_only=True)
    genres = serializers.SerializerMethodField()

    visibility = serializers.CharField(read_only=True)
    is_public = serializers.BooleanField(read_only=True)
    is_private = serializers.BooleanField(read_only=True)
    is_link_only = serializers.BooleanField(read_only=True)

    share_token = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'user_id', 'user_username', 'user_avatar', 'user_is_premium',
            'title', 'description', 'cover_image', 'cover_mode', 'cover_urls',
            'visibility', 'is_public', 'is_private', 'is_link_only',
            'is_favorited', 'favorites_count', 'likes_count', 'is_liked', 'topics',
            'created_at', 'updated_at', 'items', 'items_count', 'genres',
            'share_token', 'total_duration',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes_count if hasattr(obj, 'likes_count') else obj.likes.count()

    def get_is_liked(self, obj):
        if hasattr(obj, 'is_liked'):
            return obj.is_liked
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.likes.filter(user=request.user).exists())

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        include_items = self.context.get('include_items') or (
            request is not None and request.query_params.get('include_items') == 'true'
        )
        if not include_items:
            fields.pop('items', None)
        if not include_items:
            fields.pop('genres', None)
        return fields

    def get_user_avatar(self, obj):
        if hasattr(obj.user, 'avatar') and obj.user.avatar:
            avatar_url = obj.user.avatar.url
            if avatar_url.startswith('/media/media/'):
                avatar_url = avatar_url.replace('/media/media/', '/media/')
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(avatar_url)
            return get_full_url(avatar_url)
        return None

    def get_items_count(self, obj):
        return getattr(obj, 'items_count_ann', None) if hasattr(obj, 'items_count_ann') else obj.items.count()

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if hasattr(obj, 'is_favorited_ann'):
            return obj.is_favorited_ann
        if request and request.user.is_authenticated:
            return FavoritePlaylist.objects.filter(user=request.user, playlist=obj).exists()
        return False

    def get_favorites_count(self, obj):
        return obj.favorites_count_ann if hasattr(obj, 'favorites_count_ann') else obj.favorited_by.count()

    def get_genres(self, obj):
        genres = set()
        for item in obj.items.all():
            for genre in (item.anime.genres or []) if item.anime else []:
                genres.add(genre)
        return list(genres)[:10]

    def get_cover_image(self, obj):
        return get_full_url(obj.cover_image.url) if obj.cover_mode == 'custom' and obj.cover_image else None

    def get_cover_urls(self, obj):
        if hasattr(obj, 'cover_items'):
            urls = []
            for item in obj.cover_items:
                poster = item.anime.poster.url if item.anime and item.anime.poster else getattr(item.anime, 'poster_url', None)
                if poster:
                    urls.append(poster)
        else:
            urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned

    def get_share_token(self, obj):
        request = self.context.get('request')
        if not request or getattr(self.context.get('view'), 'action', None) in ('list', 'public', 'my'):
            return None
        is_owner = request.user.is_authenticated and obj.user_id == request.user.id
        if is_owner or obj.is_link_only:
            link = obj.get_active_share_link()
            if link:
                return link.token
        return None

    def get_total_duration(self, obj):
        return obj.total_duration or 0


class PlaylistCreateSerializer(TopicSelectionMixin, serializers.ModelSerializer):
    items = SelectionEntrySerializer(many=True, required=False, write_only=True, max_length=1000)
    topics = serializers.SlugRelatedField(many=True, slug_field='slug', queryset=PlaylistTopic.objects.all(), required=False)
    cover_urls = serializers.SerializerMethodField()
    visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        default='public',
        required=False
    )

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'visibility', 'topics', 'items', 'cover_urls', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned

    @transaction.atomic
    def create(self, validated_data):
        entries = validated_data.pop('items', None)
        validated_data['user'] = self.context['request'].user
        playlist = super().create(validated_data)
        if entries is not None:
            synchronize_anime_items(playlist, entries)
        if playlist.visibility == 'link':
            playlist.get_or_create_share_link()
        return playlist


class PlaylistUpdateSerializer(TopicSelectionMixin, serializers.ModelSerializer):
    items = SelectionEntrySerializer(many=True, required=False, write_only=True, max_length=1000)
    topics = serializers.SlugRelatedField(many=True, slug_field='slug', queryset=PlaylistTopic.objects.all(), required=False)
    cover_urls = serializers.SerializerMethodField()
    visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        required=False
    )

    class Meta:
        model = Playlist
        fields = ['id', 'title', 'description', 'visibility', 'topics', 'items', 'cover_urls', 'updated_at']
        read_only_fields = ['id', 'updated_at']

    @transaction.atomic
    def update(self, instance, validated_data):
        entries = validated_data.pop("items", None)
        old_visibility = instance.visibility
        instance = super().update(instance, validated_data)
        if entries is not None:
            synchronize_anime_items(instance, entries)
        new_visibility = instance.visibility
        if new_visibility == 'link' and old_visibility != 'link':
            instance.get_or_create_share_link()
        elif old_visibility == 'link' and new_visibility != 'link':
            instance.invalidate_share_links()
        return instance

    def get_cover_urls(self, obj):
        urls = obj.get_cover_urls()
        cleaned = []
        for url in urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned.append(get_full_url(url))
        return cleaned


class PlaylistItemCreateSerializer(serializers.ModelSerializer):
    anime_id = serializers.IntegerField(required=False)
    nested_playlist_id = serializers.CharField(required=False)
    franchise_id = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistItem
        fields = ['anime_id', 'nested_playlist_id', 'franchise_id', 'notes']

    def validate(self, data):
        anime_id = data.get('anime_id')
        nested_playlist_id = data.get('nested_playlist_id')
        franchise_id = data.get('franchise_id')
        
        ids_provided = sum(1 for x in [anime_id, nested_playlist_id, franchise_id] if x)
        
        if ids_provided > 1:
            raise serializers.ValidationError(
                "Нельзя добавить одновременно аниме, плейлист и франшизу"
            )
        if ids_provided == 0:
            raise serializers.ValidationError(
                "Необходимо указать anime_id, nested_playlist_id или franchise_id"
            )
        
        if anime_id:
            try:
                Anime.objects.get(id=anime_id)
            except Anime.DoesNotExist:
                raise serializers.ValidationError("Аниме не найдено")
        
        if franchise_id:
            try:
                from apps.anime.infrastructure.models.anime import Franchise
                Franchise.objects.get(id=franchise_id)
            except Exception:
                raise serializers.ValidationError("Франшиза не найдена")
        
        if nested_playlist_id:
            try:
                Playlist.objects.get(id=nested_playlist_id)
            except Playlist.DoesNotExist:
                raise serializers.ValidationError("Плейлист не найден")
        
        return data

    def create(self, validated_data):
        anime_id = validated_data.pop('anime_id', None)
        nested_playlist_id = validated_data.pop('nested_playlist_id', None)
        
        item = PlaylistItem(**validated_data)
        if anime_id:
            item.anime_id = anime_id
        if nested_playlist_id:
            item.nested_playlist_id = nested_playlist_id
        
        item.save()
        return item


class PlaylistItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaylistItem
        fields = ['position', 'notes']


class ReorderItemsSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField(), allow_empty=False)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Список элементов не может быть пустым")
        for item in value:
            if 'id' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь id")
            if 'position' not in item:
                raise serializers.ValidationError("Каждый элемент должен иметь position")
        return value


class FavoriteAnimeSerializer(serializers.ModelSerializer):
    anime = serializers.PrimaryKeyRelatedField(queryset=Anime.objects.all())
    anime_id = serializers.IntegerField(source='anime.id', read_only=True)
    anime_title = serializers.CharField(source='anime.title_ru', read_only=True)
    anime_title_en = serializers.CharField(source='anime.title_en', read_only=True)
    anime_poster = serializers.SerializerMethodField()
    anime_poster_url = serializers.CharField(source='anime.poster_url', read_only=True)
    anime_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoriteAnime
        fields = [
            'id', 'anime', 'anime_id', 'anime_title', 'anime_title_en',
            'anime_poster', 'anime_poster_url', 'anime_data', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_anime_poster(self, obj):
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            return get_full_url(poster_url)
        return obj.anime.poster_url

    def get_anime_data(self, obj):
        poster_url = None
        if obj.anime.poster and hasattr(obj.anime.poster, 'url'):
            poster_url = obj.anime.poster.url
            if poster_url.startswith('/media/media/'):
                poster_url = poster_url.replace('/media/media/', '/media/')
            poster_url = get_full_url(poster_url)
        return {
            'id': obj.anime.id,
            'title_ru': obj.anime.title_ru,
            'title_en': obj.anime.title_en,
            'title_jp': obj.anime.title_jp,
            'poster_url': obj.anime.poster_url,
            'poster': poster_url,
            'year': obj.anime.year,
            'status': obj.anime.status,
            'score': obj.anime.score,
            'kind': obj.anime.kind,
            'episodes': obj.anime.episodes,
            'genres': obj.anime.genres,
            'studios': obj.anime.studios,
            'description': obj.anime.description[:500] if obj.anime.description else '',
        }


class FavoritePlaylistSerializer(serializers.ModelSerializer):
    playlist_data = serializers.SerializerMethodField()

    class Meta:
        model = FavoritePlaylist
        fields = ['id', 'playlist', 'playlist_data', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_playlist_data(self, obj):
        cover_image_url = None
        if obj.playlist.cover_mode == 'custom' and obj.playlist.cover_image:
            cover_image_url = obj.playlist.cover_image.url
            if cover_image_url.startswith('/media/media/'):
                cover_image_url = cover_image_url.replace('/media/media/', '/media/')
            cover_image_url = get_full_url(cover_image_url)

        cover_urls = obj.playlist.get_cover_urls()
        cleaned_cover_urls = []
        for url in cover_urls:
            if url.startswith('/media/media/'):
                url = url.replace('/media/media/', '/media/')
            cleaned_cover_urls.append(get_full_url(url))

        return {
            'id': obj.playlist.id,
            'title': obj.playlist.title,
            'description': obj.playlist.description,
            'visibility': obj.playlist.visibility,
            'is_public': obj.playlist.is_public,
            'is_private': obj.playlist.is_private,
            'is_link_only': obj.playlist.is_link_only,
            'cover_image': cover_image_url,
            'cover_urls': cleaned_cover_urls,
            'user_id': obj.playlist.user.id,
            'user_username': obj.playlist.user.username,
            'items_count': obj.playlist.items.count(),
            'favorites_count': obj.playlist.favorited_by.count(),
            'likes_count': obj.playlist.likes.count(),
            'is_liked': any(like.user_id == self.context['request'].user.pk for like in obj.playlist.likes.all()),
            'topics': [topic.slug for topic in obj.playlist.topics.all()],
            'created_at': obj.playlist.created_at,
            'updated_at': obj.playlist.updated_at,
        }


class AddToPlaylistSerializer(serializers.Serializer):
    anime_id = serializers.IntegerField()
    playlist_id = serializers.IntegerField(required=False)
    new_playlist_title = serializers.CharField(required=False, max_length=255)
    new_playlist_description = serializers.CharField(required=False, allow_blank=True)
    new_playlist_visibility = serializers.ChoiceField(
        choices=['public', 'private', 'link'],
        default='public',
        required=False
    )
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        playlist_id = data.get('playlist_id')
        new_playlist_title = data.get('new_playlist_title')
        if not playlist_id and not new_playlist_title:
            raise serializers.ValidationError(
                "Необходимо указать playlist_id или new_playlist_title"
            )
        if playlist_id and new_playlist_title:
            raise serializers.ValidationError(
                "Укажите либо существующий плейлист, либо создайте новый"
            )
        return data
