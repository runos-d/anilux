import logging
import traceback as traceback_module
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F, Count
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from apps.anime.infrastructure.models.anime import Anime
from apps.playlists.infrastructure.models.playlists import Playlist
from apps.reactor.infrastructure.models.reactor import ReactorPost
from apps.users.infrastructure.models.users import User
from apps.social.infrastructure.models.social import (
    Comment,
    Group,
    GroupMembership,
    Post,
    Message,
    GroupChat,
    ChatRole,
    ChatMember,
    ChatAdminLog,
    PrivateChat,
    PrivateChatUserSettings,
    Follow,
    PostLike,
    PostDislike,
    Repost,
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
    MessageReadStatus,
    MessageAttachment,
    Attachment,
)
from apps.social.presentation.serializers.social_serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    GroupSerializer,
    GroupCreateSerializer,
    GroupMembershipSerializer,
    PostSerializer,
    PostCreateSerializer,
    PostUpdateSerializer,
    MessageSerializer,
    GroupChatSerializer,
    GroupChatCreateSerializer,
    ChatRoleSerializer,
    PrivateChatSerializer,
    PrivateChatCreateSerializer,
    FollowSerializer,
    PostCommentSerializer,
    PostCommentCreateSerializer,
)
from core.redis_events import publish_post_created, publish_message_sent
from core.online_status import online_status
from apps.social.application.chat_cache import ChatCacheService

logger = logging.getLogger(__name__)


class SocialService:
    @classmethod
    def build_unread_chats_data(cls, user):
        from apps.social.application.unread_count_service import unread_service

        unread_by_chat = unread_service.get_all_chats(user.id)
        chats_data = []

        for chat_id, count in unread_by_chat.items():
            chat = GroupChat.objects.filter(id=chat_id).first()
            if chat:
                chats_data.append(
                    {
                        "id": chat.id,
                        "type": "group",
                        "name": chat.name,
                        "avatar_url": chat.avatar.url if chat.avatar else None,
                        "unread_count": count,
                    }
                )
                continue

            chat = PrivateChat.objects.filter(
                Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
            ).first()
            if chat:
                other_user = chat.user1 if chat.user2 == user else chat.user2
                chats_data.append(
                    {
                        "id": chat.id,
                        "type": "private",
                        "name": other_user.display_name or other_user.username,
                        "avatar_url": other_user.avatar.url
                        if other_user.avatar
                        else None,
                        "unread_count": count,
                    }
                )

        return chats_data

    @classmethod
    def mark_chat_as_read(cls, user, chat_id):
        from apps.social.application.unread_count_service import unread_service

        chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
        if chat:
            unread_messages = Message.objects.filter(chat=chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )

            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))

            if read_statuses:
                MessageReadStatus.objects.bulk_create(
                    read_statuses, ignore_conflicts=True
                )

            unread_service.decrement(chat_id, user.id)

            return {"message": "Групповой чат отмечен как прочитанный"}

        private_chat = PrivateChat.objects.filter(
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        ).first()

        if private_chat:
            unread_messages = Message.objects.filter(private_chat=private_chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )

            read_statuses = []
            for msg in unread_messages:
                read_statuses.append(MessageReadStatus(message=msg, user=user))

            if read_statuses:
                MessageReadStatus.objects.bulk_create(
                    read_statuses, ignore_conflicts=True
                )

            unread_service.decrement(chat_id, user.id)

            return {"message": "Личный чат отмечен как прочитанный"}

        return None

    @classmethod
    def get_unread_count_data(cls, user, chat_id=None):
        from apps.social.application.unread_count_service import unread_service

        if chat_id:
            return {
                "unread_count": unread_service.get_for_chat(user.id, chat_id)
            }
        else:
            return {
                "unread_count": unread_service.get_total(user.id)
            }

    @classmethod
    def build_combined_chats_data(cls, user, request):
        chats_data = []

        try:
            group_chats = (
                GroupChat.objects.filter(members__user=user)
                .select_related("created_by")
                .prefetch_related("members__user")
            )

            for chat in group_chats:
                try:
                    last_message = (
                        Message.objects.filter(chat=chat)
                        .order_by("-created_at")
                        .first()
                    )
                except Exception:
                    last_message = None

                avatar_url = None
                if chat.avatar:
                    avatar_url = request.build_absolute_uri(chat.avatar.url)
                elif chat.anime and chat.anime.poster:
                    try:
                        avatar_url = request.build_absolute_uri(chat.anime.poster.url)
                    except Exception:
                        avatar_url = getattr(chat.anime, "poster_url", None)
                elif chat.franchise_id and chat.anime is None:
                    try:
                        from apps.anime.infrastructure.models.anime import Anime as AnimeModel

                        first = (
                            AnimeModel.objects.filter(franchise_id=chat.franchise_id)
                            .exclude(poster="")
                            .order_by("franchise_order", "id")
                            .first()
                        )
                        if first and first.poster:
                            avatar_url = request.build_absolute_uri(first.poster.url)
                    except Exception:
                        pass

                chat_data = {
                    "id": chat.id,
                    "type": "group",
                    "name": chat.name,
                    "avatar_url": avatar_url,
                    "franchise_id": chat.franchise_id,
                    "discussion_type": chat.discussion_type,
                    "participants_usernames": [
                        member.user.username for member in chat.members.all()
                    ],
                    "last_message_text": last_message.text if last_message else None,
                    "last_message_sender": last_message.sender.username
                    if last_message
                    else None,
                    "updated_at": (chat.last_message_at or chat.created_at).isoformat(),
                    "created_at": chat.created_at.isoformat(),
                }
                chats_data.append(chat_data)

        except Exception as e:
            logger.error(f"DEBUG: Ошибка при получении групповых чатов: {e}")

        try:
            private_chats = PrivateChat.objects.filter(
                Q(user1=user) | Q(user2=user)
            ).select_related("user1", "user2")

            for chat in private_chats:
                other_user = chat.user1 if chat.user2 == user else chat.user2

                is_online = online_status.is_online(other_user.id)

                try:
                    user_settings = PrivateChatUserSettings.objects.get(
                        chat=chat, user=user
                    )
                    custom_name = user_settings.custom_name
                    custom_avatar = (
                        user_settings.custom_avatar.url
                        if user_settings.custom_avatar
                        else None
                    )
                except PrivateChatUserSettings.DoesNotExist:
                    custom_name = None
                    custom_avatar = None

                try:
                    last_message = (
                        Message.objects.filter(private_chat=chat)
                        .order_by("-created_at")
                        .first()
                    )
                except Exception:
                    last_message = None

                chat_data = {
                    "id": chat.id,
                    "type": "private",
                    "name": custom_name,
                    "avatar_url": custom_avatar
                    or (other_user.avatar.url if other_user.avatar else None),
                    "participants_usernames": [other_user.username],
                    "other_user": {
                        "id": other_user.id,
                        "username": other_user.username,
                        "display_name": other_user.display_name or other_user.username,
                        "avatar": other_user.avatar.url if other_user.avatar else None,
                        "is_online": is_online,
                    },
                    "last_message_text": last_message.text if last_message else None,
                    "last_message_sender": last_message.sender.username
                    if last_message
                    else None,
                    "updated_at": chat.last_message_at.isoformat()
                    if chat.last_message_at
                    else chat.created_at.isoformat(),
                    "created_at": chat.created_at.isoformat(),
                }
                chats_data.append(chat_data)

        except Exception as e:
            logger.error(f"DEBUG: Ошибка при получении личных чатов: {e}")

        chats_data.sort(key=lambda x: x["updated_at"], reverse=True)

        return chats_data

    @classmethod
    def build_chat_detail_data(cls, user, chat_id, request):
        try:
            private_chat = PrivateChat.objects.get(
                Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
            )
            other_user = private_chat.other_user(user)

            try:
                user_settings = PrivateChatUserSettings.objects.get(
                    chat=private_chat, user=user
                )
                custom_name = user_settings.custom_name
                custom_avatar_url = (
                    user_settings.custom_avatar.url
                    if user_settings.custom_avatar
                    else None
                )
            except PrivateChatUserSettings.DoesNotExist:
                custom_name = None
                custom_avatar_url = None

            is_online = online_status.is_online(other_user.id)

            try:
                from apps.social.application.unread_count_service import unread_service

                unread_count_for_other = unread_service.get_for_chat(
                    other_user.id, private_chat.id
                )
            except Exception as e:
                logger.error(f"DEBUG: Ошибка подсчёта непрочитанных: {e}")
                unread_count_for_other = 0

            chat_data = {
                "id": private_chat.id,
                "type": "private",
                "name": custom_name,
                "avatar_url": custom_avatar_url
                or (other_user.avatar.url if other_user.avatar else None),
                "user1": private_chat.user1.id,
                "user2": private_chat.user2.id,
                "created_at": private_chat.created_at,
                "last_message_at": private_chat.last_message_at,
                "unread_count": unread_count_for_other,
                "other_user": {
                    "id": other_user.id,
                    "username": other_user.username,
                    "display_name": other_user.display_name or other_user.username,
                    "avatar": other_user.avatar.url if other_user.avatar else None,
                    "is_online": is_online,
                },
            }

            return {"type": "private", "data": chat_data}

        except PrivateChat.DoesNotExist:
            pass

        try:
            group_chat = GroupChat.objects.get(id=chat_id, members__user=user)

            serializer = GroupChatSerializer(group_chat, context={"request": request})
            data = serializer.data
            data["type"] = "group"

            return {"type": "group", "data": data}

        except GroupChat.DoesNotExist:
            pass

        return None

    @classmethod
    def get_user_posts_data(cls, user, page=1, limit=20):
        posts = (
            Post.objects.filter(author=user, status="published", is_deleted=False)
            .select_related("author", "anime", "group", "playlist", "reactor_post")
            .prefetch_related("media_files")
            .order_by("-created_at")
        )

        offset = (page - 1) * limit
        total = posts.count()
        posts_page = posts[offset : offset + limit]

        return {
            "count": total,
            "page": page,
            "limit": limit,
            "results": posts_page,
        }

    @classmethod
    def get_group_posts_data(cls, group, user, page=1, limit=20):
        posts = (
            Post.objects.filter(group=group, status="published", is_deleted=False)
            .select_related("author", "anime", "group", "playlist", "reactor_post")
            .prefetch_related("media_files", "attachments", "hashtag_links__hashtag")
            .order_by("-created_at")
        )

        offset = (page - 1) * limit
        total = posts.count()
        posts_page = posts[offset : offset + limit]

        return {
            "count": total,
            "page": page,
            "limit": limit,
            "results": posts_page,
        }

    @classmethod
    def get_popular_posts_data(cls, period="day"):
        if period == "day":
            since = timezone.now() - timedelta(days=1)
        elif period == "week":
            since = timezone.now() - timedelta(days=7)
        elif period == "month":
            since = timezone.now() - timedelta(days=30)
        else:
            since = None

        queryset = Post.objects.filter(
            status="published", post_type__in=["text", "image", "video", "anime"]
        )

        if since:
            queryset = queryset.filter(created_at__gte=since)

        queryset = queryset.annotate(
            popularity=F("likes_count") + F("comments_count") + F("reposts_count")
        ).order_by("-popularity")[:50]

        return queryset

    @classmethod
    def get_feed_statistics_data(cls, user):
        posts_count = Post.objects.filter(author=user, status="published").count()

        likes_received = PostLike.objects.filter(post__author=user).count()

        comments_received = PostComment.objects.filter(post__author=user).count()

        reposts_received = Repost.objects.filter(original_post__author=user).count()

        bookmarks_count = Bookmark.objects.filter(user=user).count()

        from apps.social.infrastructure.models.social import Follow

        following_ids = Follow.objects.filter(follower=user).values_list(
            "following_id", flat=True
        )
        new_posts_count = Post.objects.filter(
            author_id__in=following_ids,
            status="published",
            created_at__gte=timezone.now() - timedelta(days=1),
        ).count()

        return {
            "posts_count": posts_count,
            "likes_received": likes_received,
            "comments_received": comments_received,
            "reposts_received": reposts_received,
            "bookmarks_count": bookmarks_count,
            "new_posts_count": new_posts_count,
        }

    @classmethod
    def build_report_data(cls, report):
        return {
            "id": report.id,
            "reporter": {
                "id": report.reporter.id,
                "username": report.reporter.username,
                "display_name": report.reporter.display_name,
            },
            "content_type": report.content_type,
            "content_id": report.content_id,
            "reason": report.reason,
            "reason_display": dict(Report.REASON_CHOICES).get(report.reason),
            "comment": report.comment,
            "status": report.status,
            "status_display": dict(Report.STATUS_CHOICES).get(report.status),
            "created_at": report.created_at.isoformat(),
            "resolved_by": {
                "id": report.resolved_by.id,
                "username": report.resolved_by.username,
            } if report.resolved_by else None,
            "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None,
        }

    @classmethod
    def get_reports_data(cls, status_filter=None, content_type_filter=None, page=1, per_page=20):
        queryset = Report.objects.select_related(
            "reporter", "resolved_by"
        ).order_by("-created_at")

        if status_filter and status_filter != "all":
            queryset = queryset.filter(status=status_filter)

        if content_type_filter:
            queryset = queryset.filter(content_type=content_type_filter)

        total = queryset.count()
        reports_page = queryset[(page - 1) * per_page : page * per_page]

        reports = []
        for report in reports_page:
            reports.append(cls.build_report_data(report))

        return {
            "count": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "results": reports,
        }

    @classmethod
    def resolve_report(cls, report, user, status):
        report.status = status
        report.resolved_by = user
        report.resolved_at = timezone.now()
        report.save()

        logger.info(f"Report {report.id} resolved by {user.username} as {status}")

        return {
            "success": True,
            "message": "Жалоба рассмотрена",
            "report": {
                "id": report.id,
                "status": report.status,
                "resolved_by": user.username,
                "resolved_at": report.resolved_at.isoformat(),
            },
        }

    @classmethod
    def handle_media_uploads(cls, request, post, replace=False):
        if replace:
            post.media_files.all().delete()

        VIDEO_EXTENSIONS = {
            ".mp4",
            ".webm",
            ".mov",
            ".avi",
            ".mkv",
            ".m4v",
            ".ogv",
            ".flv",
        }
        IMAGE_EXTENSIONS = {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".bmp",
            ".svg",
            ".tiff",
            ".avif",
        }

        import os
        import imghdr
        from mimetypes import guess_type
        from io import BytesIO

        try:
            from PIL import Image
        except Exception:
            Image = None

        for key, file in request.FILES.items():
            if not key.startswith("media_"):
                continue

            ext = os.path.splitext(file.name)[1].lower()
            content_type = (file.content_type or "").lower()

            if content_type.startswith("video") or ext in VIDEO_EXTENSIONS:
                media_type = "video"
            elif content_type.startswith("image") or ext in IMAGE_EXTENSIONS:
                media_type = "image"
            else:
                media_type = None

            try:
                head = file.read(4096)
                file.seek(0)

                img_type = imghdr.what(None, h=head)
                if img_type:
                    media_type = "image"

                if media_type is None:
                    if len(head) >= 12 and b"ftyp" in head[4:12]:
                        media_type = "video"
                    elif head.startswith(b"\x1a\x45\xdf\xa3"):
                        media_type = "video"
                    elif head.startswith(b"RIFF") and b"AVI " in head[8:16]:
                        media_type = "video"

            except Exception:
                try:
                    file.seek(0)
                except Exception:
                    pass

            if not media_type:
                media_type = "image"

            file_size = getattr(file, "size", None) or 0

            mime_type = content_type or (guess_type(file.name)[0] or "")

            width = height = duration = None
            if media_type == "image" and Image is not None:
                try:
                    data = file.read()
                    file.seek(0)
                    img = Image.open(BytesIO(data))
                    width, height = img.size
                    try:
                        img.close()
                    except Exception:
                        pass
                except Exception:
                    try:
                        file.seek(0)
                    except Exception:
                        pass

            PostMedia.objects.create(
                post=post,
                media_type=media_type,
                file=file,
                file_size=file_size,
                mime_type=mime_type,
                width=width,
                height=height,
                duration=duration,
            )

    @classmethod
    def determine_post_type(cls, post):
        new_type = post.post_type
        media_qs = post.media_files.all()

        if post.playlist_id:
            new_type = "playlist"
        elif post.anime_id:
            new_type = "anime"
        elif post.reactor_post_id:
            new_type = "repost"
        elif media_qs.exists():
            if media_qs.filter(media_type="video").exists():
                new_type = "video"
            else:
                new_type = "image"

        if new_type != post.post_type:
            post.post_type = new_type
            post.save(update_fields=["post_type"])

    @classmethod
    def update_post_media_and_attachments(cls, request, post):
        VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v", ".ogv", ".flv"}
        IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".tiff", ".avif"}

        import os
        import imghdr
        from mimetypes import guess_type
        from io import BytesIO

        try:
            from PIL import Image
        except Exception:
            Image = None

        for key, file in request.FILES.items():
            if not key.startswith("media_"):
                continue

            ext = os.path.splitext(file.name)[1].lower()
            content_type = (file.content_type or "").lower()

            if content_type.startswith("video") or ext in VIDEO_EXTENSIONS:
                media_type = "video"
            elif content_type.startswith("image") or ext in IMAGE_EXTENSIONS:
                media_type = "image"
            else:
                try:
                    head = file.read(4096)
                    file.seek(0)
                    img_type = imghdr.what(None, h=head)
                    if img_type:
                        media_type = "image"
                    elif len(head) >= 12 and b"ftyp" in head[4:12]:
                        media_type = "video"
                    elif head.startswith(b"\x1a\x45\xdf\xa3"):
                        media_type = "video"
                    else:
                        media_type = "image"
                except Exception:
                    try:
                        file.seek(0)
                    except Exception:
                        pass
                    media_type = "image"

            file_size = getattr(file, "size", None) or 0
            mime_type = content_type or (guess_type(file.name)[0] or "")

            width = height = None
            if media_type == "image" and Image is not None:
                try:
                    data = file.read()
                    file.seek(0)
                    img = Image.open(BytesIO(data))
                    width, height = img.size
                    try:
                        img.close()
                    except Exception:
                        pass
                except Exception:
                    try:
                        file.seek(0)
                    except Exception:
                        pass

            PostMedia.objects.create(
                post=post,
                media_type=media_type,
                file=file,
                file_size=file_size,
                mime_type=mime_type,
                width=width,
                height=height,
            )

        has_new_attachments = (
            "anime_ids" in request.data
            or "anime_ids[]" in request.data
            or "playlist_ids" in request.data
            or "playlist_ids[]" in request.data
            or "reactor_ids" in request.data
            or "reactor_ids[]" in request.data
        )
        if has_new_attachments:
            post.attachments.all().delete()

        if hasattr(request, "POST") and request.POST:
            anime_raw = request.POST.getlist("anime_ids[]") or request.POST.getlist("anime_ids") or []
        else:
            anime_raw = request.data.get("anime_ids[]") or request.data.get("anime_ids") or []

        if isinstance(anime_raw, str):
            anime_ids = [anime_raw]
        elif hasattr(anime_raw, "__iter__") and not isinstance(anime_raw, dict):
            anime_ids = list(anime_raw)
        else:
            anime_ids = []

        anime_ids = [aid for aid in anime_ids if aid]

        if hasattr(request, "POST") and request.POST:
            anime_ratings_raw = request.POST.getlist("anime_ratings[]") or request.POST.getlist("anime_ratings") or []
        else:
            anime_ratings_raw = request.data.get("anime_ratings[]") or request.data.get("anime_ratings") or []

        if isinstance(anime_ratings_raw, str):
            anime_ratings = [anime_ratings_raw]
        elif hasattr(anime_ratings_raw, "__iter__") and not isinstance(anime_ratings_raw, dict):
            anime_ratings = list(anime_ratings_raw)
        else:
            anime_ratings = []

        for idx, anime_id in enumerate(anime_ids):
            try:
                anime = Anime.objects.get(id=anime_id)
                PostAttachment.objects.create(
                    post=post,
                    content_type="anime",
                    object_id=anime.id,
                    metadata={"title": anime.title_ru or anime.title_en},
                )
            except Anime.DoesNotExist:
                pass

        post.anime = None
        if anime_ids:
            try:
                post.anime = Anime.objects.filter(id=anime_ids[0]).first()
                if anime_ratings and len(anime_ratings) > 0 and anime_ratings[0]:
                    try:
                        post.anime_rating = int(anime_ratings[0])
                    except (ValueError, TypeError):
                        post.anime_rating = None
            except Exception:
                pass

        if hasattr(request, "POST") and request.POST:
            playlist_raw = request.POST.getlist("playlist_ids[]") or request.POST.getlist("playlist_ids") or []
        else:
            playlist_raw = request.data.get("playlist_ids[]") or request.data.get("playlist_ids") or []

        if isinstance(playlist_raw, str):
            playlist_ids = [playlist_raw]
        elif hasattr(playlist_raw, "__iter__") and not isinstance(playlist_raw, dict):
            playlist_ids = list(playlist_raw)
        else:
            playlist_ids = []

        playlist_ids = [pid for pid in playlist_ids if pid]

        for playlist_id in playlist_ids:
            try:
                playlist = Playlist.objects.get(id=playlist_id)
                if playlist.user != request.user and playlist.visibility != "public":
                    return {"error": "Нет доступа к плейлисту", "status": 403}
                PostAttachment.objects.create(
                    post=post,
                    content_type="playlist",
                    object_id=playlist.id,
                    metadata={"title": playlist.title},
                )
            except Playlist.DoesNotExist:
                pass

        post.playlist = None
        if playlist_ids:
            try:
                post.playlist = Playlist.objects.filter(id=playlist_ids[0]).first()
            except Exception:
                pass

        if hasattr(request, "POST") and request.POST:
            reactor_raw = request.POST.getlist("reactor_ids[]") or request.POST.getlist("reactor_ids") or []
        else:
            reactor_raw = request.data.get("reactor_ids[]") or request.data.get("reactor_ids") or []

        if isinstance(reactor_raw, str):
            reactor_ids = [reactor_raw]
        elif hasattr(reactor_raw, "__iter__") and not isinstance(reactor_raw, dict):
            reactor_ids = list(reactor_raw)
        else:
            reactor_ids = []

        reactor_ids = [rid for rid in reactor_ids if rid]

        for reactor_id in reactor_ids:
            try:
                reactor = ReactorPost.objects.get(id=reactor_id)
                PostAttachment.objects.create(
                    post=post,
                    content_type="shorts",
                    object_id=reactor.id,
                    metadata={"title": reactor.title},
                )
            except ReactorPost.DoesNotExist:
                pass

        post.reactor_post = None
        if reactor_ids:
            try:
                post.reactor_post = ReactorPost.objects.filter(id=reactor_ids[0]).first()
            except Exception:
                pass

        if "anime_rating" in request.data and not anime_ratings:
            rating = request.data.get("anime_rating")
            if rating is None or rating == "":
                post.anime_rating = None
            else:
                try:
                    rating_val = int(rating)
                    if 1 <= rating_val <= 10:
                        post.anime_rating = rating_val
                    else:
                        return {"error": "Рейтинг должен быть от 1 до 10", "status": 400}
                except (ValueError, TypeError):
                    return {"error": "Неверный формат рейтинга", "status": 400}

        media_qs = post.media_files.all()
        if post.playlist:
            post.post_type = "playlist"
        elif post.anime:
            post.post_type = "anime"
        elif post.reactor_post:
            post.post_type = "repost"
        elif media_qs.exists():
            if media_qs.filter(media_type="video").exists():
                post.post_type = "video"
            else:
                post.post_type = "image"

            first = media_qs.order_by("order").first()
            if first:
                if first.media_type == "video":
                    post.video_file = first.file
                    post.video_url = first.url or ""
                    post.image_file = None
                    post.image_url = ""
                else:
                    post.image_file = first.file
                    post.image_url = first.url or ""
                    post.video_file = None
                    post.video_url = ""

        post.edited_at = timezone.now()
        post.save()

        return None

    @classmethod
    def repost_post(cls, user, post_id, data):
        try:
            original_post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return {"error": "Пост не найден", "status": 404}

        if original_post.author == user:
            return {"error": "Нельзя репостнуть свой пост", "status": 400}

        if original_post.post_type == "system":
            return {"error": "Нельзя репостнуть системный пост", "status": 400}

        if original_post.visibility == "private":
            return {"error": "Нельзя репостнуть приватный пост", "status": 400}

        comment = data.get("comment", "")
        chat_id = data.get("chat_id")
        repost_type = data.get("type", "feed")

        if chat_id or repost_type == "chat":
            chat = None
            chat_type = None

            try:
                chat = GroupChat.objects.get(id=chat_id)
                chat_type = "group"
            except (GroupChat.DoesNotExist, TypeError, ValueError):
                try:
                    chat = PrivateChat.objects.get(id=chat_id)
                    chat_type = "private"
                except (PrivateChat.DoesNotExist, TypeError, ValueError):
                    return {"error": "Чат не найден", "status": 404}

            if chat_type == "group":
                if not chat.members.filter(user=user).exists():
                    return {"error": "Вы не состоите в этом чате", "status": 403}
            else:
                if chat.user1 != user and chat.user2 != user:
                    return {"error": "Вы не состоите в этом чате", "status": 403}

            message = Message.objects.create(
                sender=user,
                shared_post=original_post,
                text=comment,
                chat=chat if chat_type == "group" else None,
                private_chat=chat if chat_type == "private" else None,
            )

            original_post.shares_count += 1
            original_post.save(update_fields=["shares_count"])

            from apps.social.presentation.serializers.social_serializers import MessageSerializer

            return {
                "success": True,
                "message_text": "Пост переслан в чат",
                "message_id": message.id,
                "message": MessageSerializer(
                    message, context={"request": data.get("request")}
                ).data,
            }

        existing_repost = Repost.objects.filter(
            user=user, original_post=original_post
        ).first()

        if existing_repost:
            return {"error": "Вы уже репостнули этот пост", "status": 400}

        with transaction.atomic():
            new_post = Post.objects.create(
                author=user,
                post_type="repost",
                text=comment,
                status="published",
                visibility="public",
                allow_comments=True,
                original_post=original_post,
                repost_comment=comment,
            )

            Repost.objects.create(
                user=user, original_post=original_post, comment=comment
            )

            original_post.reposts_count += 1
            original_post.save(update_fields=["reposts_count"])

        return {
            "success": True,
            "message": "Пост репостнут",
            "repost_id": new_post.id,
            "original_post_id": original_post.id,
            "post": new_post,
        }

    @classmethod
    def unrepost_post(cls, user, post_id):
        try:
            original_post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return {"error": "Пост не найден", "status": 404}

        repost = Repost.objects.filter(
            user=user, original_post=original_post
        ).first()

        if not repost:
            return {"error": "Вы не репостнули этот пост", "status": 400}

        Post.objects.filter(author=user, type="repost").filter(
            attachments__content_type="repost", attachments__object_id=original_post.id
        ).delete()

        repost.delete()

        original_post.reposts_count = max(0, original_post.reposts_count - 1)
        original_post.save(update_fields=["reposts_count"])

        return {"success": True, "message": "Репост удалён"}

    @classmethod
    def report_post(cls, user, post_id, data):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return {"error": "Пост не найден", "status": 404}

        if post.author == user:
            return {"error": "Нельзя жаловаться на свой пост", "status": 400}

        reason = data.get("reason", "other")
        if reason not in ["spam", "copyright", "harassment", "inappropriate", "other"]:
            return {"error": "Неверная причина жалобы", "status": 400}

        comment = data.get("comment", "")

        existing_report = Report.objects.filter(
            reporter=user, content_type="post", content_id=post_id, status="pending"
        ).first()

        if existing_report:
            return {"error": "Вы уже отправили жалобу на этот пост", "status": 400}

        try:
            report = Report.objects.create(
                reporter=user,
                content_type="post",
                content_id=post_id,
                reason=reason,
                comment=comment,
                status="pending",
            )

            logger.info(f"Report created: {report.id} by {user.username} on post {post_id}")

            try:
                from apps.notifications.infrastructure.models.notifications import Notification

                moderator = User.objects.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                ).first()

                if moderator:
                    reason_display = dict(Report.REASON_CHOICES).get(reason, reason)

                    Notification.objects.create(
                        user=moderator,
                        type="system",
                        title="🚨 Новая жалоба: Пост",
                        content=f"Причина: {reason_display}\nЖалоба от: @{user.username}\nID поста: {post_id}",
                        link=f"/admin/social/report/{report.id}/",
                    )
                    logger.info(f"Moderator notification sent to {moderator.username}")
                else:
                    logger.warning("No moderator found for report notification")
            except Exception as e:
                logger.warning(f"Failed to send moderator notification: {e}")

            return {
                "success": True,
                "message": "Жалоба отправлена",
                "report_id": report.id,
            }
        except Exception as e:
            logger.error(f"Error creating report: {e}", exc_info=True)
            return {"error": "Ошибка при создании жалобы", "detail": str(e), "status": 500}

    @classmethod
    def toggle_comment_like(cls, user, comment_id):
        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            return {"error": "Комментарий не найден", "status": 404}

        if comment.author == user:
            return {"error": "Нельзя лайкать свой комментарий", "status": 400}

        existing_like = PostCommentLike.objects.filter(
            user=user, comment=comment
        ).first()

        existing_dislike = PostCommentDislike.objects.filter(
            user=user, comment=comment
        ).first()

        if existing_like:
            existing_like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            comment.save(update_fields=["likes_count"])
            return {
                "success": True,
                "liked": False,
                "likes_count": comment.likes_count,
                "dislikes_count": comment.dislikes_count,
            }

        if existing_dislike:
            existing_dislike.delete()
            comment.dislikes_count = max(0, comment.dislikes_count - 1)

        PostCommentLike.objects.create(user=user, comment=comment)
        comment.likes_count += 1
        comment.save(update_fields=["likes_count", "dislikes_count"])

        return {
            "success": True,
            "liked": True,
            "likes_count": comment.likes_count,
            "dislikes_count": comment.dislikes_count,
        }

    @classmethod
    def toggle_comment_dislike(cls, user, comment_id):
        try:
            comment = PostComment.objects.get(id=comment_id)
        except PostComment.DoesNotExist:
            return {"error": "Комментарий не найден", "status": 404}

        if comment.author == user:
            return {"error": "Нельзя дизлайкать свой комментарий", "status": 400}

        existing_dislike = PostCommentDislike.objects.filter(
            user=user, comment=comment
        ).first()

        existing_like = PostCommentLike.objects.filter(
            user=user, comment=comment
        ).first()

        if existing_dislike:
            existing_dislike.delete()
            comment.dislikes_count = max(0, comment.dislikes_count - 1)
            comment.save(update_fields=["dislikes_count"])
            return {
                "success": True,
                "disliked": False,
                "likes_count": comment.likes_count,
                "dislikes_count": comment.dislikes_count,
            }

        if existing_like:
            existing_like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)

        PostCommentDislike.objects.create(user=user, comment=comment)
        comment.dislikes_count += 1
        comment.save(update_fields=["likes_count", "dislikes_count"])

        return {
            "success": True,
            "disliked": True,
            "likes_count": comment.likes_count,
            "dislikes_count": comment.dislikes_count,
        }

    @classmethod
    def create_comment(cls, user, content_type_str, object_id, data):
        try:
            content_type = ContentType.objects.get(model=content_type_str)
        except ContentType.DoesNotExist:
            raise ValueError("Invalid content_type")

        return content_type, object_id

    @classmethod
    def check_post_edit_permission(cls, post, user):
        if post.author != user:
            return {"error": "Нельзя редактировать чужие посты", "status": 403}

        if (timezone.now() - post.created_at).total_seconds() > 300:
            return {"error": "Время на редактирование истекло", "status": 400}

        return None

    @classmethod
    def update_post_fields(cls, post, data):
        if "title" in data:
            post.title = data["title"][:200] if data["title"] else None

        if "text" in data:
            text = data["text"]
            if text and len(text) > 5000:
                return {"error": "Максимум 5000 символов", "status": 400}
            post.text = text

        if "visibility" in data:
            if data["visibility"] in ["public", "followers", "friends", "private"]:
                post.visibility = data["visibility"]

        if "allow_comments" in data:
            post.allow_comments = bool(data["allow_comments"])

        if "is_spoiler" in data:
            post.is_spoiler = bool(data["is_spoiler"])

        if "spoiler_description" in data:
            post.spoiler_description = data["spoiler_description"][:255]

        return None

    @classmethod
    def create_message(cls, user, chat_id, serializer, topic_id=None):
        if not chat_id:
            raise PermissionError("Не указан ID чата")

        chat = None
        private_chat = None

        try:
            chat = GroupChat.objects.get(id=chat_id)
            member = ChatMember.objects.filter(
                chat=chat, user=user
            ).first()
            if not member:
                raise PermissionError("Пользователь не является участником чата")
            if member.is_banned:
                raise PermissionError("Пользователь забанен в чате")
            if member.is_muted and (
                member.muted_until is None or member.muted_until > timezone.now()
            ):
                raise PermissionError("Пользователь заглушен в чате")
            if not member.can_send_messages:
                raise PermissionError("Пользователь не может отправлять сообщения")

            message = serializer.save(
                chat=chat, sender=user, topic_id=topic_id
            )

        except GroupChat.DoesNotExist:
            try:
                private_chat = PrivateChat.objects.get(id=chat_id)
                if user not in [
                    private_chat.user1,
                    private_chat.user2,
                ]:
                    raise PermissionError("Нет доступа к чату")

                settings = private_chat.get_user_settings(user)
                if settings.get("blocked", False):
                    raise PermissionError("Чат заблокирован")

                message = serializer.save(
                    private_chat=private_chat,
                    sender=user,
                    topic_id=topic_id,
                )

            except PrivateChat.DoesNotExist:
                raise PermissionError("Чат не найден")

        if chat:
            chat.save(update_fields=["last_message_at"])
        elif private_chat:
            private_chat.last_message_at = timezone.now()
            private_chat.save(update_fields=["last_message_at"])

        return message, chat, private_chat

    @classmethod
    def get_message_queryset(cls, chat_id, user):
        try:
            chat = GroupChat.objects.get(id=chat_id)
            if not ChatMember.objects.filter(
                chat=chat, user=user
            ).exists():
                return Message.objects.none()

            qs = Message.objects.filter(chat=chat, is_deleted=False).select_related(
                "sender", "reply_to__sender"
            )

            return qs
        except GroupChat.DoesNotExist:
            try:
                private_chat = PrivateChat.objects.get(id=chat_id)
                if user not in [private_chat.user1, private_chat.user2]:
                    return Message.objects.none()
                return Message.objects.filter(
                    private_chat=private_chat, is_deleted=False
                ).select_related("sender", "reply_to__sender")
            except PrivateChat.DoesNotExist:
                return Message.objects.none()

    @classmethod
    def process_message_attachments(cls, message, request, user):
        from apps.social.infrastructure.models.social import MessageAttachment, Attachment
        import os
        from mimetypes import guess_type

        attachment_ids = request.data.getlist("attachment_ids[]") or request.data.get("attachment_ids", [])
        if isinstance(attachment_ids, str):
            attachment_ids = [attachment_ids]

        media_files_uploaded = []
        for key in request.FILES.keys():
            if key.startswith("media_"):
                media_files_uploaded.append(request.FILES[key])

        first_media_file = None
        first_media_type = None

        for media_file in media_files_uploaded:
            content_type = media_file.content_type or ""
            ext = os.path.splitext(media_file.name)[1].lower()

            if content_type.startswith("image/") or ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                att_type = "image"
            elif content_type.startswith("video/") or ext in [".mp4", ".webm", ".mov", ".avi"]:
                att_type = "video"
            else:
                att_type = "file"

            Attachment.objects.create(
                message=message,
                type=att_type,
                file=media_file,
                file_name=media_file.name,
                file_size=media_file.size,
                mime_type=content_type or guess_type(media_file.name)[0] or "",
            )

            if first_media_file is None:
                first_media_file = media_file
                first_media_type = att_type

        if first_media_file:
            message.media = first_media_file
            message.media_type = first_media_type
            message.save(update_fields=['media', 'media_type'])

        anime_ids = request.data.getlist("anime_ids[]") or request.data.get("anime_ids", [])
        if isinstance(anime_ids, str):
            anime_ids = [anime_ids]
        for anime_id in anime_ids:
            if anime_id:
                try:
                    from apps.anime.infrastructure.models.anime import Anime

                    anime = Anime.objects.get(id=anime_id)
                    MessageAttachment.objects.create(
                        message=message,
                        content_type="anime",
                        object_id=anime_id,
                        metadata={"title": anime.title_ru or anime.title_en},
                    )
                except Anime.DoesNotExist:
                    pass

        playlist_ids = request.data.getlist("playlist_ids[]") or request.data.get("playlist_ids", [])
        if isinstance(playlist_ids, str):
            playlist_ids = [playlist_ids]
        for playlist_id in playlist_ids:
            if playlist_id:
                try:
                    from apps.playlists.infrastructure.models.playlists import Playlist

                    playlist = Playlist.objects.get(id=playlist_id)
                    MessageAttachment.objects.create(
                        message=message,
                        content_type="playlist",
                        object_id=playlist_id,
                        metadata={"title": playlist.title},
                    )
                except Playlist.DoesNotExist:
                    pass

        shorts_ids = request.data.getlist("shorts_ids[]") or request.data.get("shorts_ids", [])
        if isinstance(shorts_ids, str):
            shorts_ids = [shorts_ids]
        for shorts_id in shorts_ids:
            if shorts_id:
                try:
                    from apps.reactor.infrastructure.models.reactor import ReactorPost

                    shorts = ReactorPost.objects.get(id=shorts_id)
                    MessageAttachment.objects.create(
                        message=message,
                        content_type="shorts",
                        object_id=shorts_id,
                        metadata={"title": shorts.title},
                    )
                except ReactorPost.DoesNotExist:
                    pass

        post_ids = request.data.getlist("post_ids[]") or request.data.get("post_ids", [])
        if isinstance(post_ids, str):
            post_ids = [post_ids]
        for post_id in post_ids:
            if post_id:
                try:
                    post = Post.objects.get(id=post_id)
                    MessageAttachment.objects.create(
                        message=message,
                        content_type="post",
                        object_id=post_id,
                        metadata={"text": post.text[:100] if post.text else ""},
                    )
                except Post.DoesNotExist:
                    pass

    @classmethod
    def create_group_chat(cls, user, name, **kwargs):
        chat = GroupChat.objects.create(
            name=name,
            created_by=user,
            **kwargs,
        )

        ChatMember.objects.create(
            user=user, chat=chat, is_admin=True
        )

        ChatAdminLog.objects.create(
            chat=chat,
            user=user,
            action="chat_created",
            details={"chat_name": chat.name},
        )

        return chat

    @classmethod
    def leave_group_chat(cls, user, chat_id):
        try:
            chat = GroupChat.objects.get(pk=chat_id)

            member = ChatMember.objects.filter(chat=chat, user=user).first()
            if not member:
                return {"error": "Вы не являетесь участником этого чата", "status": 404}

            if member.is_owner and chat.discussion_type not in ["anime", "franchise"]:
                return {
                    "error": "Создатель чата не может его покинуть. Сначала передайте права или удалите чат.",
                    "status": 403,
                }

            member.delete()

            if chat.discussion_type == "anime":
                pass

            chat.save(update_fields=["last_message_at"])

            return {
                "message": "Вы успешно покинули чат",
                "chat_id": chat.id,
                "action": "left",
            }
        except GroupChat.DoesNotExist:
            return {"error": "Чат не найден", "status": 404}
        except Exception as e:
            logger.error(f"DEBUG leave_group_chat error: {e}")
            return {"error": str(e), "status": 500}

    @classmethod
    def delete_group_chat(cls, user, chat_id):
        try:
            chat = GroupChat.objects.get(pk=chat_id)

            member = ChatMember.objects.filter(chat=chat, user=user).first()
            if not member:
                return {
                    "error": "Вы не участник этого чата",
                    "status": 403,
                }

            if chat.discussion_type != "anime" and not member.is_owner:
                return {
                    "error": "Только создатель чата может его удалить",
                    "status": 403,
                }

            chat_id_value = chat.id
            is_anime_discussion = chat.discussion_type == "anime"

            if is_anime_discussion:
                Message.objects.filter(chat=chat).delete()

                ChatMember.objects.filter(chat=chat).delete()

                chat.last_message_at = None
                chat.save(update_fields=["last_message_at"])

                return {
                    "message": "Чат обсуждения очищен от участников",
                    "chat_id": chat_id_value,
                    "action": "cleared",
                }
            else:
                Message.objects.filter(chat=chat).delete()

                ChatMember.objects.filter(chat=chat).delete()

                chat.delete()

                return {
                    "message": "Чат успешно удалён",
                    "chat_id": chat_id_value,
                    "action": "deleted",
                }
        except GroupChat.DoesNotExist:
            return {"error": "Чат не найден", "status": 404}
        except Exception as e:
            logger.error(f"DEBUG delete_group_chat error: {e}")
            return {"error": str(e), "status": 500}

    @classmethod
    def soft_delete_message(cls, message, user):
        if message.sender != user:
            raise PermissionDenied("Вы можете удалять только свои сообщения")

        message.is_deleted = True
        message.deleted_at = timezone.now()
        message.deleted_by = user
        message.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

        return message

    @classmethod
    def create_group_chat_membership(cls, user, group):
        if group.memberships.filter(user=user).exists():
            return {"detail": "Already a member", "status": 400}

        membership = GroupMembership.objects.create(user=user, group=group)
        group.update_members_count()
        return {"data": GroupMembershipSerializer(membership).data}

    @classmethod
    def leave_group(cls, user, group):
        membership = group.memberships.filter(user=user).first()
        if not membership:
            return {"detail": "Not a member", "status": 400}

        membership.delete()
        group.update_members_count()
        return {"detail": "Left group"}

    @classmethod
    def check_follow(cls, user, following_id):
        try:
            target_user = User.objects.get(id=following_id)
        except User.DoesNotExist:
            return {"error": "User not found", "status": 404}

        is_following = Follow.objects.filter(
            follower=user, following=target_user
        ).exists()

        return {"is_following": is_following, "following_id": following_id}

    @classmethod
    def get_followers_data(cls, user):
        follows = Follow.objects.filter(following=user).select_related("follower")
        data = []
        for follow in follows:
            data.append(
                {
                    "id": follow.id,
                    "user": {
                        "id": follow.follower.id,
                        "username": follow.follower.username,
                        "display_name": follow.follower.display_name,
                        "avatar_url": follow.follower.avatar.url
                        if follow.follower.avatar
                        else None,
                    },
                    "created_at": follow.created_at.isoformat(),
                }
            )
        return data

    @classmethod
    def get_following_data(cls, user):
        follows = Follow.objects.filter(follower=user).select_related("following")
        data = []
        for follow in follows:
            data.append(
                {
                    "id": follow.id,
                    "user": {
                        "id": follow.following.id,
                        "username": follow.following.username,
                        "display_name": follow.following.display_name,
                        "avatar_url": follow.following.avatar.url
                        if follow.following.avatar
                        else None,
                    },
                    "created_at": follow.created_at.isoformat(),
                }
            )
        return data

    @classmethod
    def create_repost_notification(cls, comment, post, user):
        if post.author_id != user.id:
            try:
                from apps.notifications.application.services import NotificationService

                NotificationService.create_notification(
                    user=post.author,
                    notification_type="comment",
                    title="Новый комментарий",
                    content=f"{user.username} прокомментировал ваш пост",
                    link=f"/post/{post.id}",
                    icon="💬",
                )
            except Exception as e:
                pass

        if comment.parent_id:
            try:
                parent_comment = PostComment.objects.get(id=comment.parent_id)
                if (
                    parent_comment.author_id != user.id
                    and parent_comment.author_id != post.author_id
                ):
                    from apps.notifications.application.services import NotificationService

                    NotificationService.create_notification(
                        user=parent_comment.author,
                        notification_type="reply",
                        title="Ответ на ваш комментарий",
                        content=f"{user.username} ответил на ваш комментарий",
                        link=f"/post/{post.id}#comment-{comment.id}",
                        icon="↩️",
                    )
            except PostComment.DoesNotExist:
                pass
            except Exception as e:
                pass
