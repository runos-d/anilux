from apps.social.infrastructure.chat_storage import chat_private_storage
from .chat_cascade import chat_cascade
from django.db import models, IntegrityError, transaction
from django.db.models.functions import Coalesce
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from django.utils import timezone
from apps.users.infrastructure.models.users import User
import secrets

def generate_public_id():
    return secrets.randbelow(90000000) + 10000000


class UUIDv8Model(models.Model):
    id = models.BigAutoField(primary_key=True)
    public_id = models.PositiveBigIntegerField(unique=True, null=False, db_index=True, default=generate_public_id)

    def save(self, *args, **kwargs):
        if not self._state.adding:
            return super().save(*args, **kwargs)
        for attempt in range(10):
            if self.public_id is None:
                self.public_id = generate_public_id()
            try:
                with transaction.atomic():
                    return super().save(*args, **kwargs)
            except IntegrityError as exc:
                if 'public_id' not in str(exc) or attempt == 9:
                    raise
                self.public_id = generate_public_id()

    class Meta:
        abstract = True


class Comment(UUIDv8Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='answer_to')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['parent', 'created_at']),
            models.Index(fields=['reply_to', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.content_object}"

    @property
    def is_reply(self):
        return self.parent is not None

    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        if self.author != user:
            return False
        if (timezone.now() - self.created_at).total_seconds() > 600:
            return False
        return True

    def can_delete(self, user):
        if not user.is_authenticated:
            return False
        if self.author == user:
            return True
        if user.is_staff or user.is_superuser:
            return True
        return False


class Group(UUIDv8Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    avatar_url = models.URLField(blank=True)
    avatar_file = models.ImageField(upload_to='groups/avatars/', null=True, blank=True)
    banner_url = models.URLField(blank=True)
    banner_file = models.ImageField(upload_to='groups/banners/', null=True, blank=True)

    is_private = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')

    moderators = models.ManyToManyField(User, related_name='moderated_groups', blank=True)

    members_count = models.IntegerField(default=1)  
    posts_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Group.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        
        if self.avatar_file:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.avatar_file, max_size=(500, 500), quality=85)
            if webp_file:
                self.avatar_file = webp_file
        
        if self.banner_file:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.banner_file, max_size=(1920, 500), quality=85)
            if webp_file:
                self.banner_file = webp_file
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def update_members_count(self):
        self.members_count = self.memberships.filter(role='member').count() + 1  
        self.save()


class GroupMembership(UUIDv8Model):
    ROLE_CHOICES = [
        ('member', 'Участник'),
        ('moderator', 'Модератор'),
        ('admin', 'Администратор'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class Post(UUIDv8Model):
    version = models.PositiveIntegerField(default=1)
    pending_edit = models.JSONField(default=dict, blank=True)

    TYPE_CHOICES = [
        ('text', 'Текстовый'),
        ('image', 'С изображением'),
        ('video', 'С видео'),
        ('playlist', 'С плейлистом'),
        ('anime', 'Об аниме'),
        ('repost', 'Репост'),
        ('system', 'Системный'),
    ]

    STATUS_CHOICES = [
        ('published', 'Опубликован'),
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('moderated', 'На модерации'),
        ('processing', 'Обработка вложений'),
        ('failed', 'Ошибка обработки'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Публично'),
        ('followers', 'Только подписчики'),
        ('friends', 'Только друзья'),
        ('private', 'Только я'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')

    title = models.CharField(max_length=200, blank=True)

    post_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')

    client_post_id = models.CharField(max_length=36, blank=True, db_index=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='published')

    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')

    text = models.TextField(blank=True)
    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to='posts/images/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='posts/videos/', null=True, blank=True)

    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    anime_rating = models.IntegerField(null=True, blank=True)  

    playlist = models.ForeignKey('playlists.Playlist', on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')

    reactor_post = models.ForeignKey('reactor.ReactorPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='feed_posts')

    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='posts')

    original_post = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='reposts_of')
    repost_comment = models.TextField(blank=True)  

    system_type = models.CharField(max_length=50, blank=True)  

    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    reposts_count = models.IntegerField(default=0)
    views_count = models.IntegerField(default=0)
    shares_count = models.IntegerField(default=0)

    is_pinned = models.BooleanField(default=False)
    pinned_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_spoiler = models.BooleanField(default=False)
    spoiler_description = models.CharField(max_length=255, blank=True)  
    spoiler_for = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='spoiler_posts')

    allow_comments = models.BooleanField(default=True)

    edited_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    feed_sort_at = models.GeneratedField(
        expression=Coalesce('published_at', 'created_at'), output_field=models.DateTimeField(), db_persist=True,
    )

    favorites = GenericRelation('social.Favorite', related_query_name='posts')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at', 'id']),
            models.Index(fields=['is_deleted', 'created_at', 'id', 'status', 'visibility', 'author', 'group', 'post_type', 'is_pinned'], name='post_read_scan'),
            models.Index(fields=['is_deleted', 'feed_sort_at', 'id', 'status', 'visibility', 'author', 'group', 'post_type', 'is_pinned'], name='post_feed_date_scan'),
            models.Index(fields=['author', 'created_at']),
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['anime', 'created_at']),
            models.Index(fields=['is_pinned', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['visibility', 'created_at']),
            models.Index(fields=['post_type', 'created_at']),
        ]

    def __str__(self):
        return f"Post by {self.author.username}: {self.text[:50]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def media_url(self):
        if self.video_file:
            return self.video_file.url
        elif self.image_file:
            return self.image_file.url
        elif self.video_url:
            return self.video_url
        elif self.image_url:
            return self.image_url
        return None

    def can_edit(self, user):
        if self.author != user:
            return False
        time_limit = timezone.now() - timezone.timedelta(minutes=5)
        return self.created_at > time_limit

    def can_delete(self, user):
        return self.author == user

    def can_like(self, user):
        if self.post_type == 'system':
            return False
        return True

    def can_dislike(self, user):
        return self.can_like(user)

    def is_liked_by(self, user):
        if not user.is_authenticated:
            return False
        return PostLike.objects.filter(user=user, post=self).exists()

    def is_disliked_by(self, user):
        if not user.is_authenticated:
            return False
        return PostDislike.objects.filter(user=user, post=self).exists()

    def is_reposted_by(self, user):
        if not user.is_authenticated:
            return False
        return Repost.objects.filter(user=user, original_post=self).exists()

    def is_bookmarked_by(self, user):
        if not user.is_authenticated:
            return False
        return Bookmark.objects.filter(user=user, post=self).exists()

    def get_content_preview(self, length=500):
        if len(self.text) <= length:
            return self.text
        return self.text[:length] + '...'

    def extract_hashtags(self):
        import re
        return re.findall(r'#([\w\-\u0400-\u04FF]+)', self.text)

    def extract_mentions(self):
        import re
        return re.findall(r'@(\w+)', self.text)


class GroupChat(UUIDv8Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='chat_avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_group_chats')
    is_public = models.BooleanField(default=False)
    invite_link = models.CharField(max_length=100, unique=True, null=True, blank=True)
    max_members = models.IntegerField(default=200)
    code = models.CharField(max_length=8, unique=True, blank=True)

    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='chats')

    franchise_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name='ИД франшизы')
    discussion_type = models.CharField(
        max_length=30, blank=True, default='',
        choices=[('', 'Обычный'), ('anime', 'Обсуждение аниме'), ('franchise', 'Обсуждение франшизы')],
        verbose_name='Тип обсуждения'
    )
    folder_type = models.CharField(
        max_length=30, blank=True, default='groups',
        choices=[('groups', 'Группы'), ('discussions', 'Обсуждения')],
        verbose_name='Папка чатов'
    )

    has_hidden_members = models.BooleanField(default=False)
    restrict_saving_content = models.BooleanField(default=False)
    slow_mode_delay = models.IntegerField(default=0)  
    history_visible = models.BooleanField(default=True)
    can_send_media = models.BooleanField(default=True)
    can_send_stickers = models.BooleanField(default=True)
    can_send_polls = models.BooleanField(default=True)
    can_add_web_page_previews = models.BooleanField(default=True)
    can_change_info = models.BooleanField(default=True)
    can_pin_messages = models.BooleanField(default=True)
    can_invite_users = models.BooleanField(default=True)

    members_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public']),
            models.Index(fields=['anime']),
        ]

    def __str__(self):
        return f"Группа: {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self._generate_code()
        for attempt in range(5):
            try:
                if GroupChat.objects.filter(code=self.code).exclude(pk=self.pk).exists():
                    self.code = self._generate_code()
                    continue
                with transaction.atomic():
                    super().save(*args, **kwargs)
                break
            except IntegrityError as exc:
                if "code" not in str(exc) or attempt == 4:
                    raise
                self.code = self._generate_code()

    @staticmethod
    def _generate_code():
        import secrets
        return str(secrets.randbelow(90000000) + 10000000)

    def update_members_count(self):
        self.members_count = self.members.count()
        self.save(update_fields=['members_count'])

def mark_as_read(self, user):
        from django.utils import timezone
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        from apps.social.infrastructure.models.social import Message, MessageReadStatus

        unread_messages = Message.objects.filter(
            chat=self
        ).exclude(
            read_statuses__user=user
        ).distinct()

        unread_message_ids = list(unread_messages.values_list('id', flat=True))
        sender_ids = set(unread_messages.values_list('sender_id', flat=True))

        if unread_message_ids:
            statuses = [
                MessageReadStatus(message_id=msg_id, user_id=user.id)
                for msg_id in unread_message_ids
            ]
            MessageReadStatus.objects.bulk_create(statuses, ignore_conflicts=True)

        if unread_message_ids:
            channel_layer = get_channel_layer()
            try:
                for sender_id in sender_ids:
                    if sender_id != user.id:
                        async_to_sync(channel_layer.group_send)(
                            f'chat_user_{sender_id}',
                            {
                                'type': 'messages_read_event',
                                'user_id': user.id,
                                'message_ids': unread_message_ids,
                                'read_at': timezone.now().isoformat(),
                                'sender_ids': list(sender_ids),
                            }
                        )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'Error sending read status: {e}')


class ChatRole(UUIDv8Model):
    ROLE_LEVELS = (
        (0, 'Участник'),
        (1, 'Модератор'),
        (2, 'Администратор'),
        (3, 'Владелец'),
    )

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='roles')
    name = models.CharField(max_length=50)
    level = models.IntegerField(choices=ROLE_LEVELS, default=0)
    color = models.CharField(max_length=7, default='#808080')  

    can_delete_messages = models.BooleanField(default=False)
    can_ban_users = models.BooleanField(default=False)
    can_pin_messages = models.BooleanField(default=False)
    can_add_new_admins = models.BooleanField(default=False)
    can_remain_anonymous = models.BooleanField(default=False)
    can_manage_chat = models.BooleanField(default=False)
    can_manage_video_chats = models.BooleanField(default=False)
    can_restrict_members = models.BooleanField(default=False)
    can_promote_members = models.BooleanField(default=False)
    can_change_chat_info = models.BooleanField(default=False)
    can_invite_users = models.BooleanField(default=False)
    can_post_messages = models.BooleanField(default=True)
    can_edit_messages = models.BooleanField(default=False)
    can_delete_chat = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['chat', 'name']
        ordering = ['-level', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class ChatMember(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_chat_memberships')
    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='members')

    role = models.ForeignKey(ChatRole, on_delete=models.SET_NULL, null=True, blank=True)

    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    until_date = models.DateTimeField(null=True, blank=True)  
    custom_title = models.CharField(max_length=32, blank=True)  

    is_muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    can_send_messages = models.BooleanField(default=True)
    can_send_media = models.BooleanField(default=True)
    can_add_reactions = models.BooleanField(default=True)
    can_send_polls = models.BooleanField(default=True)
    can_change_info = models.BooleanField(default=False)
    can_invite_users = models.BooleanField(default=False)
    can_pin_messages = models.BooleanField(default=False)

    is_banned = models.BooleanField(default=False)
    banned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='banned_users')
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_reason = models.TextField(blank=True)

    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'chat']
        indexes = [
            models.Index(fields=['user', 'chat']),
            models.Index(fields=['is_admin']),
            models.Index(fields=['is_banned']),
        ]

    def __str__(self):
        return f"{self.user.username} в {self.chat.name}"

    @property
    def is_owner(self):
        if getattr(self.chat, 'discussion_type', None) in ['anime', 'franchise']:
            return False
        return self.chat.created_by_id == self.user_id if self.chat.created_by_id else False

    @property
    def effective_permissions(self):
        from apps.social.application.chat_services import effective_member_permissions
        return effective_member_permissions(self)


class ChatAdminLog(UUIDv8Model):
    ACTION_CHOICES = (
        ('chat_created', 'Чат создан'),
        ('chat_updated', 'Настройки чата изменены'),
        ('member_joined', 'Участник присоединился'),
        ('member_left', 'Участник вышел'),
        ('member_banned', 'Участник забанен'),
        ('member_unbanned', 'Участник разбанен'),
        ('member_promoted', 'Участник повышен'),
        ('member_demoted', 'Участник понижен'),
        ('message_deleted', 'Сообщение удалено'),
        ('message_pinned', 'Сообщение закреплено'),
        ('message_unpinned', 'Сообщение откреплено'),
        ('invite_link_created', 'Пригласительная ссылка создана'),
        ('invite_link_revoked', 'Пригласительная ссылка отозвана'),
        ('slow_mode_changed', 'Режим медленной отправки изменен'),
    )

    chat = models.ForeignKey(GroupChat, on_delete=models.CASCADE, related_name='admin_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='admin_actions')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='targeted_actions')
    message = models.ForeignKey('Message', on_delete=models.SET_NULL, null=True, blank=True)
    details = models.JSONField(default=dict)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_action_display()} в {self.chat.name}"


class PrivateChat(UUIDv8Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user2')
    is_support = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)
    code = models.CharField(max_length=8, unique=True, blank=True)

    user1_notifications = models.BooleanField(default=True)
    user2_notifications = models.BooleanField(default=True)
    user1_muted_until = models.DateTimeField(null=True, blank=True)
    user2_muted_until = models.DateTimeField(null=True, blank=True)
    user1_archived = models.BooleanField(default=False)
    user2_archived = models.BooleanField(default=False)
    user1_pinned = models.BooleanField(default=False)
    user2_pinned = models.BooleanField(default=False)
    user1_blocked = models.BooleanField(default=False)
    user2_blocked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_message_at', '-created_at']
        unique_together = ['user1', 'user2']
        constraints = [models.CheckConstraint(condition=models.Q(user1__lt=models.F('user2')), name='private_chat_ordered_pair')]
        indexes = [
            models.Index(fields=['user1', 'last_message_at']),
            models.Index(fields=['user2', 'last_message_at']),
            models.Index(fields=['user1', 'user1_pinned']),
            models.Index(fields=['user2', 'user2_pinned']),
        ]

    def __str__(self):
        return f"Личный чат: {self.user1.username} ↔ {self.user2.username}"

    def save(self, *args, **kwargs):
        if self.user1_id and self.user2_id and self.user1_id > self.user2_id:
            self.user1_id, self.user2_id = self.user2_id, self.user1_id
            for field in self._meta.fields:
                if field.name.startswith('user1_'):
                    counterpart = field.name.replace('user1_', 'user2_', 1)
                    first, second = getattr(self, field.name), getattr(self, counterpart)
                    setattr(self, field.name, second)
                    setattr(self, counterpart, first)
        if not self.code:
            self.code = self._generate_code()
        if self.public_id is None:
            self.public_id = generate_public_id()
        with transaction.atomic():
            for attempt in range(5):
                try:
                    if PrivateChat.objects.filter(code=self.code).exclude(pk=self.pk).exists():
                        self.code = self._generate_code()
                        continue
                    with transaction.atomic():
                        super(PrivateChat, self).save(*args, **kwargs)
                    return
                except IntegrityError as exc:
                    msg = str(exc).lower()
                    if 'code' in msg and attempt < 4:
                        self.code = self._generate_code()
                        continue
                    raise

    @staticmethod
    def _generate_code():
        import secrets
        return str(secrets.randbelow(90000000) + 10000000)

    def other_user(self, current_user):
        if current_user == self.user1:
            return self.user2
        return self.user1

    def get_user_settings(self, user):
        if user.pk not in (self.user1_id, self.user2_id):
            raise ValueError('User is not a private chat participant')
        prefix = 'user1' if user.pk == self.user1_id else 'user2'
        data = {key: getattr(self, f'{prefix}_{key}') for key in ('notifications', 'muted_until', 'archived', 'pinned', 'blocked')}
        prefetched = getattr(self, '_prefetched_objects_cache', {}).get('settings')
        settings = next((row for row in prefetched if row.user_id == user.pk), None) if prefetched is not None else self.settings.filter(user=user).first()
        if settings:
            data.update(notifications=settings.notifications_enabled, muted_until=settings.muted_until,
                        archived=settings.is_archived, pinned=settings.is_pinned, blocked=settings.is_blocked,
                        custom_name=settings.custom_name, is_hidden=settings.is_hidden)
        data.update(notifications_enabled=data['notifications'], is_archived=data['archived'],
                    is_pinned=data['pinned'], is_blocked=data['blocked'],
                    is_muted=not data['notifications'] or bool(data['muted_until'] and data['muted_until'] > timezone.now()))
        return data

    def update_user_settings(self, user, **kwargs):
        if user == self.user1:
            for key, value in kwargs.items():
                setattr(self, f'user1_{key}', value)
        else:
            for key, value in kwargs.items():
                setattr(self, f'user2_{key}', value)
        self.save()

    def mark_as_read(self, user):
        from django.utils import timezone
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        other_user = self.other_user(user)
        if not other_user:
            return
        
        from apps.social.infrastructure.models.social import Message, MessageReadStatus
        
        unread_messages = Message.objects.filter(
            private_chat=self,
            sender=other_user
        ).exclude(
            read_statuses__user=user
        ).distinct()

        read_message_ids = list(unread_messages.values_list('id', flat=True))
        if read_message_ids:
            MessageReadStatus.objects.bulk_create(
                [
                    MessageReadStatus(message_id=message_id, user=user)
                    for message_id in read_message_ids
                ],
                ignore_conflicts=True,
            )

        if read_message_ids:
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    f'chat_user_{other_user.id}',
                    {
                        'type': 'messages_read_event',
                        'user_id': user.id,
                        'message_ids': read_message_ids,
                        'read_at': timezone.now().isoformat(),
                        'sender_ids': [other_user.id],
                    }
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f'Error sending read status: {e}')


class Message(UUIDv8Model):
    chat = models.ForeignKey('GroupChat', on_delete=chat_cascade, null=True, blank=True, related_name='group_messages')
    private_chat = models.ForeignKey('PrivateChat', on_delete=chat_cascade, null=True, blank=True, related_name='private_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField(blank=True)
    
    topic = models.ForeignKey('social.ChatTopic', null=True, blank=True,
                              on_delete=models.SET_NULL, related_name='messages')
    legacy_topic_id = models.IntegerField(null=True, blank=True, editable=False)
    
    media = models.FileField(upload_to='message_media/', storage=chat_private_storage, null=True, blank=True)
    media_type = models.CharField(max_length=20, blank=True)  

    location_latitude = models.FloatField(null=True, blank=True)
    location_longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)

    shared_post = models.ForeignKey('Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_playlist = models.ForeignKey('playlists.Playlist', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')
    shared_shorts = models.ForeignKey('reactor.ReactorPost', on_delete=models.SET_NULL, null=True, blank=True, related_name='shared_in_messages')

    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_messages')

    is_pinned = models.BooleanField(default=False)
    pinned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='pinned_messages')
    pinned_at = models.DateTimeField(null=True, blank=True)

    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    forwarded_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='forwarded_to')

    reactions = models.JSONField(default=dict)
    message_type = models.CharField(max_length=20, default='regular', choices=[('regular', 'Обычное'), ('system', 'Системное')])
    system_action = models.CharField(max_length=10, blank=True, null=True, choices=[('block', 'Блокировка'), ('unblock', 'Разблокировка')])
    system_target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    seq = models.PositiveBigIntegerField(default=0, db_index=True)
    client_message_id = models.CharField(max_length=36, blank=True, null=True, default=None)
    conversation = models.ForeignKey('social.Conversation', on_delete=models.CASCADE, related_name='messages')
    version = models.PositiveIntegerField(default=1)
    command_fingerprint = models.CharField(max_length=64, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['seq', 'id']
        constraints = [
            models.CheckConstraint(condition=(models.Q(chat__isnull=False, private_chat__isnull=True) | models.Q(chat__isnull=True, private_chat__isnull=False)), name='message_exactly_one_chat'),
            models.UniqueConstraint(fields=['conversation', 'seq'], name='message_conversation_seq_unique'),
            models.UniqueConstraint(fields=['conversation', 'sender', 'client_message_id'], name='message_command_unique'),
        ]
        indexes = [
            models.Index(fields=['chat', 'seq']),
            models.Index(fields=['private_chat', 'seq']),
            models.Index(fields=['sender', 'created_at']),
            models.Index(fields=['conversation', 'is_deleted', 'seq', 'sender', 'created_at'], name='message_unread_scan'),
            models.Index(fields=['chat', 'topic', 'created_at']),
            models.Index(
                fields=['private_chat', 'created_at'],
                name='social_msg_priv_created_idx',
            ),
        ]

    def __str__(self):
        return f"Сообщение от {self.sender.username}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            from apps.social.application.conversations import get_conversation
            if bool(self.chat_id) == bool(self.private_chat_id):
                raise ValueError('Message requires exactly one chat')
            with transaction.atomic():
                parent = self.parent_chat
                type(parent).objects.select_for_update().get(pk=parent.pk)
                conversation = get_conversation(parent, lock=True)
                conversation.next_message_seq += 1
                conversation.save(update_fields=['next_message_seq'])
                self.conversation = conversation
                self.seq = conversation.next_message_seq
                self.client_message_id = self.client_message_id or None
                return super().save(*args, **kwargs)
        return super().save(*args, **kwargs)

    @property
    def parent_chat(self):
        return self.chat or self.private_chat

    def can_edit(self, user):
        if self.is_deleted:
            return False

        if self.sender != user:
            return False

        time_limit = timezone.now() - timezone.timedelta(hours=48)
        return self.created_at > time_limit

    def can_delete(self, user):
        if self.is_deleted:
            return False

        if self.sender == user:
            return True

        if self.chat:
            try:
                member = self.chat.members.get(user=user)
                return member.effective_permissions.get('can_delete_messages', False)
            except ChatMember.DoesNotExist:
                return False

        return False


class MessageAttachment(UUIDv8Model):
    CONTENT_TYPE_CHOICES = [
        ('anime', 'Аниме'),
        ('playlist', 'Плейлист'),
        ('shorts', 'Shorts'),
        ('excerpt', 'Отрывок'),
        ('post', 'Пост'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='content_attachments')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)

    object_id = models.PositiveIntegerField()

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['message', 'content_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.content_type} attachment for message {self.message.id}"


class MessageReadStatus(UUIDv8Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reads')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']
        indexes = [
            models.Index(
                fields=['user', 'message'],
                name='social_reads_user_msg_idx',
            ),
        ]

    def __str__(self):
        return f"{self.user.username} прочел сообщение {self.message.id}"


class ChatTypingStatus(UUIDv8Model):
    chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, related_name='typing_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='typing_statuses')
    typed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['chat', 'user']
        indexes = [
            models.Index(fields=['chat', 'typed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} печатает в чате {self.chat.id}"


class ChatSettings(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_settings')
    chat = models.ForeignKey('GroupChat', on_delete=models.CASCADE, related_name='user_settings')

    notifications_enabled = models.BooleanField(default=True)
    sound_enabled = models.BooleanField(default=True)

    auto_repeat_enabled = models.BooleanField(default=False)
    repeat_interval = models.IntegerField(default=1000)  

    is_blocked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'chat']

    def __str__(self):
        return f"Settings for {self.user.username} in {self.chat}"


class PrivateChatUserSettings(UUIDv8Model):
    chat = models.ForeignKey('PrivateChat', on_delete=models.CASCADE, related_name='user_settings')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chat_settings')

    custom_name = models.CharField(max_length=255, blank=True)

    custom_avatar = models.ImageField(upload_to='private_chat_avatars/', null=True, blank=True)

    notifications_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['chat', 'user']

    def __str__(self):
        return f"Settings for {self.user.username} in private chat {self.chat.id}"


class Contest(UUIDv8Model):
    TYPE_CHOICES = [
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('seasonal', 'Сезонный'),
        ('special', 'Специальный'),
    ]

    FORMAT_CHOICES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('text', 'Текст'),
        ('mixed', 'Смешанный'),
    ]

    STATUS_CHOICES = [
        ('announce', 'Анонс'),
        ('active', 'Активен'),
        ('voting', 'Голосование'),
        ('finished', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='weekly')
    format = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='image')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='announce')

    theme = models.CharField(max_length=500, blank=True)
    rules = models.TextField(blank=True)

    prize_1st = models.CharField(max_length=500, blank=True)
    prize_2nd = models.CharField(max_length=500, blank=True)
    prize_3rd = models.CharField(max_length=500, blank=True)

    announced_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    voting_started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_contests')

    anime = models.ForeignKey('anime.Anime', on_delete=models.SET_NULL, null=True, blank=True, related_name='contests')

    entries_count = models.IntegerField(default=0)
    votes_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ContestEntry(UUIDv8Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='entries')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_entries')

    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    image_url = models.URLField(blank=True)
    image_file = models.ImageField(upload_to='contests/entries/images/', null=True, blank=True)
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to='contests/entries/videos/', null=True, blank=True)

    votes_count = models.IntegerField(default=0)

    is_winner = models.BooleanField(default=False)
    winner_place = models.IntegerField(null=True, blank=True)  

    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ['contest', 'participant']

    def __str__(self):
        return f"{self.participant.username} in {self.contest.title}"

    def save(self, *args, **kwargs):
        if self.image_file:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.image_file, max_size=(1920, 1920), quality=85)
            if webp_file:
                self.image_file = webp_file
        super().save(*args, **kwargs)


class ContestVote(UUIDv8Model):
    contest = models.ForeignKey(Contest, on_delete=models.CASCADE, related_name='votes')
    entry = models.ForeignKey(ContestEntry, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contest_votes')

    vote_type = models.CharField(max_length=20, choices=[
        ('like', 'Лайк'),
        ('star', 'Звезда'),
        ('heart', 'Сердце'),
    ], default='like')

    value = models.IntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['contest', 'entry', 'voter']
        indexes = [
            models.Index(fields=['contest', 'voter']),
        ]

    def __str__(self):
        return f"{self.voter.username} voted for {self.entry}"


class Follow(UUIDv8Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['follower', 'following']
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class PostLike(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} likes post {self.post.id}"


class PostDislike(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_dislikes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='dislikes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} dislikes post {self.post.id}"


class Repost(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reposts')
    original_post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reposts')
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'original_post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['original_post', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reposted {self.original_post.id}"


class Achievement(UUIDv8Model):
    CATEGORY_CHOICES = [
        ('basic', 'Основные'),
        ('social', 'Социальные'),
        ('collection', 'Коллекционные'),
        ('contest', 'Конкурсные'),
        ('special', 'Специальные'),
    ]

    LEVEL_CHOICES = [
        ('bronze', 'Бронзовый'),
        ('silver', 'Серебряный'),
        ('gold', 'Золотой'),
        ('legendary', 'Легендарный'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.ImageField(upload_to='achievements/icons/', null=True, blank=True)
    icon_svg = models.CharField(max_length=100, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='basic')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='bronze')

    condition_type = models.CharField(max_length=50)
    condition_value = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    unlocked_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'level', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

    def save(self, *args, **kwargs):
        if self.icon:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.icon, max_size=(200, 200), quality=85)
            if webp_file:
                self.icon = webp_file
        super().save(*args, **kwargs)


class UserAchievement(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='unlocked_by')

    progress = models.IntegerField(default=0)  
    is_unlocked = models.BooleanField(default=False)

    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at', '-progress']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class UploadedFile(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files')

    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=20)  
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  
    mime_type = models.CharField(max_length=100)

    thumbnail = models.ImageField(upload_to='uploads/thumbnails/', null=True, blank=True)

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
        ]

    def __str__(self):
        return f"{self.file_name} by {self.user.username}"

    def save(self, *args, **kwargs):
        if self.file and self.file_type == 'image':
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.file, max_size=(1920, 1920), quality=85)
            if webp_file:
                self.file = webp_file
        if self.thumbnail:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.thumbnail, max_size=(400, 400), quality=80)
            if webp_file:
                self.thumbnail = webp_file
        super().save(*args, **kwargs)


class Reaction(UUIDv8Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='message_reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    emoji = models.CharField(max_length=50)  

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user', 'emoji']
        indexes = [
            models.Index(fields=['message', 'created_at']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} reacted {self.emoji} to message {self.message.id}"


class Attachment(UUIDv8Model):
    ATTACHMENT_TYPES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
        ('audio', 'Аудио'),
        ('file', 'Файл'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    type = models.CharField(max_length=20, choices=ATTACHMENT_TYPES)

    file = models.FileField(upload_to='attachments/', storage=chat_private_storage)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()  
    mime_type = models.CharField(max_length=100)

    thumbnail = models.ImageField(upload_to='attachments/thumbnails/', storage=chat_private_storage, null=True, blank=True)

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['uploaded_at']
        indexes = [
            models.Index(fields=['message', 'uploaded_at']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.get_type_display()}: {self.file_name}"

    def save(self, *args, **kwargs):
        if self.file and self.type == 'image':
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.file, max_size=(1920, 1920), quality=85)
            if webp_file:
                self.file = webp_file
        if self.thumbnail:
            from apps.social.application.image_processor import convert_to_webp
            webp_file = convert_to_webp(self.thumbnail, max_size=(400, 400), quality=80)
            if webp_file:
                self.thumbnail = webp_file
        super().save(*args, **kwargs)


class EmailLog(UUIDv8Model):
    EMAIL_TYPES = [
        ('daily_digest', 'Ежедневный дайджест'),
        ('weekly_digest', 'Еженедельный дайджест'),
        ('mention', 'Упоминание'),
        ('message', 'Новое сообщение'),
        ('system', 'Системное уведомление'),
        ('chat_invite', 'Приглашение в чат'),
    ]

    STATUS_CHOICES = [
        ('pending', 'В ожидании'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs')
    email_type = models.CharField(max_length=20, choices=EMAIL_TYPES)

    subject = models.CharField(max_length=255)
    to_email = models.EmailField()
    content = models.TextField(blank=True)  

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    chat_id = models.BigIntegerField(null=True, blank=True)
    message_id = models.BigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['email_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.get_email_type_display()} to {self.to_email} ({self.get_status_display()})"




class ChatFolder(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_folders')

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default='📁')  
    color = models.CharField(max_length=7, default='#7c4dff')  
    position = models.IntegerField(default=0)

    include_private = models.BooleanField(default=False)
    include_groups = models.BooleanField(default=False)
    include_archived = models.BooleanField(default=False)
    include_pinned = models.BooleanField(default=False)
    include_channels = models.BooleanField(default=False)
    include_muted = models.BooleanField(default=True)
    match_all = models.BooleanField(default=False)
    rules = models.JSONField(default=dict, blank=True)

    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['position', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"Папка {self.name} пользователя {self.user.username}"


class ChatFolderChat(UUIDv8Model):
    folder = models.ForeignKey(ChatFolder, on_delete=models.CASCADE, related_name='chats')
    chat_id = models.BigIntegerField()
    chat_type = models.CharField(max_length=20)  
    conversation = models.ForeignKey('social.Conversation', null=True, blank=True,
                                     on_delete=models.CASCADE, related_name='folder_items')

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['folder', 'chat_type', 'chat_id']
        ordering = ['-added_at']

    def __str__(self):
        return f"Чат {self.chat_id} в папке {self.folder.name}"



class PostMedia(UUIDv8Model):
    processing_progress = models.PositiveSmallIntegerField(default=0)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    upload = models.OneToOneField('social.PostUpload', null=True, blank=True, on_delete=models.SET_NULL)
    processing_state = models.CharField(max_length=20, default='ready', db_index=True)
    is_active = models.BooleanField(default=True)
    variants = models.JSONField(default=dict, blank=True)
    processing_error = models.CharField(max_length=500, blank=True)

    TYPE_CHOICES = [
        ('image', 'Изображение'),
        ('video', 'Видео'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='media_files')
    media_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='image')

    from apps.social.infrastructure.post_storage import post_private_storage
    file = models.FileField(upload_to='posts/media/', storage=post_private_storage)
    url = models.URLField(blank=True)  

    thumbnail = models.ImageField(upload_to='posts/media/thumbnails/', storage=post_private_storage, null=True, blank=True)
    poster = models.ImageField(upload_to='posts/media/posters/', storage=post_private_storage, null=True, blank=True)

    caption = models.CharField(max_length=500, blank=True)

    order = models.IntegerField(default=0)

    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  
    file_size = models.BigIntegerField(null=True, blank=True)  
    mime_type = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['post', 'order']),
        ]

    def __str__(self):
        return f"Media for post {self.post.id} (#{self.order})"

    def save(self, *args, **kwargs):
        if self.file and not self.mime_type:
            import mimetypes
            self.mime_type = mimetypes.guess_type(self.file.name)[0] or 'application/octet-stream'
        file_needs_conversion = (
            self.file and
            self.media_type == 'image' and
            not self.file.name.lower().endswith('.webp')
        )
        thumbnail_needs_conversion = (
            self.thumbnail and
            not self.thumbnail.name.lower().endswith('.webp')
        )

        super().save(*args, **kwargs)

        if file_needs_conversion and not self.upload_id:
            from apps.social.application.tasks import convert_post_media_to_webp
            transaction.on_commit(lambda: convert_post_media_to_webp.delay(self.id, 'file'), robust=True)

        if thumbnail_needs_conversion and not self.upload_id:
            from apps.social.application.tasks import convert_post_media_to_webp
            transaction.on_commit(lambda: convert_post_media_to_webp.delay(self.id, 'thumbnail'), robust=True)


class PostAttachment(UUIDv8Model):
    CONTENT_TYPE_CHOICES = [
        ('playlist', 'Плейлист'),
        ('anime', 'Аниме'),
        ('shorts', 'Shorts'),
        ('excerpt', 'Отрывок'),
    ]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='attachments')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    object_id = models.PositiveIntegerField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['post', 'content_type']),
        ]
        unique_together = ['post', 'content_type', 'object_id']

    def __str__(self):
        return f"{self.content_type} attachment for post {self.post.id}"


class PostComment(UUIDv8Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')

    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    content = models.TextField()

    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    likes_count = models.IntegerField(default=0)
    dislikes_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)

    path = models.CharField(max_length=500, blank=True)  
    level = models.IntegerField(default=0)  

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
            models.Index(fields=['post', 'path']),
            models.Index(fields=['author', 'created_at']),
        ]

    def __str__(self):
        return f"Comment by {self.author.username} on post {self.post.id}"

    @property
    def is_reply(self):
        return self.parent is not None


class PostCommentLike(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_likes')
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='likes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} likes comment {self.comment.id}"


class PostCommentDislike(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comment_dislikes')
    comment = models.ForeignKey(PostComment, on_delete=models.CASCADE, related_name='dislikes')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'comment']
        indexes = [
            models.Index(fields=['comment', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} dislikes comment {self.comment.id}"


class FeedView(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_views')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')

    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
        ]

    def __str__(self):
        return f"{self.user.username} viewed post {self.post.id}"


class Bookmark(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='bookmarks')

    folder = models.CharField(max_length=100, blank=True)  

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'folder']),
        ]

    def __str__(self):
        return f"{self.user.username} bookmarked post {self.post.id}"


class Report(UUIDv8Model):
    REASON_CHOICES = [
        ('spam', 'Спам'),
        ('copyright', 'Нарушение авторских прав'),
        ('harassment', 'Оскорбления / травля'),
        ('inappropriate', 'Неприемлемый контент (18+)'),
        ('spoiler', 'Спойлер без предупреждения'),
        ('other', 'Другое'),
    ]

    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('resolved', 'Рассмотрено'),
        ('rejected', 'Отклонено'),
    ]

    CONTENT_TYPE_CHOICES = [
        ('post', 'Пост'),
        ('comment', 'Комментарий'),
        ('user', 'Пользователь'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')

    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.PositiveIntegerField()

    reason = models.CharField(max_length=20, choices=REASON_CHOICES)

    comment = models.TextField(blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    resolved_at = models.DateTimeField(null=True, blank=True)
    moderation_comment = models.TextField(blank=True)
    action_taken = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reporter', 'created_at']),
            models.Index(fields=['content_type', 'content_id']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Report by {self.reporter.username}: {self.reason}"


class Hashtag(UUIDv8Model):
    name = models.CharField(max_length=100, unique=True)
    posts_count = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posts_count', 'name']

    def __str__(self):
        return f"#{self.name}"


class PostHashtag(UUIDv8Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hashtag_links')
    hashtag = models.ForeignKey(Hashtag, on_delete=models.CASCADE, related_name='post_links')

    class Meta:
        unique_together = ['post', 'hashtag']
        indexes = [
            models.Index(fields=['hashtag', 'post']),
        ]


class UserMention(UUIDv8Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mentions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions_in_posts')
    is_notified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['user', 'is_notified']),
        ]

    def __str__(self):
        return f"{self.user.username} mentioned in post {self.post.id}"


class UserPostHidden(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='hidden_for_users')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} hid post {self.post.id}"


class UserPostNotInterested(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='not_interested_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='not_interested_for_users')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'post']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} not interested in post {self.post.id}"


class UserNotificationSettings(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feed_notification_settings')

    notify_likes = models.BooleanField(default=True)

    notify_comments = models.BooleanField(default=True)

    notify_mentions = models.BooleanField(default=True)

    email_digest = models.CharField(
        max_length=20,
        choices=[
            ('never', 'Никогда'),
            ('daily', 'Раз в день'),
            ('weekly', 'Раз в неделю'),
        ],
        default='never'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User notification settings'

    def __str__(self):
        return f"Notification settings for {self.user.username}"

    @classmethod
    def get_or_create_settings(cls, user):
        settings, created = cls.objects.get_or_create(user=user)
        return settings


class UserNotInterested(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='not_interested_users')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hidden_by_users')

    reason = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'target_user']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} not interested in {self.target_user.username}"


class Favorite(UUIDv8Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_favorites')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    folder = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f"{self.user.username} favorited {self.content_type.model}#{self.object_id}"


from apps.social.infrastructure.models.social_chat import (
    ChatInviteLink, ChatWallpaper, ChatTheme, MessageReaction,
    ChatBan, ChatRestriction, ChatSlowMode, ChatJoinRequest,
    ChatTag, ChatTagAssignment, AntiSpamRule, ChatBackup, ScheduledMessage,
    ChatTopic, UserGlobalChatStyle
)
