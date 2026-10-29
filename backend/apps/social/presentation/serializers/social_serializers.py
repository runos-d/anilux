from apps.social.infrastructure.chat_storage import private_file_url
import logging
import random

from rest_framework import serializers
from django.db import IntegrityError, transaction
from django.db.models import Q, Count, Prefetch

logger = logging.getLogger(__name__)
from apps.social.infrastructure.models.social import (
    Comment,
    Group,
    GroupMembership,
    Post,
    ChatSettings,
    Message,
    Contest,
    ContestEntry,
    ContestVote,
    GroupChat,
    ChatRole,
    ChatMember,
    ChatAdminLog,
    PrivateChat,
    MessageReadStatus,
    PrivateChatUserSettings,
    Follow,
    PostLike,
    PostDislike,
    Repost,
    Achievement,
    UserAchievement,
    UploadedFile,
    Favorite,
    Reaction,
    Attachment,
    EmailLog,
    ChatFolder,
    ChatFolderChat,
    PostMedia,
    PostAttachment,
    PostComment,
    PostCommentLike,
    PostCommentDislike,
    FeedView,
    Bookmark,
    Report,
    Hashtag,
    PostHashtag,
    UserMention,
    UserPostHidden,
    UserPostNotInterested,
    UserNotificationSettings,
)
from apps.anime.infrastructure.models.anime import Anime
from apps.playlists.infrastructure.models.playlists import Playlist
from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social_news import News





def _extract_and_link_hashtags(post, text):
    import re
    if not text:
        return
    tags = re.findall(r'#([\w\-\u0400-\u04FF]+)', text)
    cleaned_text = re.sub(r'#([\w\-\u0400-\u04FF]+)', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    if cleaned_text != text:
        post.text = cleaned_text
        post.save(update_fields=['text'])
    for tag_name in tags:
        tag, _ = Hashtag.objects.get_or_create(name=tag_name.lower())
        PostHashtag.objects.get_or_create(post=post, hashtag=tag)


class PrivateChatSettingsSerializer(serializers.Serializer):
    custom_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notifications_enabled = serializers.BooleanField(required=False)
    mentions_only = serializers.BooleanField(required=False)
    sound_enabled = serializers.BooleanField(required=False)
    notification_sound = serializers.CharField(max_length=50, required=False, allow_blank=True)
    vibration_enabled = serializers.BooleanField(required=False)
    vibration_type = serializers.CharField(max_length=20, required=False, allow_blank=True)
    show_preview = serializers.BooleanField(required=False)
    show_popup = serializers.BooleanField(required=False)
    muted_until = serializers.DateTimeField(required=False, allow_null=True)
    is_archived = serializers.BooleanField(required=False)
    is_pinned = serializers.BooleanField(required=False)
    is_hidden = serializers.BooleanField(required=False)
    is_blocked = serializers.BooleanField(required=False)
    auto_delete_enabled = serializers.BooleanField(required=False)
    auto_delete_after = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    folder_id = serializers.IntegerField(required=False, allow_null=True)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)


class GroupMemberSettingsSerializer(serializers.Serializer):
    notifications_enabled = serializers.BooleanField(required=False)
    mentions_only = serializers.BooleanField(required=False)
    sound_enabled = serializers.BooleanField(required=False)
    notification_sound = serializers.CharField(max_length=50, required=False, allow_blank=True)
    vibration_enabled = serializers.BooleanField(required=False)
    vibration_type = serializers.CharField(max_length=20, required=False, allow_blank=True)
    show_preview = serializers.BooleanField(required=False)
    show_popup = serializers.BooleanField(required=False)
    muted_until = serializers.DateTimeField(required=False, allow_null=True)
    is_muted = serializers.BooleanField(required=False)
    is_pinned = serializers.BooleanField(required=False)
    is_archived = serializers.BooleanField(required=False)
    tags = serializers.ListField(child=serializers.CharField(max_length=50), required=False)


class GlobalChatStyleSerializer(serializers.Serializer):
    wallpaper_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    wallpaper_color = serializers.CharField(max_length=20, required=False, allow_blank=True)
    wallpaper_color2 = serializers.CharField(max_length=20, required=False, allow_blank=True)
    bubble_style = serializers.CharField(max_length=50, required=False, allow_blank=True)
    accent_color = serializers.CharField(max_length=20, required=False, allow_blank=True)
    font_size = serializers.CharField(max_length=20, required=False, allow_blank=True)
    message_animation = serializers.CharField(max_length=50, required=False, allow_blank=True)
    emoji_set = serializers.CharField(max_length=50, required=False, allow_blank=True)
    time_format = serializers.CharField(max_length=50, required=False, allow_blank=True)


class MuteGroupChatSerializer(serializers.Serializer):
    duration = serializers.IntegerField(required=False, allow_null=True, min_value=0)


class ArchiveChatSerializer(serializers.Serializer):
    is_archived = serializers.BooleanField(required=False)


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(
        source="reporter.username", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "content_type",
            "content_id",
            "reason",
            "reason_display",
            "comment",
            "status",
            "status_display",
            "created_at",
            "resolved_at",
            "resolved_by",
            "moderation_comment",
            "action_taken",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "created_at",
            "resolved_at",
            "resolved_by",
        ]


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)
    replies_count = serializers.SerializerMethodField()
    is_reply = serializers.ReadOnlyField()
    parent_id = serializers.CharField(source="parent.id", read_only=True)
    parent_username = serializers.CharField(
        source="parent.author.username", read_only=True
    )
    reply_to_data = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "author_username",
            "author_avatar",
            "author_is_premium",
            "text",
            "parent",
            "parent_id",
            "parent_username",
            "is_reply",
            "replies_count",
            "reply_to",
            "reply_to_data",
            "created_at",
            "updated_at",
            "is_deleted",
            "is_edited",
        ]
        read_only_fields = ["id", "author", "created_at", "updated_at"]

    def get_replies_count(self, obj):
        if hasattr(obj, "replies"):
            return obj.replies.filter(is_deleted=False).count()
        return obj.replies.count() if hasattr(obj, "replies") else 0

    def get_reply_to_data(self, obj):
        if obj.reply_to:
            return {
                "id": obj.reply_to.id,
                "author_id": obj.reply_to.author_id,
                "author_username": obj.reply_to.author.username,
                "author_avatar": obj.reply_to.author.avatar.url
                if obj.reply_to.author.avatar
                else None,
                "text": obj.reply_to.text,
                "created_at": obj.reply_to.created_at.isoformat()
                if obj.reply_to.created_at
                else None,
            }
        return None


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["text", "parent", "content_type", "object_id"]

    def validate(self, data):
        content_type = data.get("content_type")
        object_id = data.get("object_id")

        if content_type and object_id:
            try:
                model_class = content_type.model_class()
                model_class.objects.get(pk=object_id)
            except model_class.DoesNotExist:
                raise serializers.ValidationError("Object does not exist.")

        parent = data.get("parent")
        if parent:
            if parent.content_type != content_type or parent.object_id != object_id:
                raise serializers.ValidationError(
                    "Parent comment must be on the same object."
                )

        return data

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class GroupSerializer(serializers.ModelSerializer):
    creator_username = serializers.CharField(source="creator.username", read_only=True)
    is_member = serializers.SerializerMethodField()
    is_moderator = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "avatar_url",
            "avatar_file",
            "banner_url",
            "banner_file",
            "is_private",
            "creator",
            "creator_username",
            "moderators",
            "members_count",
            "posts_count",
            "is_member",
            "is_moderator",
            "public_id",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "creator",
            "members_count",
            "posts_count",
            "created_at",
            "updated_at",
        ]

    def get_is_member(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.memberships.filter(user=request.user).exists()
        return False

    def get_is_moderator(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return (
                obj.moderators.filter(pk=request.user.pk).exists()
                or obj.creator == request.user
            )
        return False


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["name", "description", "avatar_url", "avatar_file", "banner_url", "is_private", "anime"]
        read_only_fields = ["slug", "creator", "members_count", "posts_count", "created_at", "updated_at"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = GroupMembership
        fields = [
            "id",
            "user",
            "user_username",
            "group",
            "group_name",
            "role",
            "joined_at",
        ]
        read_only_fields = ["id", "joined_at"]


from .post_read import PostReadMixin, PostListSerializer, post_anime, playlist_card, reactor_card, attachment_content, anime_card, original_post


class PostSerializer(PostReadMixin, serializers.ModelSerializer):
    playlist = serializers.SerializerMethodField()
    reactor_post = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    playlist_title = serializers.CharField(source='playlist.title', read_only=True, default=None)
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(
        source="author.display_name", read_only=True
    )
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)
    anime_title = serializers.CharField(source="anime.title_ru", read_only=True)
    anime_poster = serializers.ImageField(source="anime.poster", read_only=True)
    anime = serializers.SerializerMethodField()
    group_name = serializers.CharField(source="group.name", read_only=True)
    group_avatar = serializers.ImageField(source="group.avatar_file", read_only=True)
    media_url = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    original_post = serializers.SerializerMethodField(method_name='get_original_post_data')
    original_post_data = serializers.SerializerMethodField()
    media_files = serializers.SerializerMethodField()
    attachments_data = serializers.SerializerMethodField()
    content_preview = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    edited_at_display = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()
    spoiler_for = serializers.SerializerMethodField()

    class Meta:
        model = Post
        list_serializer_class = PostListSerializer
        fields = [
            "id",
            "author",
            "author_username",
            "author_display_name",
            "author_avatar",
            "author_is_premium",
            "title",
            "text",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "anime",
            "anime_title",
            "anime_poster",
            "anime_rating",
            "playlist",
            "playlist_title",
            "group",
            "group_name",
            "group_avatar",
            "reactor_post",
            "post_type",
            "original_post",
            "original_post_data",
            "repost_comment",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "shares_count",
            "is_liked",
            "is_disliked",
            "is_favorited",
            "is_bookmarked",
            "is_following",
            "is_pinned",
            "is_deleted",
            "allow_comments",
            "status",
            "visibility",
            "is_spoiler",
            "spoiler_for",
            "spoiler_description",
            "media_files",
            "attachments_data",
            "content_preview",
            "media_url",
            "hashtags",
            "created_at",
            "updated_at",
            "edited_at",
            "edited_at_display",
            "published_at",
            "can_edit",
            "can_delete",
        ]
        read_only_fields = [
            "id",
            "author",
            "created_at",
            "updated_at",
            "likes_count",
            "published_at",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "shares_count",
        ]

    def get_group(self, obj):
        if not obj.group:
            return None

        try:
            return {
                "id": obj.group.id,
                "name": obj.group.name or "",
                "avatar": obj.group.avatar_file.url if obj.group.avatar_file else None,
            }
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting group for post {obj.id}: {e}")
            return None

    def get_anime(self, obj):
        return post_anime(obj, self.context)


    def get_playlist(self, obj):
        value = self.context.get('post_contents', {}).get('playlist', {}).get(obj.playlist_id, obj.playlist)
        return playlist_card(value, self.context.get('request')) if value else None


    def get_reactor_post(self, obj):
        return reactor_card(obj.reactor_post, self.context.get('request')) if obj.reactor_post else None


    def get_is_liked(self, obj):
        if hasattr(obj, 'viewer_liked'): return obj.viewer_liked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_disliked(self, obj):
        if hasattr(obj, 'viewer_disliked'): return obj.viewer_disliked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.dislikes.filter(user=request.user).exists()
        return False

    def get_is_favorited(self, obj):
        if hasattr(obj, 'viewer_favorited'): return obj.viewer_favorited
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            return False
        favs = getattr(obj, "favorites", None)
        if favs is None:
            return False
        try:
            return favs.filter(user=request.user).exists()
        except Exception:
            return False

    def get_is_bookmarked(self, obj):
        if hasattr(obj, 'viewer_bookmarked'): return obj.viewer_bookmarked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False

    def get_is_following(self, obj):
        if hasattr(obj, 'viewer_following'): return obj.viewer_following
        request = self.context.get("request")
        if request and request.user.is_authenticated and obj.author:
            return obj.author.following.filter(follower=request.user).exists()
        return False

    def get_original_post_data(self, obj):
        depth = self.context.get('repost_depth', 0)
        if depth >= 2: return None
        source = original_post(obj, self.context)
        if source is None: return None
        cache = self.context.setdefault('serialized_originals', {})
        key = ('post', source.pk, depth)
        if key not in cache:
            cache[key] = PostSerializer(source, context={**self.context, 'repost_depth': depth+1}).data
        return cache[key]

    def get_media_files(self, obj):
        try:
            media = [item for item in obj.media_files.all() if item.is_active] if hasattr(obj, "media_files") else []
            return PostMediaSerializer(media, many=True, context=self.context).data
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(f"Error serializing media files for post {obj.id}: {e}")
            return []

    def get_attachments_data(self, obj):
        try:
            if hasattr(obj, '_prefetched_objects_cache') and 'attachments' in obj._prefetched_objects_cache:
                attachments = obj.attachments.all()
            elif hasattr(obj, 'attachments'):
                attachments = obj.attachments.all()
            else:
                from apps.social.infrastructure.models.social import PostAttachment
                attachments = PostAttachment.objects.filter(post_id=obj.id)
            
            import logging
            logger = logging.getLogger(__name__)
            attachments_list = list(attachments)

            result = PostAttachmentSerializer(
                attachments_list, many=True, context=self.context
            ).data
            
            return result
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error getting attachments for post {obj.id}: {e}")
            return []

    def get_content_preview(self, obj):
        text = obj.text or ""
        if len(text) > 200:
            return text[:200] + "..."
        return text

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request and request.user == obj.author:
            from django.utils import timezone
            from datetime import timedelta

            return (timezone.now() - obj.created_at) < timedelta(minutes=5)
        return False

    def get_can_delete(self, obj):
        request = self.context.get("request")
        if request and (request.user == obj.author or request.user.is_staff):
            return True
        return False

    def get_hashtags(self, obj):
        if hasattr(obj, "hashtag_links"):
            return [link.hashtag.name for link in obj.hashtag_links.all()]
        return []

    def get_spoiler_for(self, obj):
        if obj.spoiler_for:
            return {
                "id": obj.spoiler_for.id,
                "title_ru": obj.spoiler_for.title_ru,
                "title_en": obj.spoiler_for.title_en,
            }
        return None

    def get_edited_at_display(self, obj):
        if obj.edited_at:
            from django.utils import timezone

            delta = timezone.now() - obj.edited_at
            if delta.days > 1:
                return f"(изменено {obj.edited_at.strftime('%d.%m.%y')})"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"(изменено {hours}ч назад)"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"(изменено {minutes}м назад)"
            else:
                return "(изменено сейчас)"
        return None


FeedPostSerializer = PostSerializer


def _write_post_attachments(post, values):
    from apps.anime.infrastructure.models.anime import Anime
    from apps.playlists.infrastructure.models.playlists import Playlist
    from apps.reactor.infrastructure.models.reactor import ReactorPost
    ratings = values.pop('anime_ratings', None)
    for field, model, kind, relation in (
        ('anime_ids', Anime, 'anime', 'anime'),
        ('playlist_ids', Playlist, 'playlist', 'playlist'),
        ('reactor_ids', ReactorPost, 'shorts', 'reactor_post'),
    ):
        if field not in values:
            continue
        ids = list(dict.fromkeys(values.pop(field)))
        objects = model.objects.in_bulk(ids)
        if len(objects) != len(ids):
            raise serializers.ValidationError({field: 'Некоторые вложения не найдены'})
        post.attachments.filter(content_type=kind).delete()
        rows = []
        for index, pk in enumerate(ids):
            item = objects[pk]
            metadata = {'title': (item.title_ru or item.title_en) if kind == 'anime' else item.title}
            if kind == 'anime':
                metadata['rating'] = ratings[index] if ratings and index < len(ratings) else None
            rows.append(PostAttachment(post=post, object_id=pk, content_type=kind, metadata=metadata))
        PostAttachment.objects.bulk_create(rows)
        setattr(post, relation + '_id', ids[0] if ids else None)
        if kind == 'anime' and ratings is not None:
            post.anime_rating = ratings[0] if ids and ratings else None
    if 'excerpt_ids' in values:
        from apps.anime.application.excerpts import enable_attachment
        ids = list(dict.fromkeys(values.pop('excerpt_ids')))
        post.attachments.filter(content_type='excerpt').delete()
        for pk in ids:
            enable_attachment(pk, post.author)
            PostAttachment.objects.create(post=post, content_type='excerpt', object_id=pk)
    return values


class PostCreateSerializer(serializers.ModelSerializer):
    excerpt_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), max_length=10, required=False, write_only=True)
    anime_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, write_only=True)
    playlist_ids = serializers.ListField(child=serializers.RegexField(r'^\d{1,8}$'), required=False, write_only=True)
    reactor_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False, write_only=True)
    anime_ratings = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=10, allow_null=True), required=False, write_only=True)

    class Meta:
        model = Post
        fields = ['title', 'text', 'image_url', 'image_file', 'video_url', 'video_file',
                  'anime', 'anime_rating', 'group', 'playlist', 'reactor_post', 'post_type',
                  'original_post', 'repost_comment', 'visibility', 'allow_comments',
                  'is_spoiler', 'spoiler_description', 'spoiler_for', 'anime_ids',
                  'client_post_id', 'playlist_ids', 'reactor_ids', 'anime_ratings', 'excerpt_ids']
        extra_kwargs = {'text': {'max_length': 5000}, 'title': {'max_length': 200},
                        'spoiler_description': {'max_length': 500}}

    def validate_playlist_ids(self, values):
        return [str(value).zfill(8) for value in values]

    def validate(self, data):
        request = self.context.get('request')
        has_files = bool(request and (request.FILES or request.data.get('media_ids') or request.data.get('media_ids[]')))
        content_fields = ('text', 'title', 'anime', 'playlist', 'reactor_post', 'original_post',
                          'anime_ids', 'playlist_ids', 'reactor_ids', 'excerpt_ids', 'image_file', 'video_file',
                          'image_url', 'video_url')
        if not has_files and not any(data.get(field) for field in content_fields):
            raise serializers.ValidationError('Пост должен содержать текст или вложение')
        return data

    def create(self, validated_data):
        lists = {key: validated_data.pop(key) for key in ('anime_ids', 'playlist_ids', 'reactor_ids', 'anime_ratings', 'excerpt_ids') if key in validated_data}
        post = super().create(validated_data)
        _write_post_attachments(post, lists)
        post.save()
        _extract_and_link_hashtags(post, post.text)
        return post


class PostUpdateSerializer(PostCreateSerializer):
    anime_id = serializers.PrimaryKeyRelatedField(source='anime', queryset=Anime.objects.all(), required=False, allow_null=True, write_only=True)
    playlist_id = serializers.PrimaryKeyRelatedField(source='playlist', queryset=Playlist.objects.all(), required=False, allow_null=True, write_only=True)
    attachments_data = serializers.SerializerMethodField(read_only=True)

    class Meta(PostCreateSerializer.Meta):
        fields = ['title', 'text', 'visibility', 'allow_comments', 'is_spoiler',
                  'spoiler_description', 'spoiler_for', 'anime_ids', 'playlist_ids',
                  'reactor_ids', 'anime_ratings', 'anime', 'playlist', 'reactor_post',
                  'anime_id', 'playlist_id', 'attachments_data', 'excerpt_ids']

    def validate(self, data):
        return data

    def update(self, instance, validated_data):
        validated_data = _write_post_attachments(instance, validated_data)
        text_changed = 'text' in validated_data
        for name, value in validated_data.items():
            setattr(instance, name, value)
        instance.save()
        if text_changed:
            instance.hashtag_links.all().delete()
            _extract_and_link_hashtags(instance, instance.text)
        instance._prefetched_objects_cache = {}
        return instance

    def get_attachments_data(self, obj):
        return PostAttachmentSerializer(obj.attachments.all(), many=True, context=self.context).data


class PostMediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    media_type_display = serializers.CharField(
        source="get_media_type_display", read_only=True
    )

    class Meta:
        model = PostMedia
        fields = [
            "id",
            "media_type",
            "media_type_display",
            "file",
            "file_url",
            "url",
            "thumbnail",
            "thumbnail_url",
            "caption",
            "order",
            "width",
            "height",
            "duration",
            "file_size",
            "mime_type",
        ]
        read_only_fields = ["id", "file_size", "mime_type"]

    def _make_absolute(self, path_or_url):
        if not path_or_url:
            return None
        request = self.context.get("request")
        if (
            request
            and hasattr(path_or_url, "startswith")
            and path_or_url.startswith("/")
        ):
            return request.build_absolute_uri(path_or_url)
        return path_or_url

    def get_file_url(self, obj):
        if obj.file:
            from .post_read import media_url
            return media_url(obj.file.name, self.context.get('request')) if obj.processing_state == 'ready' else None
        return obj.url or None

    def get_url(self, obj):
        return self.get_file_url(obj)

    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            from .post_read import media_url
            return media_url(obj.thumbnail.name, self.context.get('request'))
        return None

    def to_representation(self, instance):
        from .post_read import media_url
        data = super().to_representation(instance)
        data['id'] = str(instance.pk)
        data['file'] = self.get_file_url(instance)
        data['thumbnail'] = self.get_thumbnail_url(instance)
        data['processing_state'] = instance.processing_state
        data['processing_progress'] = 100 if instance.processing_state == 'ready' else instance.processing_progress
        data['processing_error'] = instance.processing_error
        data['upload_id'] = str(instance.upload_id) if instance.upload_id else None
        data['sources'] = [{'quality': quality, 'url': media_url(path, self.context.get('request'))}
                           for quality, path in instance.variants.items() if quality != 'poster']
        return data


class PostAttachmentSerializer(serializers.ModelSerializer):
    content_type_display = serializers.CharField(
        source="get_content_type_display", read_only=True
    )
    anime_data = serializers.SerializerMethodField()
    playlist_data = serializers.SerializerMethodField()
    shorts_data = serializers.SerializerMethodField()
    excerpt_data = serializers.SerializerMethodField()

    def to_representation(self, instance):
        if instance.content_type == 'excerpt':
            from apps.anime.application.excerpts import attachment_data
            return {'id': str(instance.pk), 'content_type': 'excerpt', 'object_id': instance.object_id,
                    'excerpt_data': attachment_data(instance.object_id)}
        from .post_read import content_visible
        from apps.playlists.infrastructure.models.playlists import Playlist
        from apps.reactor.infrastructure.models.reactor import ReactorPost
        model = {'playlist': Playlist, 'shorts': ReactorPost}.get(instance.content_type)
        if model and not content_visible(attachment_content(instance, self.context), self.context.get('request')):
            return {'id': str(instance.pk), 'content_type': 'unavailable', 'metadata': {}}
        data = super().to_representation(instance)
        for field in ('id', 'post', 'object_id'): data[field] = str(data[field])
        return data

    class Meta:
        model = PostAttachment
        fields = [
            "id",
            "post",
            "content_type",
            "content_type_display",
            "object_id",
            "metadata",
            "anime_data",
            "playlist_data",
            "shorts_data",
            "excerpt_data",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_anime_data(self, obj):
        if obj.content_type != 'anime': return None
        value = attachment_content(obj, self.context)
        if value is None: return None
        rating = obj.metadata.get('rating') if isinstance(obj.metadata, dict) else None
        return anime_card(value, self.context.get('request'), rating)


    def get_playlist_data(self, obj):
        if obj.content_type != 'playlist': return None
        value = attachment_content(obj, self.context)
        if value is None: return None
        return playlist_card(value, self.context.get('request'))


    def get_excerpt_data(self, obj):
        if obj.content_type != 'excerpt': return None
        from apps.anime.application.excerpts import attachment_data
        return attachment_data(obj.object_id)

    def get_shorts_data(self, obj):
        if obj.content_type != 'shorts': return None
        value = attachment_content(obj, self.context)
        if value is None: return None
        return reactor_card(value, self.context.get('request'))


class MessageSerializer(serializers.ModelSerializer):
    media = serializers.SerializerMethodField()
    topic_id = serializers.IntegerField(required=False, allow_null=True)
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_username = serializers.CharField(source="sender.username", read_only=True)
    sender_avatar = serializers.ImageField(source="sender.avatar", read_only=True)
    sender_nickname = serializers.CharField(source="sender.nickname", read_only=True)
    reply_text = serializers.SerializerMethodField()
    reply_sender_username = serializers.SerializerMethodField()
    reply_to_message = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()
    shared_post_data = serializers.SerializerMethodField()
    shared_anime_title = serializers.CharField(
        source="shared_anime.title_ru", read_only=True
    )
    shared_anime_poster = serializers.ImageField(
        source="shared_anime.poster", read_only=True
    )
    shared_anime_data = serializers.SerializerMethodField()
    shared_playlist_data = serializers.SerializerMethodField()
    shared_shorts_data = serializers.SerializerMethodField()
    pinned_by_username = serializers.CharField(
        source="pinned_by.username", read_only=True
    )
    forwarded_from_data = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()

    is_read_by_other = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    public_id = serializers.IntegerField(read_only=True)
    is_mine = serializers.SerializerMethodField()

    chat_id = serializers.SerializerMethodField()
    chat_type = serializers.SerializerMethodField()
    conversation_id = serializers.IntegerField(read_only=True)
    seq = serializers.IntegerField(read_only=True)
    version = serializers.IntegerField(read_only=True)

    def get_chat_id(self, obj):
        return obj.parent_chat.public_id

    def get_chat_type(self, obj):
        return 'private' if obj.private_chat_id else 'group'

    class Meta:
        model = Message
        fields = [
            "id", "chat_id", "chat_type", "conversation_id", "seq", "version",
            "chat",
            "private_chat",
            "sender",
            "sender_id",
            "sender_username",
            "sender_nickname",
            "sender_avatar",
            "text",
            "topic_id",
            "media",
            "media_type",
            "media_url",
            "location_latitude",
            "location_longitude",
            "location_name",
            "shared_post",
            "shared_post_data",
            "shared_anime",
            "shared_anime_title",
            "shared_anime_poster",
            "shared_anime_data",
            "shared_playlist",
            "shared_playlist_data",
            "shared_shorts",
            "shared_shorts_data",
            "reply_to",
            "reply_text",
            "reply_sender_username",
            "reply_to_message",
            "is_edited",
            "edited_at",
            "is_deleted",
            "deleted_at",
            "deleted_by",
            "is_pinned",
            "pinned_by",
            "pinned_by_username",
            "pinned_at",
            "forwarded_from",
            "forwarded_from_data",
            "reactions",
            "message_type",
            "system_action",
            "system_target_user",
            "attachments",
            "created_at",
            "updated_at",
            "is_read_by_other",
            "read_count",
            "public_id",
            "client_message_id",
            "is_mine",
        ]
        read_only_fields = [
            "id",
            "sender", "chat", "private_chat", "reactions",
            "is_edited",
            "edited_at",
            "is_deleted",
            "deleted_at",
            "deleted_by",
            "is_pinned",
            "pinned_by",
            "pinned_at",
            "forwarded_from",
            "created_at",
            "updated_at",
            "message_type",
            "system_action",
            "system_target_user",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.message_type == 'system' and instance.system_action in ('block', 'unblock'):
            action = 'заблокировал(а)' if instance.system_action == 'block' else 'разблокировал(а)'
            data['text'] = instance.text or f'{instance.sender.username} {action} пользователя'
        return data

    def get_is_read_by_other(self, obj):
        request = self.context.get("request")
        if not request or not getattr(request, 'user', None) or not request.user.is_authenticated:
            return False

        if obj.sender_id != request.user.id:
            return False

        prefetched = getattr(obj, "_prefetched_objects_cache", {}).get("read_statuses")
        if prefetched is not None:
            read_user_ids = {status.user_id for status in prefetched}
            if obj.private_chat_id:
                other_user_id = (
                    obj.private_chat.user2_id
                    if obj.private_chat.user1_id == request.user.id
                    else obj.private_chat.user1_id
                )
                return other_user_id in read_user_ids
            return any(uid != request.user.id for uid in read_user_ids)

        if obj.private_chat_id:
            other_user_id = (
                obj.private_chat.user2_id
                if obj.private_chat.user1_id == request.user.id
                else obj.private_chat.user1_id
            )
            return MessageReadStatus.objects.filter(
                message_id=obj.id, user_id=other_user_id
            ).exists()
        if obj.chat_id:
            return (
                MessageReadStatus.objects.filter(message_id=obj.id)
                .exclude(user_id=request.user.id)
                .exists()
            )
        return False

    def get_read_count(self, obj):
        if obj.chat_id:
            return sum(r.user_id != obj.sender_id for r in obj.read_statuses.all())
        return 0

    def get_is_mine(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.sender_id == request.user.id

    def get_media_url(self, obj):
        return private_file_url(obj.media, self.context.get('request'))

    get_media = get_media_url

    def visible_reply(self, obj):
        if not obj.reply_to_id or obj.reply_to.is_deleted or obj.reply_to.conversation_id != obj.conversation_id:
            return None
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            cache = self.context.setdefault('_visible_replies', {})
            key = (request.user.pk, obj.reply_to_id)
            if key not in cache:
                from apps.social.application.conversations import visible_messages
                cache[key] = visible_messages(obj.parent_chat, request.user).filter(pk=obj.reply_to_id).exists()
            if not cache[key]:
                return None
        return obj.reply_to

    def get_reply_text(self, obj):
        reply = self.visible_reply(obj)
        return reply.text if reply else None

    def get_reply_sender_username(self, obj):
        reply = self.visible_reply(obj)
        return reply.sender.username if reply else None

    def get_reply_to_message(self, obj):
        if self.visible_reply(obj):
            reply_sender_avatar = None
            if obj.reply_to.sender.avatar:
                try:
                    reply_sender_avatar = obj.reply_to.sender.avatar.url
                    request = self.context.get("request")
                    if (
                        request
                        and reply_sender_avatar
                        and not reply_sender_avatar.startswith("http")
                    ):
                        reply_sender_avatar = request.build_absolute_uri(
                            reply_sender_avatar
                        )
                except Exception:
                    pass

            reply_media = None
            if obj.reply_to.media:
                try:
                    reply_media = private_file_url(obj.reply_to.media, self.context.get('request'))
                    request = self.context.get("request")
                    if request and reply_media and not reply_media.startswith("http"):
                        reply_media = request.build_absolute_uri(reply_media)
                except Exception:
                    pass

            return {
                "id": obj.reply_to.id,
                "topic_id": obj.reply_to.topic_id,
                "topic_slug": obj.reply_to.topic.slug if obj.reply_to.topic_id else 'general',
                "text": obj.reply_to.text,
                "sender_id": obj.reply_to.sender.id,
                "sender_username": obj.reply_to.sender.username,
                "sender_avatar": reply_sender_avatar,
                "media": reply_media,
                "media_type": obj.reply_to.media_type,
                "created_at": serializers.DateTimeField().to_representation(obj.reply_to.created_at),
            }
        return None

    def get_forwarded_from_data(self, obj):
        if obj.forwarded_from:
            return {
                "id": obj.forwarded_from.id,
                "text": obj.text,
                "sender": UserSimpleSerializer(obj.forwarded_from.sender).data,
                "media_type": obj.media_type,
                "media_url": private_file_url(obj.media, self.context.get("request")),
            }
        return None

    def get_attachments(self, obj):
        prefetched = getattr(obj, '_prefetched_objects_cache', {}).get('attachments')
        if prefetched is not None:
            file_attachments = prefetched
        else:
            file_attachments = obj.attachments.all()
        attachments_data = AttachmentSerializer(file_attachments, many=True, context=self.context).data
        
        content_attachments = obj.content_attachments.all()

        for ca in content_attachments:
            attachment_data = {
                'id': ca.id,
                'type': ca.content_type,
                'object_id': ca.object_id,
                'data': None,
            }
            
            if ca.content_type == 'excerpt':
                from apps.anime.application.excerpts import attachment_data as excerpt_attachment_data
                attachment_data_value = excerpt_attachment_data(ca.object_id)
                attachments_data.append({**attachment_data, 'data': attachment_data_value or {'id': ca.object_id, 'unavailable': True}})
                continue
            if ca.content_type == 'anime':
                from apps.anime.infrastructure.models.anime import Anime
                try:
                    anime = Anime.objects.get(id=ca.object_id)
                    if not self._shared_visible(anime):
                        continue
                    attachment_data['data'] = {
                        'id': anime.id,
                        'title_ru': anime.title_ru,
                        'title_en': anime.title_en,
                        'poster_url': anime.poster.url if anime.poster else anime.poster_url,
                        'kind': anime.kind,
                        'year': anime.year,
                    }
                except Anime.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'playlist':
                from apps.playlists.infrastructure.models.playlists import Playlist
                try:
                    playlist = Playlist.objects.get(id=ca.object_id)
                    if not self._shared_visible(playlist):
                        continue
                    items = playlist.items.select_related('anime')[:4]
                    posters = []
                    for item in items:
                        if item.anime:
                            poster = item.anime.poster.url if item.anime.poster else item.anime.poster_url
                            if poster:
                                posters.append(poster)
                    
                    attachment_data['data'] = {
                        'id': playlist.id,
                        'title': playlist.title,
                        'description': playlist.description,
                        'poster_url': posters[0] if posters else None,
                        'posters': posters,
                        'items_count': playlist.items.count(),
                        'user': {
                            'id': playlist.user.id,
                            'username': playlist.user.username,
                        } if playlist.user else None,
                    }
                except Playlist.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'shorts':
                from apps.reactor.infrastructure.models.reactor import ReactorPost
                try:
                    shorts = ReactorPost.objects.get(id=ca.object_id)
                    if not self._shared_visible(shorts):
                        continue
                    attachment_data['data'] = {
                        'id': shorts.id,
                        'video_url': shorts.video_url,
                        'thumbnail_url': shorts.thumbnail_url,
                        'text': shorts.text,
                        'author': {
                            'id': shorts.author.id,
                            'username': shorts.author.username,
                            'avatar_url': shorts.author.avatar.url if shorts.author.avatar else None,
                        } if shorts.author else None,
                        'anime': {
                            'id': shorts.anime.id,
                            'title_ru': shorts.anime.title_ru,
                        } if shorts.anime else None,
                        'likes_count': shorts.likes_count,
                        'views_count': shorts.views_count,
                    }
                except ReactorPost.DoesNotExist:
                    pass
                    
            elif ca.content_type == 'post':
                try:
                    post = Post.objects.get(id=ca.object_id)
                    if not self._shared_visible(post):
                        continue
                    attachment_data['data'] = {
                        'id': post.id,
                        'text': post.text[:200],
                        'author': {
                            'id': post.author.id,
                            'username': post.author.username,
                            'avatar_url': post.author.avatar.url if post.author.avatar else None,
                        } if post.author else None,
                        'likes_count': post.likes_count,
                        'comments_count': post.comments_count,
                    }
                except Post.DoesNotExist:
                    pass
            
            if attachment_data['data']:
                attachments_data.append(attachment_data)
        
        return attachments_data

    def get_shared_anime_data(self, obj):
        if obj.shared_anime and self._shared_visible(obj.shared_anime):
            return {
                "id": obj.shared_anime.id,
                "title_ru": obj.shared_anime.title_ru,
                "title_en": obj.shared_anime.title_en,
                "poster_url": obj.shared_anime.poster.url
                if obj.shared_anime.poster
                else obj.shared_anime.poster_url,
                "kind": obj.shared_anime.kind,
                "year": obj.shared_anime.year,
            }
        return None

    def get_shared_playlist_data(self, obj):
        if obj.shared_playlist and self._shared_visible(obj.shared_playlist):
            items = (
                obj.shared_playlist.items.select_related("anime")[:4]
                if hasattr(obj.shared_playlist, "items")
                else []
            )
            posters = []
            for item in items:
                if item.anime:
                    poster = (
                        item.anime.poster.url
                        if item.anime.poster
                        else item.anime.poster_url
                    )
                    if poster:
                        posters.append(poster)

            return {
                "id": obj.shared_playlist.id,
                "title": obj.shared_playlist.title,
                "description": obj.shared_playlist.description,
                "poster_url": posters[0] if posters else None,
                "posters": posters,
                "items_count": len(items),
                "user": {
                    "id": obj.shared_playlist.user.id,
                    "username": obj.shared_playlist.user.username,
                }
                if obj.shared_playlist.user
                else None,
            }
        return None

    def get_shared_shorts_data(self, obj):
        if obj.shared_shorts and self._shared_visible(obj.shared_shorts):
            return {
                "id": obj.shared_shorts.id,
                "video_url": obj.shared_shorts.video_url,
                "thumbnail_url": obj.shared_shorts.thumbnail_url,
                "text": obj.shared_shorts.text,
                "author": {
                    "id": obj.shared_shorts.author.id,
                    "username": obj.shared_shorts.author.username,
                    "avatar_url": obj.shared_shorts.author.avatar.url
                    if obj.shared_shorts.author.avatar
                    else None,
                }
                if obj.shared_shorts.author
                else None,
                "anime": {
                    "id": obj.shared_shorts.anime.id,
                    "title_ru": obj.shared_shorts.anime.title_ru,
                }
                if obj.shared_shorts.anime
                else None,
                "likes_count": obj.shared_shorts.likes_count,
                "views_count": obj.shared_shorts.views_count,
            }
        return None

    def _shared_visible(self, content):
        from apps.social.application.conversations import check_shareable
        from rest_framework.exceptions import APIException
        try:
            check_shareable(content, getattr(self.context.get('request'), 'user', None))
            return True
        except APIException:
            return False

    def get_shared_post_data(self, obj):
        return PostSerializer(obj.shared_post, context=self.context).data if obj.shared_post and self._shared_visible(obj.shared_post) else None

    def validate(self, data):
        text = data.get("text", "").strip()
        media = data.get("media")
        location_latitude = data.get("location_latitude")
        shared_post = data.get("shared_post")
        shared_anime = data.get("shared_anime")
        shared_playlist = data.get("shared_playlist")
        shared_shorts = data.get("shared_shorts")

        request = self.context.get("request")
        has_attachments = False
        if request and hasattr(request.data, 'getlist'):
            anime_ids = request.data.getlist('anime_ids[]') or request.data.getlist('anime_ids')
            playlist_ids = request.data.getlist('playlist_ids[]') or request.data.getlist('playlist_ids')
            reactor_ids = request.data.getlist('reactor_ids[]') or request.data.getlist('reactor_ids')
            excerpt_ids = request.data.getlist('excerpt_ids[]') or request.data.getlist('excerpt_ids')
            has_attachments = bool(anime_ids or playlist_ids or reactor_ids or excerpt_ids)
        else:
            payload = request.data if request else self.initial_data
            has_attachments = (
                payload.get('anime_ids[]') or payload.get('anime_ids') or
                payload.get('playlist_ids[]') or payload.get('playlist_ids') or
                payload.get('reactor_ids') or payload.get('excerpt_ids') or payload.get('excerpt_ids[]')
            )

        has_media_files = False
        if request and hasattr(request, 'FILES'):
            for key in request.FILES.keys():
                if key.startswith('media_'):
                    has_media_files = True
                    break

        if not any(
            [
                text,
                media,
                has_media_files,  
                location_latitude,
                shared_post,
                shared_anime,
                shared_playlist,
                shared_shorts,
                has_attachments,
            ]
        ):
            raise serializers.ValidationError(
                "Сообщение должно содержать текст, медиафайл, геолокацию, пост, аниме, плейлист или шортс"
            )

        return data


class ContestSerializer(serializers.ModelSerializer):
    organizer_username = serializers.CharField(
        source="organizer.username", read_only=True
    )
    anime_title = serializers.CharField(source="anime.title_ru", read_only=True)

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "description",
            "type",
            "format",
            "status",
            "theme",
            "rules",
            "prize_1st",
            "prize_2nd",
            "prize_3rd",
            "announced_at",
            "started_at",
            "voting_started_at",
            "ended_at",
            "organizer",
            "organizer_username",
            "anime",
            "anime_title",
            "entries_count",
            "votes_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organizer",
            "entries_count",
            "votes_count",
            "created_at",
            "updated_at",
        ]


class ContestEntrySerializer(serializers.ModelSerializer):
    participant_username = serializers.CharField(
        source="participant.username", read_only=True
    )
    participant_avatar = serializers.ImageField(
        source="participant.avatar", read_only=True
    )
    contest_title = serializers.CharField(source="contest.title", read_only=True)

    class Meta:
        model = ContestEntry
        fields = [
            "id",
            "contest",
            "contest_title",
            "participant",
            "participant_username",
            "participant_avatar",
            "title",
            "description",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "votes_count",
            "is_winner",
            "winner_place",
            "submitted_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "participant",
            "votes_count",
            "is_winner",
            "winner_place",
            "submitted_at",
            "updated_at",
        ]


class ContestVoteSerializer(serializers.ModelSerializer):
    voter_username = serializers.CharField(source="voter.username", read_only=True)

    class Meta:
        model = ContestVote
        fields = [
            "id",
            "contest",
            "entry",
            "voter",
            "voter_username",
            "vote_type",
            "value",
            "created_at",
        ]
        read_only_fields = ["id", "voter", "created_at"]


class ChatSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSettings
        fields = [
            "id",
            "user",
            "chat",
            "notifications_enabled",
            "sound_enabled",
            "auto_repeat_enabled",
            "repeat_interval",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "chat", "created_at", "updated_at"]


class UserSimpleSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    last_seen = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar_url",
            "is_online",
            "last_seen",
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        
        from django.conf import settings
        from pathlib import Path
        request = self.context.get("request")
        jpg_names = getattr(request, '_chat_default_avatar_names', None)
        if jpg_names is None:
            def_ava_dir = Path(settings.MEDIA_ROOT) / "def_avatars"
            jpg_names = ([path.name for pattern in ('*.jpg', '*.jpeg')
                          for path in def_ava_dir.glob(pattern)]
                         if def_ava_dir.exists() else [])
            if request is not None:
                request._chat_default_avatar_names = jpg_names
        if jpg_names:
            return f"{settings.MEDIA_URL}def_avatars/{jpg_names[obj.id % len(jpg_names)]}"
        
        return None

    def get_is_online(self, obj):
        from core.online_status import online_status
        if hasattr(obj, '_list_online_data'):
            return bool(obj._list_online_data)
        return online_status.is_online(obj.id)

    def get_last_seen(self, obj):
        from core.online_status import online_status
        if hasattr(obj, '_list_online_data'):
            return obj._list_online_data.get('last_seen') if obj._list_online_data else None
        user_data = online_status.get_user_data(obj.id)
        if user_data:
            return user_data.get("last_seen")
        return None


class ChatRoleSerializer(serializers.ModelSerializer):
    chat = serializers.ReadOnlyField(source='chat.public_id')

    class Meta:
        model = ChatRole
        fields = "__all__"
        read_only_fields = ["id", "chat", "created_at", "created_by"]
        validators = []

    def validate(self, data):
        chat = self.context['view'].parent_chat()
        level = data.get('level', getattr(self.instance, 'level', 0))
        if level >= 3:
            raise serializers.ValidationError({'level': 'Владение передаётся отдельно'})
        name = data.get('name', getattr(self.instance, 'name', ''))
        roles = ChatRole.objects.filter(chat=chat, name=name)
        if self.instance:
            roles = roles.exclude(pk=self.instance.pk)
        if roles.exists():
            raise serializers.ValidationError({'name': 'Роль с таким именем уже существует'})
        return data


class ChatMemberSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    role = ChatRoleSerializer(read_only=True)
    effective_permissions = serializers.JSONField(read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = ChatMember
        fields = "__all__"
        read_only_fields = ["joined_at"]

    def get_is_owner(self, obj):
        return obj.is_owner


class GroupChatCreateSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False, default=list
    )
    avatar = serializers.ImageField(required=False, allow_null=True)
    anime = serializers.PrimaryKeyRelatedField(
        queryset=None, required=False, allow_null=True, read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'anime' in self.fields:
            from apps.anime.infrastructure.models.anime import Anime
            self.fields['anime'].queryset = Anime.objects.all()

    class Meta:
        model = GroupChat
        fields = ["name", "description", "avatar", "participants", "anime", "is_public"]

    def validate_participants(self, value):
        value = sorted(set(value) - {self.context['request'].user.pk})
        if len(value) > 199 or User.objects.filter(pk__in=value, is_active=True).count() != len(value):
            raise serializers.ValidationError('Укажите до 199 существующих пользователей')
        return value

    def update(self, instance, validated_data):
        from apps.social.application.chat_services import PermissionChecker
        if not PermissionChecker(self.context['request'].user, instance).has_permission('can_change_chat_info').allowed:
            raise serializers.ValidationError('Недостаточно прав для изменения группы')
        participants = validated_data.pop("participants", None)
        avatar_provided = "avatar" in validated_data
        avatar = validated_data.pop("avatar", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if avatar is not None:
            instance.avatar.save(avatar.name, avatar, save=True)
        elif avatar_provided:
            instance.avatar.delete(save=True)

        instance.save()

        ChatAdminLog.objects.create(
            chat=instance,
            user=self.context["request"].user,
            action="chat_updated",
            details={"updated_fields": list(validated_data.keys())},
        )

        return instance

    def create(self, validated_data):
        participants = validated_data.pop("participants", [])
        avatar = validated_data.pop("avatar", None)

        chat = GroupChat.objects.create(**validated_data)

        if avatar:
            chat.avatar = avatar
            chat.save(update_fields=["avatar"])
        else:
            try:
                self._generate_default_avatar(chat)
            except Exception as e:
                logger.info(f"DEBUG: Ошибка генерации аватарки: {e}")

        ChatMember.objects.create(
            user=self.context["request"].user, chat=chat, is_admin=True
        )

        for user_id in participants:
            try:
                user = User.objects.get(id=user_id)
                ChatMember.objects.create(
                    user=user,
                    chat=chat,
                    can_send_messages=True,
                    can_send_media=chat.can_send_media,
                )
            except User.DoesNotExist:
                continue

        ChatAdminLog.objects.create(
            chat=chat,
            user=self.context["request"].user,
            action="chat_created",
            details={
                "chat_name": chat.name,
                "participants_count": len(participants) + 1,
            },
        )

        return chat

    def _generate_default_avatar(self, chat):
        from PIL import Image, ImageDraw, ImageFont
        import io
        import random

        words = chat.name.split()
        initials = []
        for word in words:
            if len(word) > 2:
                first_letter = word[0].upper()
                if first_letter.isalpha():
                    initials.append(first_letter)
                    if len(initials) == 2:
                        break

        if not initials:
            initials = ["?"]

        hue = random.randint(0, 270)
        saturation = random.randint(60, 100)
        value = random.randint(50, 80)

        import colorsys

        r, g, b = colorsys.hsv_to_rgb(hue / 360, saturation / 100, value / 100)
        bg_color = (int(r * 255), int(g * 255), int(b * 255))

        img = Image.new("RGB", (200, 200), bg_color)
        draw = ImageDraw.Draw(img)

        text = "".join(initials)[:2]  

        try:
            font = ImageFont.truetype("arial.ttf", 80)
        except Exception:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 80
                )
            except Exception:
                font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (200 - text_width) // 2
        y = (200 - text_height) // 2

        draw.text((x, y), text, fill=(255, 255, 255), font=font)

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        from django.core.files.uploadedfile import InMemoryUploadedFile

        avatar_file = InMemoryUploadedFile(
            buffer,
            None,
            f"{chat.id}_avatar.png",
            "image/png",
            buffer.getbuffer().nbytes,
            None,
        )
        chat.avatar.save(f"{chat.id}_avatar.png", avatar_file)
        chat.save(update_fields=["avatar"])


class GroupChatSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="public_id", read_only=True)
    created_by = UserSimpleSerializer(read_only=True)
    members_count = serializers.IntegerField(source="members.count", read_only=True)
    online_count = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_permissions = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    user_member_settings = serializers.SerializerMethodField()
    participants_usernames = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    anime_id = serializers.SerializerMethodField()
    anime_title = serializers.SerializerMethodField()
    anime_poster = serializers.SerializerMethodField()
    anime_slug = serializers.SerializerMethodField()  
    franchise_id = serializers.SerializerMethodField()
    franchise_slug = serializers.SerializerMethodField()  
    discussion_type = (
        serializers.SerializerMethodField()
    )
    code = serializers.CharField()

    class Meta:
        model = GroupChat
        fields = "__all__"
        read_only_fields = ["created_at", "created_by", "invite_link"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_anime_id(self, obj):
        try:
            if hasattr(obj, "anime_id") and obj.anime_id:
                return obj.anime_id
            if obj.anime:
                return obj.anime.id
        except Exception:
            pass
        return None

    def get_anime_title(self, obj):
        try:
            if obj.anime:
                return obj.anime.title_ru or obj.anime.title_en
        except Exception:
            pass
        return None

    def get_anime_poster(self, obj):
        request = self.context.get("request")

        def _abs(url):
            if url and request and not url.startswith("http"):
                return request.build_absolute_uri(url)
            return url

        try:
            if obj.anime:
                if obj.anime.poster:
                    return _abs(obj.anime.poster.url)
                if obj.anime.poster_url:
                    return obj.anime.poster_url
        except Exception:
            pass

        try:
            if getattr(obj, "franchise_id", None):
                if hasattr(obj, '_list_franchise_poster'):
                    return _abs(obj._list_franchise_poster)
                from apps.anime.infrastructure.models.anime import Anime as AnimeModel
                from django.db.models import Q

                first = (
                    AnimeModel.objects.filter(franchise_id=obj.franchise_id)
                    .filter(Q(poster__isnull=False, poster__gt="") | Q(poster_url__isnull=False, poster_url__gt=""))
                    .order_by("franchise_order", "id")
                    .first()
                )
                if first:
                    if first.poster:
                        return _abs(first.poster.url)
                    if first.poster_url:
                        return first.poster_url
        except Exception:
            pass

        return None

    def get_anime_slug(self, obj):
        try:
            if obj.anime:
                title = obj.anime.title_ru or obj.anime.title_en
                if title:
                    from django.utils.text import slugify

                    return slugify(title)
        except Exception:
            pass
        return None

    def get_franchise_id(self, obj):
        try:
            return getattr(obj, "franchise_id", None)
        except Exception:
            return None

    def get_franchise_slug(self, obj):
        if hasattr(obj, '_list_franchise_name'):
            from django.utils.text import slugify
            return slugify(obj._list_franchise_name) if obj._list_franchise_name else None
        try:
            franchise_id = getattr(obj, "franchise_id", None)
            if franchise_id:
                from apps.anime.infrastructure.models.anime import Franchise

                try:
                    franchise = Franchise.objects.get(id=franchise_id)
                    if franchise.name:
                        from django.utils.text import slugify

                        return slugify(franchise.name)
                except Franchise.DoesNotExist:
                    pass
        except Exception:
            pass
        return None

    def get_discussion_type(self, obj):
        try:
            return getattr(obj, "discussion_type", "") or ""
        except Exception:
            return ""

    def get_participants_usernames(self, obj):
        request = self.context.get('request')
        if obj.has_hidden_members:
            member = self._member(obj)
            if not request or not member or not member.effective_permissions.get('can_manage_chat'):
                return []
        return [member.user.username for member in obj.members.all()]

    def get_online_count(self, obj):
        from core.online_status import online_status
        members = [member for member in obj.members.all() if not member.is_banned]
        missing = [member.user_id for member in members if not hasattr(member.user, '_list_online_data')]
        presence = online_status.get_users_data(missing) if missing else {}
        return sum(bool(getattr(member.user, '_list_online_data', presence.get(member.user_id))) for member in members)

    def _member(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        if 'members' in getattr(obj, '_prefetched_objects_cache', {}):
            return next((member for member in obj.members.all() if member.user_id == request.user.pk), None)
        return obj.members.select_related('role', 'user', 'chat').filter(user=request.user).first()

    def get_user_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                member = self._member(obj)
                if member is None:
                    return None
                return {
                    "is_owner": member.is_owner,
                    "role": ChatRoleSerializer(member.role).data
                    if member.role
                    else None,
                    "custom_title": member.custom_title,
                    "is_admin": member.is_admin,
                }
            except ChatMember.DoesNotExist:
                return None
        return None

    def get_user_permissions(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            try:
                member = self._member(obj)
                if member is None:
                    return {}
                return member.effective_permissions
            except ChatMember.DoesNotExist:
                return {}
        return {}

    def get_user_member_settings(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        member = self._member(obj)
        if not member:
            return None
        from apps.social.infrastructure.models.social_chat import GroupMemberSettings
        try:
            settings = member.personal_settings
        except GroupMemberSettings.DoesNotExist:
            settings = None
        return {'is_pinned': settings.is_pinned if settings else member.is_pinned,
                'is_archived': settings.is_archived if settings else member.is_archived,
                'notifications_enabled': settings.notifications_enabled if settings else True,
                'muted_until': settings.muted_until if settings else None,
                'is_muted': settings.is_muted if settings else False}

    def get_unread_count(self, obj):
        if hasattr(obj, '_list_unread_count'):
            return obj._list_unread_count
        from apps.social.application.conversations import unread_count
        request = self.context.get('request')
        return unread_count(obj, request.user) if request and request.user.is_authenticated else 0

    def get_last_message(self, obj):
        from apps.social.application.conversations import visible_messages
        request = self.context.get('request')
        qs = None if hasattr(obj, '_list_last_message') else (visible_messages(obj, request.user) if request and request.user.is_authenticated else Message.objects.filter(chat=obj, is_deleted=False))
        last_message = obj._list_last_message if hasattr(obj, '_list_last_message') else qs.select_related('sender').order_by('-seq').first()
        if last_message:
            try:
                sender_data = UserSimpleSerializer(last_message.sender, context=self.context).data
            except Exception:
                sender_data = {
                    "id": None,
                    "username": "[удалён]",
                    "display_name": None,
                    "avatar": None,
                }
            return {
                "id": last_message.id,
                "text": last_message.text,
                "sender": sender_data,
                "created_at": last_message.created_at,
                "is_edited": last_message.is_edited,
                "media_type": last_message.media_type,
            }
        return None

    is_blocked = serializers.SerializerMethodField()

    def get_is_blocked(self, obj):
        return {
            "blocked": False,
            "current_user_blocked": False,
            "other_user_blocked": False,
        }


class ChatAdminLogSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    target_user = UserSimpleSerializer(read_only=True)
    action_display = serializers.CharField(source="get_action_display", read_only=True)

    class Meta:
        model = ChatAdminLog
        fields = "__all__"
        read_only_fields = ["created_at"]


class PrivateChatSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    user_settings = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    id = serializers.IntegerField(source="public_id", read_only=True)

    class Meta:
        model = PrivateChat
        fields = [
            "id",
            "code",
            "user1",
            "user2",
            "is_support",
            "created_at",
            "last_message_at",
            "user1_notifications",
            "user2_notifications",
            "user1_muted_until",
            "user2_muted_until",
            "user1_archived",
            "user2_archived",
            "user1_pinned",
            "user2_pinned",
            "user1_blocked",
            "user2_blocked",
            "other_user",
            "user_settings",
            "unread_count",
            "last_message",
            "name",
            "is_blocked",
        ]
        read_only_fields = ["created_at", "last_message_at", "is_support"]

    def get_name(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                if obj.is_support and not (request.user.is_staff or request.user.is_superuser):
                    return "Администратор"
                settings = obj.get_user_settings(request.user)
                other = obj.other_user(request.user)
                if other:
                    return settings.get('custom_name') or other.display_name or other.username
        except Exception as e:
            logger.info(f"Error in get_name: {e}")
        return "Чат"

    def get_other_user(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                other = obj.other_user(request.user)
                if other:
                    return UserSimpleSerializer(other, context=self.context).data
        except Exception as e:
            logger.info(f"Error in get_other_user: {e}")
        return None

    def get_user_settings(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                return obj.get_user_settings(request.user)
        except Exception as e:
            logger.info(f"Error in get_user_settings: {e}")
        return {}

    def get_unread_count(self, obj):
        if hasattr(obj, '_list_unread_count'):
            return obj._list_unread_count
        from apps.social.application.conversations import unread_count
        request = self.context.get('request')
        return unread_count(obj, request.user) if request and request.user.is_authenticated else 0


    def get_last_message(self, obj):
        try:
            from apps.social.application.conversations import visible_messages
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                return None
            last_message = obj._list_last_message if hasattr(obj, '_list_last_message') else visible_messages(obj, request.user).select_related('sender').order_by('-seq').first()
            if last_message:
                return {
                    "id": last_message.id,
                    "text": last_message.text,
                    "sender": UserSimpleSerializer(last_message.sender, context=self.context).data,
                    "created_at": last_message.created_at,
                    "is_edited": last_message.is_edited,
                    "media_type": last_message.media_type,
                }
        except Exception as e:
            logger.info(f"Error in get_last_message: {e}")
        return None

    def get_is_blocked(self, obj):
        try:
            request = self.context.get("request")
            if request and request.user.is_authenticated:
                settings = obj.get_user_settings(request.user)
                other_user = obj.other_user(request.user)
                if other_user:
                    other_settings = obj.get_user_settings(other_user)
                    current_user_blocked = settings.get("is_blocked", False)
                    other_user_blocked = other_settings.get("is_blocked", False)
                    return {
                        "blocked": current_user_blocked or other_user_blocked,
                        "current_user_blocked": current_user_blocked,
                        "other_user_blocked": other_user_blocked,
                    }
        except Exception as e:
            logger.info(f"Error in get_is_blocked: {e}")
        return {"blocked": False, "current_user_blocked": False, "other_user_blocked": False}


class PrivateChatCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source="user2",
        write_only=True,
        required=False,
    )

    class Meta:
        model = PrivateChat
        fields = ["user2", "user_id"]
        extra_kwargs = {"user2": {"required": False}}

    def validate(self, attrs):
        user2 = attrs.get("user2")
        if user2 is None:
            raise serializers.ValidationError(
                {"user2": "Укажите собеседника (user2 или user_id)"}
            )
        request = self.context.get("request")
        if request and request.user == user2:
            raise serializers.ValidationError(
                {"user2": "Нельзя создать чат с самим собой"}
            )
        return attrs

    @staticmethod
    def _generate_unique_code(max_attempts: int = 5) -> str:
        for _ in range(max_attempts):
            code = str(random.randint(10000000, 99999999))
            if not PrivateChat.objects.filter(code=code).exists():
                return code
        raise IntegrityError("Не удалось сгенерировать уникальный код личного чата")

    def create(self, validated_data):
        request = self.context.get("request")
        current_user = request.user
        other = validated_data["user2"]

        if current_user.id <= other.id:
            user1, user2 = current_user, other
        else:
            user1, user2 = other, current_user

        with transaction.atomic():
            User.objects.select_for_update().get(pk=min(user1.pk, user2.pk))
            existing = (
                PrivateChat.objects.select_for_update()
                .filter(user1=user1, user2=user2)
                .first()
            )
            if existing is None:
                existing = (
                    PrivateChat.objects.select_for_update()
                    .filter(user1=user2, user2=user1)
                    .first()
                )
            if existing is not None:
                self._created = False
                if not existing.code:
                    existing.code = self._generate_unique_code()
                    existing.save(update_fields=["code"])
                return existing

            try:
                with transaction.atomic():
                    chat = PrivateChat.objects.create(
                        user1=user1, user2=user2, code=self._generate_unique_code(),
                    )
            except IntegrityError:
                chat = PrivateChat.objects.filter(
                    user1=user1, user2=user2
                ).first()
                if chat is None:
                    raise
                self._created = False
                return chat

        self._created = True
        return chat


class PrivateChatUserSettingsSerializer(serializers.ModelSerializer):
    custom_avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = PrivateChatUserSettings
        fields = [
            "id",
            "chat",
            "custom_name",
            "custom_avatar",
            "custom_avatar_url",
            "notifications_enabled",
            "updated_at",
        ]
        read_only_fields = ["id", "chat", "updated_at"]

    def get_custom_avatar_url(self, obj):
        if obj.custom_avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.custom_avatar.url)
            return obj.custom_avatar.url
        return None

    def create(self, validated_data):
        chat = validated_data.get("chat")
        user = validated_data.get("user")

        if not chat.members.filter(id=user.id).exists():
            if user != chat.user1 and user != chat.user2:
                raise serializers.ValidationError("Вы не участник этого чата")

        settings, created = PrivateChatUserSettings.objects.update_or_create(
            chat=chat, user=user, defaults=validated_data
        )
        return settings


class GroupChatSettingsSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = GroupChat
        fields = ["id", "name", "description", "avatar", "avatar_url"]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def update(self, instance, validated_data):
        avatar = validated_data.pop("avatar", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if avatar:
            instance.avatar.save(avatar.name, avatar, save=True)

        instance.save()

        ChatAdminLog.objects.create(
            chat=instance,
            user=self.context["request"].user,
            action="chat_updated",
            details={"updated_fields": list(validated_data.keys())},
        )

        return instance


class FollowSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(
        source="follower.username", read_only=True
    )
    following_username = serializers.CharField(
        source="following.username", read_only=True
    )
    follower_avatar = serializers.ImageField(source="follower.avatar", read_only=True)
    following_avatar = serializers.ImageField(source="following.avatar", read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "follower_username",
            "follower_avatar",
            "following",
            "following_username",
            "following_avatar",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PostLikeSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = PostLike
        fields = ["id", "user", "username", "avatar", "created_at"]
        read_only_fields = ["id", "created_at"]


class PostDislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostDislike
        fields = ["id", "user", "post", "created_at"]
        read_only_fields = ["id", "created_at"]


class RepostSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)
    user_avatar = serializers.ImageField(source="user.avatar", read_only=True)
    original_post_data = PostSerializer(source="original_post", read_only=True)

    class Meta:
        model = Repost
        fields = [
            "id",
            "user",
            "user_username",
            "user_avatar",
            "original_post",
            "original_post_data",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class AchievementSerializer(serializers.ModelSerializer):
    icon_url = serializers.ImageField(source="icon", read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    level_display = serializers.CharField(source="get_level_display", read_only=True)

    class Meta:
        model = Achievement
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "icon_url",
            "icon_svg",
            "category",
            "category_display",
            "level",
            "level_display",
            "condition_type",
            "condition_value",
            "is_active",
            "unlocked_count",
            "created_at",
        ]


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserAchievement
        fields = [
            "id",
            "user",
            "achievement",
            "progress",
            "progress_percentage",
            "is_unlocked",
            "unlocked_at",
        ]

    def get_progress_percentage(self, obj):
        if obj.achievement.condition_value > 0:
            return min(100, (obj.progress / obj.achievement.condition_value) * 100)
        return 100 if obj.is_unlocked else 0


class UploadedFileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    file_url = serializers.ImageField(source="file", read_only=True)
    thumbnail_url = serializers.ImageField(source="thumbnail", read_only=True)

    class Meta:
        model = UploadedFile
        fields = [
            "id",
            "user",
            "username",
            "file",
            "file_url",
            "file_type",
            "file_name",
            "file_size",
            "mime_type",
            "thumbnail",
            "thumbnail_url",
            "width",
            "height",
            "duration",
            "uploaded_at",
        ]
        read_only_fields = ["id", "uploaded_at"]


class ReactionSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)

    class Meta:
        model = Reaction
        fields = ["id", "message", "user", "emoji", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


class ReactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ["message", "emoji"]

    def validate_emoji(self, value):
        import emoji

        if not emoji.is_emoji(value):
            raise serializers.ValidationError("Неверный формат эмодзи")
        return value

    def validate_message(self, value):
        if value.is_deleted:
            raise serializers.ValidationError(
                "Нельзя реагировать на удаленное сообщение"
            )
        return value

    def create(self, validated_data):
        user = self.context["request"].user
        message = validated_data["message"]
        emoji = validated_data["emoji"]

        existing = Reaction.objects.filter(
            message=message, user=user, emoji=emoji
        ).first()

        if existing:
            existing.delete()
            self._update_message_reactions(message)
            return None

        reaction = Reaction.objects.create(message=message, user=user, emoji=emoji)

        self._update_message_reactions(message)

        return reaction

    def _update_message_reactions(self, message):
        reactions = Reaction.objects.filter(message=message)

        reactions_dict = {}
        for reaction in reactions:
            if reaction.emoji not in reactions_dict:
                reactions_dict[reaction.emoji] = []
            reactions_dict[reaction.emoji].append(reaction.user_id)

        message.reactions = reactions_dict
        message.save(update_fields=["reactions"])


class AttachmentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Attachment
        fields = [
            "id",
            "message",
            "type",
            "type_display",
            "file",
            "file_url",
            "file_name",
            "file_size",
            "mime_type",
            "thumbnail",
            "thumbnail_url",
            "width",
            "height",
            "duration",
            "uploaded_at",
        ]
        read_only_fields = ["id", "file_size", "mime_type", "uploaded_at"]

    def get_file_url(self, obj):
        return private_file_url(obj.file, self.context.get('request'))

    def get_thumbnail_url(self, obj):
        return private_file_url(obj.thumbnail, self.context.get('request'))

    get_file = get_file_url
    get_thumbnail = get_thumbnail_url


class AttachmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["message", "type", "file", "file_name", "width", "height", "duration"]

    def validate_file(self, value):
        max_size = 10 * 1024 * 1024  
        if value.size > max_size:
            raise serializers.ValidationError("Максимальный размер файла - 10 MB")
        return value

    def validate_message(self, value):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            if value.sender != request.user:
                raise serializers.ValidationError(
                    "Вы можете добавлять вложения только к своим сообщениям"
                )

            if value.chat and not value.chat.can_send_media:
                raise serializers.ValidationError(
                    "В этом чате нельзя отправлять медиафайлы"
                )

        return value

    def create(self, validated_data):
        file = validated_data["file"]
        validated_data["file_size"] = file.size
        validated_data["mime_type"] = file.content_type

        attachment = super().create(validated_data)

        if attachment.type == "image":
            self._create_thumbnail(attachment)

        return attachment

    def _create_thumbnail(self, attachment):
        from PIL import Image
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile

        try:
            img = Image.open(attachment.file)

            img.thumbnail((200, 200), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            thumbnail_file = InMemoryUploadedFile(
                buffer,
                None,
                f"{attachment.id}_thumb.jpg",
                "image/jpeg",
                buffer.getbuffer().nbytes,
                None,
            )
            attachment.thumbnail.save(f"{attachment.id}_thumb.jpg", thumbnail_file)
            attachment.save(update_fields=["thumbnail"])
        except Exception as e:
            logger.info(f"Ошибка создания миниатюры: {e}")


class EmailLogSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    email_type_display = serializers.CharField(
        source="get_email_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EmailLog
        fields = [
            "id",
            "user",
            "email_type",
            "email_type_display",
            "subject",
            "to_email",
            "content",
            "status",
            "status_display",
            "sent_at",
            "error_message",
            "chat_id",
            "message_id",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class EmailLogCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = [
            "user",
            "email_type",
            "subject",
            "to_email",
            "content",
            "chat_id",
            "message_id",
            "metadata",
        ]

    def create(self, validated_data):
        email_log = EmailLog.objects.create(**validated_data)


        return email_log


class ChatFolderChatSerializer(serializers.ModelSerializer):
    chat_name = serializers.SerializerMethodField()
    chat_avatar = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolderChat
        fields = ["id", "chat_id", "chat_type", "chat_name", "chat_avatar", "added_at"]

    def get_chat_name(self, obj):
        if obj.chat_type == "group":
            from apps.social.infrastructure.models.social import GroupChat

            chat = GroupChat.objects.filter(id=obj.chat_id).first()
            return chat.name if chat else "Чат"
        else:
            from apps.social.infrastructure.models.social import PrivateChat

            chat = PrivateChat.objects.filter(id=obj.chat_id).first()
            if chat:
                request = self.context.get("request")
                if request and request.user.is_authenticated:
                    other = chat.other_user(request.user)
                    return other.display_name or other.username if other else "Чат"
            return "Чат"

    def get_chat_avatar(self, obj):
        if obj.chat_type == "group":
            from apps.social.infrastructure.models.social import GroupChat

            chat = GroupChat.objects.filter(id=obj.chat_id).first()
            if chat and chat.avatar:
                request = self.context.get("request")
                if request:
                    return request.build_absolute_uri(chat.avatar.url)
                return chat.avatar.url
        else:
            from apps.social.infrastructure.models.social import PrivateChat

            chat = PrivateChat.objects.filter(id=obj.chat_id).first()
            if chat:
                request = self.context.get("request")
                if request and request.user.is_authenticated:
                    other = chat.other_user(request.user)
                    if other and other.avatar:
                        if request:
                            return request.build_absolute_uri(other.avatar.url)
                        return other.avatar.url
        return None


class ChatFolderSerializer(serializers.ModelSerializer):
    chats = ChatFolderChatSerializer(many=True, read_only=True)
    chats_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolder
        fields = [
            "id",
            "name",
            "icon",
            "color",
            "position",
            "include_private",
            "include_groups",
            "include_archived",
            "include_pinned",
            "is_system",
            "chats",
            "chats_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]

    def get_chats_count(self, obj):
        return obj.chats.count()


class ChatFolderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatFolder
        fields = [
            "name",
            "icon",
            "color",
            "position",
            "include_private",
            "include_groups",
            "include_archived",
            "include_pinned",
        ]

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ChatFolderPreviewSerializer(serializers.ModelSerializer):
    chats_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolder
        fields = ["id", "name", "icon", "color", "position", "is_system", "chats_count"]

    def get_chats_count(self, obj):
        return obj.chats.count()




class PostCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(source="author.display_name", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    replies_count = serializers.SerializerMethodField()
    parent_id = serializers.CharField(source="parent.id", read_only=True)
    parent_username = serializers.CharField(
        source="parent.author.username", read_only=True
    )
    reply_to = serializers.SerializerMethodField()
    is_reply = serializers.SerializerMethodField()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        for field in ('id', 'post', 'parent'):
            if data.get(field) is not None: data[field] = str(data[field])
        return data

    class Meta:
        model = PostComment
        fields = [
            "id",
            "post",
            "author",
            "author_username",
            "author_display_name",
            "author_avatar",
            "author_is_premium",
            "parent",
            "parent_id",
            "parent_username",
            "content",
            "is_edited",
            "is_deleted",
            "deleted_at",
            "likes_count",
            "dislikes_count",
            "replies_count",
            "path",
            "level",
            "created_at",
            "updated_at",
            "is_liked",
            "is_disliked",
            "reply_to",
            "is_reply",
        ]
        read_only_fields = [
            "id",
            "post",
            "author",
            "created_at",
            "updated_at",
            "is_edited",
        ]

    def get_is_liked(self, obj):
        if hasattr(obj, 'viewer_liked'): return obj.viewer_liked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from apps.social.infrastructure.models.social import PostCommentLike

            if hasattr(obj, 'user_liked'): return obj.user_liked
            return PostCommentLike.objects.filter(
                user=request.user, comment=obj
            ).exists()
        return False

    def get_is_disliked(self, obj):
        if hasattr(obj, 'viewer_disliked'): return obj.viewer_disliked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            from apps.social.infrastructure.models.social import PostCommentDislike

            if hasattr(obj, 'user_disliked'): return obj.user_disliked
            return PostCommentDislike.objects.filter(
                user=request.user, comment=obj
            ).exists()
        return False

    def get_replies_count(self, obj):
        return obj.visible_replies if hasattr(obj, 'visible_replies') else obj.replies.filter(is_deleted=False).count()

    def get_reply_to(self, obj):
        if obj.parent:
            return {
                "id": obj.parent.id,
                "author_id": obj.parent.author.id,
                "author_username": obj.parent.author.username,
                "author_avatar": obj.parent.author.avatar.url
                if obj.parent.author.avatar
                else None,
                "text": obj.parent.content,
                "created_at": obj.parent.created_at.isoformat(),
            }
        return None

    def get_is_reply(self, obj):
        return obj.parent is not None


class PostCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ["parent", "content"]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Комментарий не может быть пустым")
        if len(value) > 2000:
            raise serializers.ValidationError(
                "Максимальная длина комментария - 2000 символов"
            )
        return value.strip()

    def validate(self, data):
        parent = data.get("parent")

        if parent:
            if parent.is_deleted:
                raise serializers.ValidationError(
                    "Нельзя отвечать на удалённый комментарий"
                )

        return data

    def create(self, validated_data):
        author = self.context["request"].user
        parent = validated_data.get("parent")
        post = validated_data.get("post")

        if parent:
            path = f"{parent.path}{parent.id}/"
            level = parent.level + 1
        else:
            path = ""
            level = 0

        comment = PostComment.objects.create(
            author=author,
            post=post,
            parent=parent,
            content=validated_data["content"],
            path=path,
            level=level,
        )

        post.comments_count = PostComment.objects.filter(
            post=post, is_deleted=False
        ).count()
        post.save(update_fields=["comments_count"])

        if parent:
            parent.replies_count = parent.replies.filter(is_deleted=False).count()
            parent.save(update_fields=["replies_count"])

        return comment


class BookmarkSerializer(serializers.ModelSerializer):
    post_data = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ["id", "post", "post_data", "folder", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_post_data(self, obj):
        return PostSerializer(obj.post, context=self.context).data


class BookmarkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        fields = ["post", "folder"]


class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(
        source="reporter.username", read_only=True
    )
    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    resolved_by_username = serializers.CharField(
        source="resolved_by.username", read_only=True
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "reporter",
            "reporter_username",
            "content_type",
            "content_id",
            "reason",
            "reason_display",
            "comment",
            "status",
            "status_display",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "moderation_comment",
            "action_taken",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "reporter",
            "status",
            "content_type",
            "content_id",
            "resolved_by",
            "resolved_at",
            "moderation_comment",
            "action_taken",
            "created_at",
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ["content_type", "content_id", "reason", "comment"]

    def validate_content_type(self, value):
        if value not in ["post", "comment"]:
            raise serializers.ValidationError("Недопустимый тип контента")
        return value

    def validate_reason(self, value):
        valid_reasons = ["spam", "copyright", "harassment", "inappropriate", "other"]
        if value not in valid_reasons:
            raise serializers.ValidationError("Недопустимая причина жалобы")
        return value

    def validate(self, data):
        content_type = data.get("content_type")
        content_id = data.get("content_id")

        if content_type == "post":
            from apps.social.infrastructure.models.social import Post

            if not Post.objects.filter(id=content_id).exists():
                raise serializers.ValidationError("Пост не найден")
        elif content_type == "comment":
            from apps.social.infrastructure.models.social import PostComment

            if not PostComment.objects.filter(id=content_id).exists():
                raise serializers.ValidationError("Комментарий не найден")

        reporter = self.context["request"].user
        if Report.objects.filter(
            reporter=reporter,
            content_type=content_type,
            content_id=content_id,
            status="pending",
        ).exists():
            raise serializers.ValidationError("Вы уже отправили жалобу на этот контент")

        return data

    def create(self, validated_data):
        validated_data["reporter"] = self.context["request"].user
        return super().create(validated_data)


class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ["id", "name", "posts_count", "created_at"]
        read_only_fields = ["id", "posts_count", "created_at"]


class FeedPostSerializer(PostReadMixin, serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.ImageField(source="author.avatar", read_only=True)
    author_display_name = serializers.CharField(
        source="author.display_name", read_only=True
    )
    author_is_premium = serializers.BooleanField(source="author.is_premium", read_only=True)

    anime = serializers.SerializerMethodField()
    playlist = serializers.SerializerMethodField()
    group = serializers.SerializerMethodField()
    original_post = serializers.SerializerMethodField(method_name='get_original_post_data')
    original_post_data = serializers.SerializerMethodField()

    media_files = serializers.SerializerMethodField()

    def get_media_files(self, obj):
        return PostMediaSerializer([item for item in obj.media_files.all() if item.is_active], many=True, context=self.context).data
    attachments_data = serializers.SerializerMethodField()
    hashtags = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    content_preview = serializers.SerializerMethodField()

    class Meta:
        model = Post
        list_serializer_class = PostListSerializer
        fields = [
            "id",
            "author",
            "author_username",
            "author_avatar",
            "author_display_name",
            "author_is_premium",
            "title",
            "post_type",
            "status",
            "visibility",
            "text",
            "content_preview",
            "image_url",
            "image_file",
            "video_url",
            "video_file",
            "anime",
            "anime_rating",
            "playlist",
            "reactor_post",
            "group",
            "original_post",
            "original_post_data",
            "repost_comment",
            "system_type",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "is_pinned",
            "pinned_at",
            "is_deleted",
            "is_spoiler",
            "allow_comments",
            "edited_at",
            "published_at",
            "created_at",
            "updated_at",
            "media_files",
            "attachments_data",
            "hashtags",
            "is_liked",
            "is_disliked",
            "is_bookmarked",
            "is_following",
            "can_edit",
            "can_delete",
        ]
        read_only_fields = [
            "id",
            "likes_count",
            "dislikes_count",
            "comments_count",
            "reposts_count",
            "views_count",
            "is_pinned",
            "pinned_at",
            "edited_at",
            "published_at",
            "created_at",
            "updated_at",
        ]

    def get_anime(self, obj):
        return post_anime(obj, self.context)


    def get_playlist(self, obj):
        value = self.context.get('post_contents', {}).get('playlist', {}).get(obj.playlist_id, obj.playlist)
        return playlist_card(value, self.context.get('request')) if value else None


    def get_group(self, obj):
        if obj.group:
            return {
                "id": obj.group.id,
                "name": obj.group.name,
                "slug": obj.group.slug,
                "avatar_url": obj.group.avatar.url if obj.group.avatar else None,
            }
        return None

    def get_original_post_data(self, obj):
        depth = self.context.get('post_depth', 0)
        if depth >= 2: return None
        source = original_post(obj, self.context)
        if source is None: return None
        cache = self.context.setdefault('serialized_originals', {})
        key = ('feed', source.pk, depth)
        if key not in cache:
            cache[key] = FeedPostSerializer(source, context={**self.context, 'post_depth': depth+1}).data
        return cache[key]

    def get_hashtags(self, obj):
        return [link.hashtag.name for link in obj.hashtag_links.all()]

    def get_is_liked(self, obj):
        if hasattr(obj, 'viewer_liked'): return obj.viewer_liked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PostLike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_disliked(self, obj):
        if hasattr(obj, 'viewer_disliked'): return obj.viewer_disliked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return PostDislike.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_bookmarked(self, obj):
        if hasattr(obj, 'viewer_bookmarked'): return obj.viewer_bookmarked
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Bookmark.objects.filter(user=request.user, post=obj).exists()
        return False

    def get_is_following(self, obj):
        if hasattr(obj, 'viewer_following'): return obj.viewer_following
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                follower=request.user, following=obj.author
            ).exists()
        return False

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.can_edit(request.user)
        return False

    def get_can_delete(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.can_delete(request.user)
        return False

    def get_content_preview(self, obj):
        return obj.get_content_preview(500)

    def get_attachments_data(self, obj):
        try:
            attachments = obj.attachments.all() if hasattr(obj, "attachments") else []
            return PostAttachmentSerializer(
                attachments, many=True, context=self.context
            ).data
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(
                "FeedPostSerializer: error getting attachments for post %s: %s", obj.id, exc
            )
            return []


class FavoriteSerializer(serializers.ModelSerializer):
    content_type_name = serializers.CharField(
        source="content_type.model", read_only=True
    )

    class Meta:
        model = Favorite
        fields = [
            "id",
            "user",
            "content_type",
            "content_type_name",
            "object_id",
            "folder",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]


class NewsSerializer(serializers.ModelSerializer):
    author_id = serializers.IntegerField(source="author.id", read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    author_display_name = serializers.CharField(source="author.display_name", read_only=True, default=None)
    author_avatar = serializers.SerializerMethodField()

    def get_author_avatar(self, obj):
        from apps.users.application.privacy import can_view_field
        viewer = getattr(self.context.get("request"), "user", None)
        return obj.author.avatar.url if obj.author.avatar and can_view_field(obj.author, viewer, "who_can_see_profile_photo") else None
    priority_display = serializers.CharField(source="get_priority_display", read_only=True)
    cover_url_final = serializers.SerializerMethodField()

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "summary",
            "content",
            "cover_url",
            "cover_file",
            "cover_url_final",
            "priority",
            "priority_display",
            "is_pinned",
            "is_published",
            "views_count",
            "author_id",
            "author_username",
            "author_display_name",
            "author_avatar",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "views_count", "created_at", "updated_at"]

    def get_cover_url_final(self, obj):
        if obj.cover_file:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.cover_file.url)
            return obj.cover_file.url
        return obj.cover_url or None

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["author"] = request.user
        return super().create(validated_data)
