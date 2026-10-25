from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.core.files.storage import default_storage
from django.conf import settings
from django.utils import timezone
from PIL import Image
import os
import uuid
import secrets
from datetime import timedelta
from PIL import Image as PILImage
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


VISIBILITY_PUBLIC = 'public'
VISIBILITY_PRIVATE = 'private'
VISIBILITY_LINK = 'link'

VISIBILITY_CHOICES = [
    (VISIBILITY_PUBLIC, 'Публичный'),
    (VISIBILITY_PRIVATE, 'Приватный'),
    (VISIBILITY_LINK, 'По ссылке'),
]


class PlaylistTopic(models.Model):
    slug = models.SlugField(primary_key=True, max_length=40)
    name = models.CharField(max_length=60)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Playlist(models.Model):
    id = models.CharField(max_length=8, primary_key=True, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    topics = models.ManyToManyField(PlaylistTopic, blank=True, related_name='playlists')

    cover_image = models.ImageField(
        upload_to='playlist_covers/',
        null=True,
        blank=True,
        verbose_name='Обложка'
    )

    cover_mode = models.CharField(max_length=10, choices=[('auto', 'Из постеров'), ('custom', 'Загруженная обложка')], default='auto')

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default=VISIBILITY_PUBLIC,
        verbose_name='Видимость'
    )

    @property
    def is_public(self):
        return self.visibility == VISIBILITY_PUBLIC

    @is_public.setter
    def is_public(self, value):
        if value:
            self.visibility = VISIBILITY_PUBLIC
        else:
            if self.visibility == VISIBILITY_PUBLIC:
                self.visibility = VISIBILITY_PRIVATE

    @property
    def is_private(self):
        return self.visibility == VISIBILITY_PRIVATE

    @property
    def is_link_only(self):
        return self.visibility == VISIBILITY_LINK

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    total_duration = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='Общая длительность (мин)'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Плейлист'
        verbose_name_plural = 'Плейлисты'
        indexes = [
            models.Index(fields=['visibility', '-created_at'], name='pl_vis_created_idx'),
            models.Index(fields=['visibility', '-updated_at'], name='pl_vis_updated_idx'),
            models.Index(fields=['user', '-created_at'], name='pl_user_created_idx'),
        ]

    def __str__(self):
        return f"{self.id} | {self.user.username}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.generate_unique_id()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_id():
        for _ in range(100):
            candidate = str(secrets.randbelow(10**8)).zfill(8)
            if not Playlist.objects.filter(id=candidate).exists():
                return candidate
        raise RuntimeError("Could not generate unique playlist ID")

    @property
    def items_count(self):
        return self.items.count()

    @property
    def favorites_count(self):
        return self.favorited_by.count()

    def recalculate_total_duration(self):
        self.total_duration = self.items.aggregate(total=models.Sum('anime__total_duration'))['total'] or 0
        self.save(update_fields=['total_duration', 'updated_at'])

    def get_cover_urls(self):
        cached = getattr(self, '_prefetched_objects_cache', {}).get('items')
        items = (item for item in cached if item.anime_id) if cached is not None else self.items.filter(anime_id__isnull=False).select_related('anime').order_by('position', 'added_at')[:3]
        urls = []
        for item in items:
            poster = item.anime.poster.url if item.anime.poster else item.anime.poster_url
            if poster:
                urls.append(poster.replace('/media/media/', '/media/'))
            if len(urls) == 3:
                break
        return urls

    def update_cover(self):
        return self.cover_image.url if self.cover_mode == 'custom' and self.cover_image else None

    def get_active_share_link(self):
        link = self.share_links.filter(
            is_active=True
        ).filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
        ).first()
        return link

    def get_or_create_share_link(self, ttl_days=30):
        link = self.get_active_share_link()
        if link:
            return link
        token = secrets.token_urlsafe(32)
        link = PlaylistShareLink.objects.create(
            playlist=self,
            token=token,
            expires_at=timezone.now() + timedelta(days=ttl_days),
        )
        return link

    def invalidate_share_links(self):
        self.share_links.update(is_active=False)


class PlaylistShareLink(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='share_links')
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='Истекает')
    is_active = models.BooleanField(default=True)
    access_count = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Share-ссылка плейлиста'
        verbose_name_plural = 'Share-ссылки плейлистов'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.playlist.title} / {self.token[:12]}..."

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    def touch(self):
        self.access_count += 1
        self.save(update_fields=['access_count'])


class PlaylistItem(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='items')
    
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, null=True, blank=True)
    nested_playlist = models.ForeignKey(
        Playlist, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='parent_items',
        verbose_name='Вложенный плейлист'
    )

    position = models.PositiveIntegerField(default=0, verbose_name='Позиция')
    notes = models.TextField(blank=True, verbose_name='Заметки')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        ordering = ['position', 'added_at']
        verbose_name = 'Элемент плейлиста'
        verbose_name_plural = 'Элементы плейлиста'
        indexes = [
            models.Index(fields=['playlist', 'position', 'added_at'], name='pl_item_order_idx'),
        ]

    def __str__(self):
        if self.anime:
            return f"{self.playlist.title}: {self.anime.title_ru}"
        elif self.nested_playlist:
            return f"{self.playlist.title}: [Плейлист] {self.nested_playlist.title}"
        return f"{self.playlist.title}: Пустой элемент"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.anime and self.nested_playlist:
            raise ValidationError('Элемент не может быть одновременно аниме и плейлистом')
        if not self.anime and not self.nested_playlist:
            raise ValidationError('Элемент должен содержать аниме или вложенный плейлист')
        if self.nested_playlist and self.nested_playlist.id == self.playlist.id:
            raise ValidationError('Нельзя добавить плейлист самого в себя')

    def save(self, *args, **kwargs):
        self.clean()
        if self.position == 0:
            max_position = PlaylistItem.objects.filter(
                playlist=self.playlist
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = max_position + 1

        is_new = self._state.adding
        old_anime_id = None
        if not is_new:
            try:
                old = PlaylistItem.objects.get(pk=self.pk)
                old_anime_id = old.anime_id
            except PlaylistItem.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        if is_new or (self.anime_id and self.anime_id != old_anime_id):
            if self.anime:
                self.playlist.recalculate_total_duration()

    def delete(self, *args, **kwargs):
        playlist = self.playlist
        had_anime = bool(self.anime)
        super().delete(*args, **kwargs)
        if playlist and had_anime:
            playlist.recalculate_total_duration()

    @property
    def item_type(self):
        return 'playlist' if self.nested_playlist else 'anime'

    @property
    def is_nested_playlist(self):
        return bool(self.nested_playlist)


class PlaylistLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlist_likes')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'playlist'], name='unique_playlist_like')]
        indexes = [models.Index(fields=['playlist', 'created_at'], name='playlist_like_period_idx')]


class FavoritePlaylist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_playlists')
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ['user', 'playlist']
        verbose_name = 'Избранный плейлист'
        verbose_name_plural = 'Избранные плейлисты'

    def __str__(self):
        return f"{self.user.username} - {self.playlist.title}"


class FavoriteAnime(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_anime')
    anime = models.ForeignKey('anime.Anime', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        unique_together = ['user', 'anime']
        verbose_name = 'Избранное аниме'
        verbose_name_plural = 'Избранные аниме'

    def __str__(self):
        return f"{self.user.username} - {self.anime.title_ru}"
