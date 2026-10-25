from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from apps.social.application.post_access import readable_posts
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from django.db import transaction
from django.db.models import Q, Count
from datetime import timedelta
import logging

from apps.social.infrastructure.models.social import (
    Follow,
    Post,
    PostLike,
    PostDislike,
    Bookmark,
    Report,
    PostComment,
    PostCommentLike,
    PostCommentDislike,
    Repost,
    Achievement,
    UserAchievement,
    Group,
    GroupMembership,
    Message,
    PrivateChat,
    GroupChat,
    ChatSettings,
    ChatMember,
    ChatFolder,
    ChatRole,
    Reaction,
    Attachment,
    EmailLog,
    FeedView,
    UserPostHidden,
    UserNotInterested,
    Hashtag,
    PostMedia,
    PostAttachment,
    UserMention,
    PostHashtag,
    Comment,
)
from apps.notifications.infrastructure.models.notifications import Complaint
from apps.users.infrastructure.models.users import User
from django.contrib.contenttypes.models import ContentType
from apps.social.presentation.serializers.social_serializers import (
    ChatFolderCreateSerializer,
    ChatFolderSerializer,
    GroupChatSerializer,
    PostCommentSerializer,
    PostCommentCreateSerializer,
    ReportSerializer,
    PostAttachmentSerializer,
    FeedPostSerializer,
    UserSimpleSerializer,
    UserAchievementSerializer,
    AchievementSerializer,
)

logger = logging.getLogger(__name__)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return Response({"error": "Нельзя подписаться на самого себя"}, status=400)

    follow = Follow.objects.filter(follower=request.user, following=target_user).first()

    if follow:
        follow.delete()
        return Response({"following": False, "message": "Вы отписались"})
    else:
        Follow.objects.create(follower=request.user, following=target_user)

    try:
        from apps.notifications.application.services import NotificationService

        NotificationService.create_notification(
            user=target_user,
            notification_type="follow",
            title=f"Новый подписчик",
            content=f"{request.user.username} подписался на вас",
            link=f"/profile/{request.user.id}",
            icon="👤",
        )
    except Exception as e:
        logger.info(f"Failed to send follow notification: {e}")

    return Response({"following": True, "message": "Вы подписались"})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_post_like(request, post_id):
    from apps.social.application.post_commands import react
    return Response(react(post_id, request.user, 'like', request.data.get('client_action_id'), request.data.get('active')))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_post_dislike(request, post_id):
    from apps.social.application.post_commands import react
    return Response(react(post_id, request.user, 'dislike', request.data.get('client_action_id'), request.data.get('active')))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_likes(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    likes = PostLike.objects.filter(post=post).select_related("user__profile")[:50]

    from apps.users.presentation.serializers.users_serializers import UserSerializer

    users = [like.user for like in likes]
    serializer = UserSerializer(users, many=True)

    return Response({"count": post.likes_count, "users": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_dislikers(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    dislikes = PostDislike.objects.filter(post=post).select_related("user__profile")[
        :50
    ]

    from apps.users.presentation.serializers.users_serializers import UserSerializer

    users = [d.user for d in dislikes]
    serializer = UserSerializer(users, many=True)

    return Response({"count": post.dislikes_count, "users": serializer.data})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    existing_like = comment.likes.filter(user=request.user).first()

    if existing_like:
        existing_like.delete()
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=["likes_count"])
        return Response({"liked": False, "likes_count": comment.likes_count})
    else:
        comment.dislikes.filter(user=request.user).delete()
        comment.likes.create(user=request.user)
        comment.likes_count += 1
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=["likes_count", "dislikes_count"])
        return Response({"liked": True, "likes_count": comment.likes_count})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    existing_dislike = comment.dislikes.filter(user=request.user).first()

    if existing_dislike:
        existing_dislike.delete()
        comment.dislikes_count = max(0, comment.dislikes_count - 1)
        comment.save(update_fields=["dislikes_count"])
        return Response({"disliked": False, "dislikes_count": comment.dislikes_count})
    else:
        comment.likes.filter(user=request.user).delete()
        comment.dislikes.create(user=request.user)
        comment.dislikes_count += 1
        comment.likes_count = max(0, comment.likes_count - 1)
        comment.save(update_fields=["likes_count", "dislikes_count"])
        return Response({"disliked": True, "dislikes_count": comment.dislikes_count})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    from apps.social.application.post_actions import pin
    return Response(pin(request, post_id, True))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    from apps.social.application.post_actions import pin
    return Response(pin(request, post_id, False))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    from types import SimpleNamespace
    payload = {**request.data, 'content_type': 'post', 'content_id': post_id}
    proxy = SimpleNamespace(user=request.user, data=payload)
    view = ReportViewSet()
    view.request = proxy
    return view.create(proxy)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_bookmark(request, post_id):
    from apps.social.application.post_actions import bookmark
    return Response(bookmark(request, post_id, True))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, post_id):
    from apps.social.application.post_actions import bookmark
    return Response(bookmark(request, post_id, False))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_bookmark_view(request):
    from apps.social.application.post_actions import bookmark
    return Response(bookmark(request, request.data.get('post_id'), request.data.get('active')))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bookmarks_folders(request):
    return Response({"folders": []})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def repost_post(request, post_id):
    from apps.social.application.post_actions import repost
    return Response(repost(request, post_id))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unrepost_post(request, post_id):
    from apps.social.application.post_actions import repost
    return Response(repost(request, post_id, remove=True))


def create_repost(request, post_id):
    return repost_post(request, post_id)


def delete_repost(request, post_id):
    return unrepost_post(request, post_id)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_post_view(request, post_id):
    from apps.social.application.post_actions import view
    return Response(view(request, post_id))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_viewers(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    views = FeedView.objects.filter(post=post).select_related("user__profile")[:50]

    from apps.users.presentation.serializers.users_serializers import UserSerializer

    users = [v.user for v in views]
    serializer = UserSerializer(users, many=True)

    return Response({"count": post.views_count, "users": serializer.data})




@api_view(["GET"])
@permission_classes([AllowAny])
def get_comment_replies(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    replies = Comment.objects.filter(parent=comment).select_related("author")[:20]

    from apps.social.presentation.serializers.social_serializers import CommentSerializer

    serializer = CommentSerializer(replies, many=True)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_post_comment_replies(request, comment_id):
    comment = get_object_or_404(PostComment.objects.filter(post__in=readable_posts(Post.objects.all(), request.user)), id=comment_id)
    from apps.social.application.post_comments import comments_for
    replies = comments_for(request.user, comment.post_id).filter(parent=comment).order_by("created_at", "pk")[:100]

    from apps.social.presentation.serializers.social_serializers import PostCommentSerializer

    serializer = PostCommentSerializer(replies, many=True, context={"request": request})

    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    from types import SimpleNamespace
    payload = {**request.data, 'content_type': 'comment', 'content_id': comment_id}
    proxy = SimpleNamespace(user=request.user, data=payload)
    view = ReportViewSet()
    view.request = proxy
    return view.create(proxy)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    from apps.social.application.post_commands import edit_post as command
    from apps.social.presentation.serializers.social_serializers import PostUpdateSerializer, PostSerializer
    post = command(request, post_id, PostUpdateSerializer, partial=True)
    return Response({'success': True, 'post': PostSerializer(post, context={'request': request}).data})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    from apps.social.application.post_comments import change_comment
    row = get_object_or_404(PostComment, pk=comment_id)
    return Response(PostCommentSerializer(change_comment(request, row.post_id, row.pk), context={'request': request}).data)





def _hide_post_for_user(request, post_id):
    from apps.social.application.post_actions import hide
    return Response(hide(request, post_id))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hide_post_from_feed(request, post_id):
    return _hide_post_for_user(request, post_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_post_not_interested(request, post_id):
    return _hide_post_for_user(request, post_id)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hide_author_from_feed(request, user_id):
    target_user = get_object_or_404(User, id=user_id)

    if target_user == request.user:
        return Response({"error": "Нельзя скрыть самого себя"}, status=400)

    _, created = UserNotInterested.objects.get_or_create(
        user=request.user, target_user=target_user
    )

    return Response(
        {
            "success": True,
            "hidden": True,
            "message": "Автор скрыт из ленты" if created else "Автор уже был скрыт",
        }
    )




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_hidden_posts(request):
    hidden_posts = (
        UserPostHidden.objects.filter(user=request.user, post__in=readable_posts(Post.objects.all(), request.user))
        .select_related("post")
        .order_by("-created_at")
    )

    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    offset = (page - 1) * page_size

    total = hidden_posts.count()
    hidden_posts_page = hidden_posts[offset : offset + page_size]

    results = []
    for hp in hidden_posts_page:
        if hp.post:
            results.append({
                "id": hp.id,
                "post_id": hp.post.id,
                "post_preview": hp.post.text[:200] if hp.post.text else "",
                "hidden_at": hp.created_at.isoformat(),
            })

    return Response(
        {
            "results": results,
            "count": total,
            "next": page + 1 if offset + page_size < total else None,
            "previous": page - 1 if page > 1 else None,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bookmarked_posts(request):
    bookmarks = (
        Bookmark.objects.filter(user=request.user, post__in=readable_posts(Post.objects.all(), request.user))
        .select_related("post")
        .order_by("-created_at")
    )

    page = int(request.query_params.get("page", 1))
    page_size = int(request.query_params.get("page_size", 20))
    offset = (page - 1) * page_size

    total = bookmarks.count()
    bookmarks_page = bookmarks[offset : offset + page_size]

    results = []
    for bm in bookmarks_page:
        if bm.post:
            from apps.social.presentation.serializers.social_serializers import PostSerializer

            try:
                serializer = PostSerializer(bm.post, context={"request": request})
                data = serializer.data
                data["bookmarked_at"] = bm.created_at.isoformat()
                data["bookmark_folder"] = bm.folder
                results.append(data)
            except:
                pass

    return Response(
        {
            "results": results,
            "count": total,
            "next": page + 1 if offset + page_size < total else None,
            "previous": page - 1 if page > 1 else None,
        }
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def restore_hidden_post(request, post_id):
    try:
        hidden = UserPostHidden.objects.get(user=request.user, post_id=post_id)
        hidden.delete()
        return Response({"success": True, "message": "Пост восстановлен"})
    except UserPostHidden.DoesNotExist:
        return Response({"error": "Пост не найден в скрытых"}, status=404)




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feed_statistics(request):
    user = request.user

    visible = readable_posts(Post.objects.all(), user)
    posts_count = visible.filter(author=user, status="published").count()
    likes_received = PostLike.objects.filter(post__in=visible.filter(author=user)).count()
    comments_received = PostComment.objects.filter(post__in=visible.filter(author=user), is_deleted=False).count()
    reposts_received = visible.filter(original_post__author=user, status='published').count()
    bookmarks_count = Bookmark.objects.filter(user=user, post__in=visible).count()

    following_ids = Follow.objects.filter(follower=user).values_list(
        "following_id", flat=True
    )
    new_posts_count = visible.filter(
        author_id__in=following_ids,
        status="published",
        created_at__gte=timezone.now() - timedelta(days=1),
    ).count()

    return Response(
        {
            "posts_count": posts_count,
            "likes_received": likes_received,
            "comments_received": comments_received,
            "reposts_received": reposts_received,
            "bookmarks_count": bookmarks_count,
            "new_posts_count": new_posts_count,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def get_popular_posts(request):
    posts = readable_posts(Post.objects.all(), request.user).filter(
        likes_count__gte=1,  
    ).order_by("-likes_count", "-created_at")[:20]

    from apps.social.presentation.serializers.social_serializers import PostSerializer

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    user = get_object_or_404(User, id=user_id)
    posts = readable_posts(Post.objects.all(), request.user).filter(
        author=user, status="published", is_deleted=False
    ).order_by("-created_at")[:20]

    from apps.social.presentation.serializers.social_serializers import PostSerializer

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_group_posts(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    posts = readable_posts(Post.objects.all(), request.user).filter(
        group=group, status="published", is_deleted=False
    ).order_by("-created_at")[:20]

    from apps.social.presentation.serializers.social_serializers import PostSerializer

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)




@api_view(["GET"])
@permission_classes([AllowAny])
def get_hashtag_posts(request, tag_name):
    hashtag = get_object_or_404(Hashtag, name=tag_name.lstrip("#"))
    posts = readable_posts(Post.objects.all(), request.user).filter(
        hashtag_links__hashtag=hashtag, status="published", is_deleted=False
    ).order_by("-created_at")[:20]

    from apps.social.presentation.serializers.social_serializers import PostSerializer

    serializer = PostSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_hashtags(request):
    query = request.query_params.get("q", "")
    hashtags = Hashtag.objects.filter(name__icontains=query).order_by("-posts_count")[
        :10
    ]

    return Response([{"name": h.name, "posts_count": h.posts_count} for h in hashtags])




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_notification_settings(request):
    user = request.user
    return Response(
        {
            "notify_likes": user.notify_likes,
            "notify_comments": user.notify_comments,
            "notify_mentions": user.notify_mentions,
            "email_digest": user.email_digest,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_user_notification_settings(request):
    from apps.users.presentation.serializers.users_serializers import UserNotificationSettingsSerializer

    serializer = UserNotificationSettingsSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    user = request.user
    for field, value in validated.items():
        setattr(user, field, value)

    user.save()

    return Response({"success": True})




class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def create_user_achievement(self, request):
        serializer = AchievementSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        achievement = serializer.save()
        achievement.is_active = True
        achievement.save(update_fields=["is_active"])

        all_users = User.objects.all()
        user_achievements = []
        for user in all_users:
            user_achievements.append(
                UserAchievement(
                    user=user,
                    achievement=achievement,
                    progress=0,
                    is_unlocked=False,
                )
            )
        UserAchievement.objects.bulk_create(
            user_achievements, ignore_conflicts=True
        )

        return Response(
            AchievementSerializer(achievement, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class UserAchievementViewSet(viewsets.ModelViewSet):
    serializer_class = None
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserAchievement.objects.filter(user=self.request.user)

    @action(detail=False, methods=["get"])
    def all(self, request):
        user_id = request.query_params.get("user_id")
        if user_id:
            qs = UserAchievement.objects.filter(user_id=user_id)
        else:
            qs = UserAchievement.objects.filter(user=request.user)
        serializer = UserAchievementSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class AchievementAdminViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @action(detail=False, methods=["get"])
    def condition_types(self, request):
        data = {
            "posts_count": "Создать N постов",
            "followers_count": "Получить N подписчиков",
            "following_count": "Подписаться на N пользователей",
            "likes_received": "Получить N лайков",
            "reposts_count": "Сделать N репостов",
            "reposts_received": "Получить N репостов",
            "comments_count": "Оставить N комментариев",
            "comments_social": "Написать N комментариев в ленте",
            "likes_given": "Поставить N лайков",
            "registration_days": "Быть на сайте N дней",
            "profile_completed": "Заполнить профиль на N%",
            "anime_watched": "Посмотреть N аниме полностью",
            "anime_watched_episodes": "Просмотреть N эпизодов",
            "anime_favorites": "Добавить N аниме в избранное",
            "anime_rated": "Поставить оценку N аниме",
            "anime_rewatched": "Пересмотреть N аниме",
            "anime_started": "Добавить N аниме в коллекцию",
            "anime_watching_now": "Смотреть одновременно N аниме",
            "anime_on_hold": "Отложить N аниме",
            "anime_dropped": "Бросить просмотр N аниме",
            "anime_planned": "Добавить N аниме в планы",
            "top_ratings": "Поставить оценку 9+ N аниме",
            "movies_watched": "Посмотреть N фильмов",
            "ova_watched": "Посмотреть N OVA",
            "anime_comments": "Написать N комментариев к аниме",
            "genres_explored": "Посмотреть аниме из N разных жанров",
            "studios_explored": "Посмотреть аниме N разных студий",
            "franchise_completed": "Полностью просмотреть N франшиз",
            "episodes_single_day": "Посмотреть N+ эпизодов за один день",
            "watch_days": "Смотреть аниме N дней",
            "hours_watched": "Провести N часов за просмотром",
            "night_owl_days": "Смотреть аниме ночью N дней",
            "evening_days": "Смотреть аниме вечером N дней",
            "morning_days": "Смотреть аниме утром N дней",
            "playlists_created": "Создать N плейлистов",
            "playlist_items_added": "Добавить N элементов в плейлисты",
        }
        return Response(data)

    @action(detail=True, methods=["post"])
    def toggle_active(self, request, pk=None):
        achievement = self.get_object()
        achievement.is_active = not achievement.is_active
        achievement.save(update_fields=["is_active"])
        return Response({"is_active": achievement.is_active})




class UploadedFileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return []  


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_file(request):
    return Response({"success": True, "url": ""})



from django.contrib.contenttypes.models import ContentType
from apps.social.infrastructure.models.social import Favorite
from apps.social.presentation.serializers.social_serializers import FavoriteSerializer


from .post_favorites import FavoriteViewSet


@api_view(["GET"])
@permission_classes([AllowAny])
def get_online_users(request):
    from django.contrib.auth import get_user_model

    User = get_user_model()

    users = User.objects.filter(is_online=True).exclude(
        id=request.user.id if request.user.is_authenticated else 0
    )[:20]

    from apps.users.presentation.serializers.users_serializers import UserSerializer

    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)


class GroupSearchView(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        return Group.objects.filter(name__icontains=query)[:20]




class ReactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return []  






class AttachmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return []  


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_attachment(request, message_id):
    from apps.social.infrastructure.models.social import Message, Attachment
    from django.core.files.storage import default_storage
    import os

    message = get_object_or_404(Message, id=message_id)

    if message.sender != request.user:
        if hasattr(message, "chat") and message.chat:
            from apps.social.infrastructure.models.social import ChatMember

            if not ChatMember.objects.filter(
                chat=message.chat, user=request.user
            ).exists():
                return Response({"error": "Нет доступа"}, status=403)
        elif hasattr(message, "private_chat") and message.private_chat:
            pc = message.private_chat
            if pc.user1 != request.user and pc.user2 != request.user:
                return Response({"error": "Нет доступа"}, status=403)
        else:
            return Response({"error": "Нет доступа"}, status=403)

    if "file" not in request.FILES:
        return Response({"error": "Файл не найден"}, status=400)

    file = request.FILES["file"]

    mime_type = file.content_type
    media_type = "file"
    if mime_type.startswith("image/"):
        media_type = "image"
    elif mime_type.startswith("video/"):
        media_type = "video"
    elif mime_type.startswith("audio/"):
        media_type = "audio"

    file_path = f"message_attachments/{message_id}/{file.name}"
    file_url = default_storage.save(file_path, file)
    file_full_url = request.build_absolute_uri(default_storage.url(file_url))

    attachment = Attachment.objects.create(
        message=message,
        file=file,
        file_name=file.name,
        file_size=file.size,
        mime_type=mime_type,
        type=media_type,
    )

    return Response(
        {
            "success": True,
            "id": attachment.id,
            "url": file_full_url,
            "file_name": file.name,
            "file_size": file.size,
            "mime_type": mime_type,
            "type": media_type,
        }
    )




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pin_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.is_pinned = True
    message.save(update_fields=["is_pinned"])
    return Response({"success": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unpin_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    message.is_pinned = False
    message.save(update_fields=["is_pinned"])
    return Response({"success": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def forward_message(request, message_id):
    return Response({"success": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_pinned_messages(request, chat_id):
    chat = get_object_or_404(GroupChat, id=chat_id)
    messages = Message.objects.filter(chat=chat, is_pinned=True)[:10]

    from apps.social.presentation.serializers.social_serializers import MessageSerializer

    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)










@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_private_chat_read(request, chat_id):
    chat = get_object_or_404(PrivateChat, id=chat_id)

    if chat.user1 != request.user and chat.user2 != request.user:
        return Response({"error": "Нет доступа к чату"}, status=403)

    message_ids = request.data.get("message_ids", [])

    if message_ids:
        from apps.social.infrastructure.models.social import Message, MessageReadStatus
        from django.utils import timezone
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        messages = Message.objects.filter(
            id__in=message_ids,
            private_chat=chat
        )

        read_message_ids = list(messages.values_list("id", flat=True))

        statuses = [
            MessageReadStatus(message_id=msg_id, user_id=request.user.id)
            for msg_id in read_message_ids
        ]
        MessageReadStatus.objects.bulk_create(statuses, ignore_conflicts=True)

        try:
            from apps.social.application.unread_count_service import unread_service
            unread_service.decrement(chat_id, request.user.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error decrementing unread count: {e}")

        try:
            from apps.social.application.tasks import create_message_read_status
            for msg_id in read_message_ids:
                create_message_read_status.delay(msg_id, request.user.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error scheduling read status task: {e}")

        other_user = chat.other_user(request.user)
        if other_user:
            channel_layer = get_channel_layer()
            try:
                async_to_sync(channel_layer.group_send)(
                    f"chat_user_{other_user.id}",
                    {
                        "type": "messages_read_event",
                        "user_id": request.user.id,
                        "message_ids": read_message_ids,
                        "read_at": timezone.now().isoformat(),
                    },
                )
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error sending read status: {e}")
    else:
        chat.mark_as_read(request.user)

    return Response({"success": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_group_chat_read(request, chat_id):
    chat = get_object_or_404(GroupChat, id=chat_id)

    from apps.social.infrastructure.models.social import ChatMember
    is_member = ChatMember.objects.filter(chat=chat, user=request.user).exists()
    if not is_member:
        return Response({"error": "Нет доступа к чату"}, status=403)

    message_ids = request.data.get("message_ids", [])

    if message_ids:
        from apps.social.infrastructure.models.social import Message, MessageReadStatus
        from django.utils import timezone
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        messages = Message.objects.filter(
            id__in=message_ids,
            chat=chat
        )

        read_message_ids = list(messages.values_list("id", flat=True))

        statuses = [
            MessageReadStatus(message_id=msg_id, user_id=request.user.id)
            for msg_id in read_message_ids
        ]
        MessageReadStatus.objects.bulk_create(statuses, ignore_conflicts=True)

        try:
            from apps.social.application.unread_count_service import unread_service
            unread_service.decrement(chat_id, request.user.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error decrementing unread count: {e}")

        try:
            from apps.social.application.tasks import create_message_read_status
            for msg_id in read_message_ids:
                create_message_read_status.delay(msg_id, request.user.id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error scheduling read status task: {e}")

        channel_layer = get_channel_layer()
        try:
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "messages_read_event",
                    "user_id": request.user.id,
                    "message_ids": read_message_ids,
                    "read_at": timezone.now().isoformat(),
                },
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending read status: {e}")
    else:
        chat.mark_as_read(request.user)

    return Response({"success": True})




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def search_messages(request):
    query = request.query_params.get("q", "")
    chat_id = request.query_params.get("chat_id")

    messages = Message.objects.filter(text__icontains=query, chat_id=chat_id).order_by(
        "-created_at"
    )[:50]

    from apps.social.presentation.serializers.social_serializers import MessageSerializer

    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reindex_messages(request):
    return Response({"success": True, "indexed": 0})










class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmailLog.objects.filter(user=self.request.user)




class RepostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Repost.objects.none()


from apps.social.presentation.views.post_comments import PostCommentViewSet


class BookmarkViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user, post__in=readable_posts(Post.objects.all(), self.request.user)).select_related("post__author", "post__anime", "post__playlist", "post__group").prefetch_related("post__media_files", "post__attachments", "post__hashtag_links__hashtag")

    def list(self, request):
        bookmarks = self.get_queryset().order_by("-created_at")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        total = bookmarks.count()
        bookmarks_page = bookmarks[offset : offset + page_size]

        posts = [b.post for b in bookmarks_page if b.post]
        serializer = FeedPostSerializer(posts, many=True, context={"request": request})

        return Response(
            {
                "results": serializer.data,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )

    @action(detail=False, methods=["get"], url_path="posts")
    def posts(self, request):
        return self.list(request)


class ReportViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        logger.info(f"Report create request data: {request.data}")

        content_type = request.data.get("content_type")
        content_id = request.data.get("content_id")
        reason = request.data.get("reason", "other")
        comment = str(request.data.get("comment", "")).strip()
        if len(comment) > 1000:
            return Response({'error': 'Комментарий не должен превышать 1000 символов'}, status=400)

        if not content_type:
            content_type = request.data.get("type")
        if not content_id:
            content_id = (
                request.data.get("object_id")
                or request.data.get("id")
                or request.data.get("post_id")
                or request.data.get("comment_id")
                or request.data.get("user_id")
            )

        if not content_type:
            if request.data.get("post_id"):
                content_type = "post"
                content_id = request.data.get("post_id")
            elif request.data.get("comment_id"):
                content_type = "comment"
                content_id = request.data.get("comment_id")
            elif request.data.get("user_id"):
                content_type = "user"
                content_id = request.data.get("user_id")

        if not content_type:
            logger.warning(f"Report missing content_type: {request.data}")
            return Response(
                {
                    "error": "Поле content_type обязательно",
                    "valid_types": ["post", "comment", "user"],
                    "received_data": request.data,
                },
                status=400,
            )

        if not content_id:
            logger.warning(f"Report missing content_id: {request.data}")
            return Response(
                {"error": "Поле content_id обязательно", "received_data": request.data},
                status=400,
            )

        content_type = str(content_type).lower()
        if content_type not in ["post", "comment", "user"]:
            logger.warning(f"Report invalid content_type: {content_type}")
            return Response(
                {
                    "error": f"Недопустимый content_type: {content_type}",
                    "valid_types": ["post", "comment", "user"],
                },
                status=400,
            )

        try:
            content_id = int(str(content_id))
            if content_id <= 0: raise ValueError()
        except (ValueError, TypeError):
            logger.warning(f"Report invalid content_id: {content_id}")
            return Response(
                {"error": f"Неверный формат content_id: {content_id}"}, status=400
            )

        if content_type == "post":
            from apps.social.application.post_access import resolve_post_id
            content_id = resolve_post_id(content_id)
            if not readable_posts(Post.objects.all(), request.user).filter(id=content_id).exists():
                return Response({"error": "Пост не найден"}, status=404)
            if Post.objects.filter(pk=content_id, author=request.user).exists():
                return Response({'error': 'Нельзя пожаловаться на свой пост'}, status=400)
        elif content_type == "comment":
            if not PostComment.objects.filter(id=content_id, post__in=readable_posts(Post.objects.all(), request.user), is_deleted=False).exists():
                return Response({"error": "Комментарий не найден"}, status=404)
            if PostComment.objects.filter(pk=content_id, author=request.user).exists():
                return Response({'error': 'Нельзя пожаловаться на свой комментарий'}, status=400)
        elif content_type == "user":
            if not User.objects.filter(id=content_id).exists():
                return Response({"error": "Пользователь не найден"}, status=404)
            if content_id == request.user.id:
                return Response(
                    {"error": "Нельзя пожаловаться на самого себя"}, status=400
                )

        if reason not in dict(Report.REASON_CHOICES):
            return Response({'error': 'Неизвестная причина жалобы'}, status=400)
        with transaction.atomic():
            User.objects.select_for_update().only('id').get(pk=request.user.pk)
            previous = Report.objects.filter(reporter=request.user, content_type=content_type,
                content_id=content_id, status='pending').first()
            if previous:
                return Response({'success': True, 'id': str(previous.pk), 'message': 'Жалоба уже отправлена'})
            report = Report.objects.create(reporter=request.user, content_type=content_type,
                content_id=content_id, reason=reason, comment=comment, status='pending')
            from apps.notifications.infrastructure.models.notifications import Notification, Complaint
            from django.contrib.contenttypes.models import ContentType

            if content_type == "post":
                target = Post.objects.select_related('author').get(pk=content_id)
                ct = ContentType.objects.get_for_model(Post)
                snapshot = {
                    'type': 'post', 'title': target.title or '', 'text': target.text or '',
                    'author_id': target.author_id, 'author_username': target.author.username,
                    'url': f'/post/{target.public_id}', 'public_id': target.public_id,
                    'media': [
                        {
                            'id': media.pk, 'type': media.media_type,
                            'path': media.file.name if media.file else '',
                            'caption': media.caption, 'mime_type': media.mime_type,
                            'file_size': media.file_size,
                        }
                        for media in target.media_files.filter(is_active=True)
                    ],
                }
                complaint_type = 'reactor_post'
            elif content_type == "comment":
                target = PostComment.objects.select_related('author', 'post').get(pk=content_id)
                ct = ContentType.objects.get_for_model(PostComment)
                snapshot = {
                    'type': 'comment', 'text': target.content or '',
                    'author_id': target.author_id, 'author_username': target.author.username,
                    'post_id': target.post_id, 'url': f'/post/{target.post.public_id}',
                }
                complaint_type = 'comment'
            else:
                target = User.objects.get(pk=content_id)
                ct = ContentType.objects.get_for_model(User)
                snapshot = {
                    'type': 'user', 'author_id': target.pk, 'author_username': target.username,
                    'title': target.nickname or target.username,
                    'url': f'/profile/@{target.nickname}' if target.nickname else f'/profile/{target.username}',
                }
                complaint_type = 'user'

            Complaint.objects.create(
                content_type=ct, object_id=content_id, complainant=request.user,
                complaint_type=complaint_type, reason=reason, description=comment,
                status='pending', source_report_id=report.pk, target_snapshot=snapshot,
            )

            content_label = {'post': 'пост', 'comment': 'комментарий', 'user': 'пользователя'}[content_type]
            reason_label = dict(Report.REASON_CHOICES).get(reason, reason)
            admin_notifications = [Notification(
                user=moderator, type='system', title=f'Новая жалоба на {content_label}',
                content=f'Причина: {reason_label}. Отправитель: @{request.user.username}.',
                link='/admin/complaints', is_important=True,
                dedupe_key=f'complaint:{report.pk}:admin:{moderator.pk}',
            ) for moderator in User.objects.filter(models.Q(is_staff=True) | models.Q(is_superuser=True), is_active=True)]
            Notification.objects.bulk_create(admin_notifications, ignore_conflicts=True)

        logger.info("Report %s and complaint created", report.pk)

        return Response(
            {"success": True, "id": str(report.id), "message": "Жалоба отправлена"},
            status=201,
        )


class PostMediaViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PostMedia.objects.all()


class PostAttachmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = PostAttachmentSerializer

    def get_queryset(self):
        qs = PostAttachment.objects.filter(post__in=readable_posts(Post.objects.all(), self.request.user)).order_by('created_at', 'id')
        post_id = self.request.query_params.get("post")
        if post_id:
            try:
                qs = qs.filter(post_id=post_id)
            except (ValueError, TypeError):
                pass
        return qs

    def create(self, request, *args, **kwargs):
        from apps.social.application.post_attachment_commands import change_attachment
        instance = change_attachment(request)
        return Response(self.get_serializer(instance).data, status=201)

    def update(self, request, *args, **kwargs):
        from apps.social.application.post_attachment_commands import change_attachment
        instance = change_attachment(request, self.get_object())
        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        from apps.social.application.post_attachment_commands import change_attachment
        change_attachment(request, self.get_object(), delete=True)
        return Response(status=204)


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user).select_related(
            "following"
        )

    def list(self, request):
        follows = self.get_queryset().order_by("-created_at")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        search = request.query_params.get("search", "")
        if search:
            follows = follows.filter(
                following__username__icontains=search
            ) | follows.filter(following__display_name__icontains=search)

        sort = request.query_params.get("sort", "date")  
        if sort == "name":
            follows = follows.order_by("following__username")
        elif sort == "activity":
            follows = follows.order_by("-following__last_activity")
        else:
            follows = follows.order_by("-created_at")

        total = follows.count()
        follows = follows[offset : offset + page_size]

        from apps.users.presentation.serializers.users_serializers import UserSerializer

        users = [f.following for f in follows]
        data = UserSerializer(users, many=True, context={"request": request}).data

        for i, user_data in enumerate(data):
            user_data["subscribed_at"] = (
                follows[i].created_at.isoformat() if follows else None
            )
            user_data["is_subscribed"] = True

        return Response(
            {
                "results": data,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )




class NotInterestedViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserNotInterested.objects.filter(user=self.request.user).select_related(
            "target_user"
        )

    def list(self, request):
        not_interested = self.get_queryset().order_by("-created_at")

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        offset = (page - 1) * page_size

        search = request.query_params.get("search", "")
        if search:
            not_interested = not_interested.filter(
                target_user__username__icontains=search
            )

        total = not_interested.count()
        not_interested = not_interested[offset : offset + page_size]

        from apps.users.presentation.serializers.users_serializers import UserSerializer

        users = [ni.target_user for ni in not_interested]
        data = UserSerializer(users, many=True, context={"request": request}).data

        for i, user_data in enumerate(data):
            user_data["hidden_at"] = (
                not_interested[i].created_at.isoformat() if not_interested else None
            )
            user_data["reason"] = not_interested[i].reason if not_interested else None

        return Response(
            {
                "results": data,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )

    @action(detail=False, methods=["post"], url_path="(?P<user_id>[^/.]+)")
    def add_or_remove(self, request, user_id=None):
        target_user = get_object_or_404(User, id=user_id)

        if target_user == request.user:
            return Response({"error": "Нельзя скрыть самого себя"}, status=400)

        existing = UserNotInterested.objects.filter(
            user=request.user, target_user=target_user
        ).first()

        if existing:
            existing.delete()
            return Response(
                {"hidden": False, "message": "Пользователь удалён из скрытых"}
            )
        else:
            reason = request.data.get("reason", "")
            UserNotInterested.objects.create(
                user=request.user, target_user=target_user, reason=reason
            )
            return Response(
                {"hidden": True, "message": "Пользователь добавлен в скрытые"}
            )




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chats_for_forward(request):
    user = request.user

    search = request.query_params.get("search", "")

    results = []

    try:
        private_chats = PrivateChat.objects.filter(
            models.Q(user1=user) | models.Q(user2=user)
        )

        if search:
            private_chats = private_chats.filter(
                models.Q(user1__username__icontains=search, user2=user)
                | models.Q(user2__username__icontains=search, user1=user)
                | models.Q(user1__display_name__icontains=search, user2=user)
                | models.Q(user2__display_name__icontains=search, user1=user)
            )

        for chat in private_chats[:20]:
            try:
                other = chat.other_user(user)
                if other:
                    results.append(
                        {
                            "id": chat.id,
                            "type": "private",
                            "name": other.display_name or other.username,
                            "avatar": other.avatar.url if other.avatar else None,
                            "is_online": getattr(other, "is_online", False),
                        }
                    )
            except Exception:
                continue

        group_chats = GroupChat.objects.filter(members__user=user)

        if search:
            group_chats = group_chats.filter(name__icontains=search)

        for chat in group_chats[:20]:
            try:
                results.append(
                    {
                        "id": chat.id,
                        "type": "group",
                        "name": chat.name,
                        "avatar": chat.avatar.url if chat.avatar else None,
                        "members_count": chat.members_count,
                    }
                )
            except Exception:
                continue
    except Exception as e:
        import logging

        logging.getLogger(__name__).error(f"Error in get_chats_for_forward: {e}")

    return Response(results)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def forward_post_to_chat(request, chat_id=None):
    from types import SimpleNamespace
    from apps.social.application.post_actions import repost
    from apps.social.application.post_access import resolve_post_id
    if not request.data.get('post_id'):
        return Response({'detail': 'Выберите пост'}, status=400)
    values = request.data.dict() if hasattr(request.data, 'dict') else dict(request.data)
    values['chat_id'] = chat_id or values.get('chat_id')
    values['destination'] = 'chat'
    return Response(repost(SimpleNamespace(user=request.user, data=values, FILES=request.FILES), resolve_post_id(values['post_id'])))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_extended_feed(request):
    from apps.social.application.post_feed import page
    return Response(page(request, 'extended'))



class SubscriptionViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        sort = request.query_params.get("sort", "date")  
        search = request.query_params.get("search", "").strip()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        follows = Follow.objects.filter(follower=request.user).select_related(
            "following"
        )

        if search:
            follows = follows.filter(
                Q(following__username__icontains=search)
                | Q(following__display_name__icontains=search)
            )

        if sort == "name":
            follows = follows.order_by("following__display_name", "following__username")
        else:
            follows = follows.order_by("-created_at")

        total = follows.count()
        offset = (page - 1) * page_size
        follows_page = follows[offset : offset + page_size]

        from core.online_status import online_status as os_service

        results = []
        for follow in follows_page:
            u = follow.following
            is_online = False
            try:
                is_online = os_service.is_online(u.id)
            except Exception:
                pass
            results.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name or u.username,
                    "avatar_url": u.avatar.url if u.avatar else None,
                    "followers_count": Follow.objects.filter(following=u).count(),
                    "is_online": is_online,
                    "followed_at": follow.created_at.isoformat(),
                }
            )

        return Response(
            {
                "results": results,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )

    @action(detail=True, methods=["delete"])
    def unfollow(self, request, pk=None):
        target_user = get_object_or_404(User, id=pk)
        deleted, _ = Follow.objects.filter(
            follower=request.user, following=target_user
        ).delete()
        if deleted:
            return Response({"success": True, "message": "Вы отписались"})
        return Response({"error": "Вы не подписаны на этого пользователя"}, status=400)




class NotInterestedViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        search = request.query_params.get("search", "").strip()
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        qs = UserNotInterested.objects.filter(user=request.user).select_related(
            "target_user"
        )

        if search:
            qs = qs.filter(
                Q(target_user__username__icontains=search)
                | Q(target_user__display_name__icontains=search)
            )

        qs = qs.order_by("-created_at")
        total = qs.count()
        offset = (page - 1) * page_size
        page_qs = qs[offset : offset + page_size]

        results = []
        for item in page_qs:
            u = item.target_user
            results.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "display_name": u.display_name or u.username,
                    "avatar_url": u.avatar.url if u.avatar else None,
                    "hidden_at": item.created_at.isoformat(),
                }
            )

        return Response(
            {
                "results": results,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )

    def destroy(self, request, pk=None):
        target_user = get_object_or_404(User, id=pk)
        deleted, _ = UserNotInterested.objects.filter(
            user=request.user, target_user=target_user
        ).delete()
        if deleted:
            return Response(
                {"success": True, "message": "Пользователь убран из списка"}
            )
        return Response({"error": "Пользователь не найден в списке"}, status=404)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hide_author_from_feed(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        return Response({"error": "Нельзя скрыть самого себя"}, status=400)
    UserNotInterested.objects.get_or_create(user=request.user, target_user=target_user)
    return Response(
        {"success": True, "message": f"Посты от @{target_user.username} скрыты"}
    )




class ModerationReportViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _check_moderator(self, user):
        return (
            user.is_staff
            or user.is_superuser
            or getattr(user, "role", None) in ("moderator", "admin")
        )

    def list(self, request):
        if not self._check_moderator(request.user):
            return Response({"error": "Нет доступа"}, status=403)

        report_status = request.query_params.get("status", "pending")
        content_type = request.query_params.get("content_type", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))

        qs = Report.objects.select_related("reporter", "resolved_by")

        if report_status:
            qs = qs.filter(status=report_status)
        if content_type:
            qs = qs.filter(content_type=content_type)

        qs = qs.order_by("-created_at")
        total = qs.count()
        offset = (page - 1) * page_size
        page_qs = qs[offset : offset + page_size]

        results = []
        for report in page_qs:
            content_data = None
            if report.content_type == "post":
                try:
                    post = Post.objects.get(id=report.content_id)
                    content_data = {
                        "id": post.id,
                        "text": post.text[:200] if post.text else "",
                        "author": post.author.username if post.author else None,
                    }
                except Post.DoesNotExist:
                    pass
            elif report.content_type == "comment":
                from apps.social.infrastructure.models.social import PostComment

                try:
                    comment = PostComment.objects.get(id=report.content_id)
                    content_data = {
                        "id": comment.id,
                        "text": comment.content[:200] if comment.content else "",
                        "author": comment.author.username if comment.author else None,
                    }
                except Exception:
                    pass

            results.append(
                {
                    "id": report.id,
                    "content_type": report.content_type,
                    "content_id": report.content_id,
                    "reason": report.reason,
                    "comment": report.comment,
                    "status": report.status,
                    "reporter": {
                        "id": report.reporter.id,
                        "username": report.reporter.username,
                    },
                    "resolved_by": {
                        "id": report.resolved_by.id,
                        "username": report.resolved_by.username,
                    }
                    if report.resolved_by
                    else None,
                    "resolved_at": report.resolved_at.isoformat()
                    if report.resolved_at
                    else None,
                    "created_at": report.created_at.isoformat(),
                    "content": content_data,
                }
            )

        return Response(
            {
                "results": results,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )

    def partial_update(self, request, pk=None):
        from django.db import transaction
        from apps.social.application.post_access import is_post_moderator
        from apps.social.application.post_commands import delete_post
        from apps.social.application.post_comments import change_comment
        from apps.social.infrastructure.models.social import PostComment

        if not is_post_moderator(request.user):
            return Response({"error": "Нет доступа"}, status=403)
        new_status = request.data.get("status")
        action_type = request.data.get("action")
        if new_status not in ("resolved", "rejected"):
            return Response({"error": "Неверный статус"}, status=400)
        with transaction.atomic():
            report = get_object_or_404(Report.objects.select_for_update(), id=pk)
            if report.status != "pending":
                return Response({"error": "Жалоба уже рассмотрена"}, status=400)
            if action_type == "delete_content" and new_status == "resolved":
                if report.content_type == "post" and Post.objects.filter(pk=report.content_id).exists():
                    delete_post(report.content_id, request.user, moderation=True)
                elif report.content_type == "comment":
                    comment = PostComment.objects.filter(pk=report.content_id, post__is_deleted=False).first()
                    if comment:
                        change_comment(request, comment.post_id, comment.pk, delete=True, moderation=True)
            report.status = new_status
            report.resolved_by = request.user
            report.resolved_at = timezone.now()
            report.moderation_comment = request.data.get("moderator_comment", "")
            report.action_taken = action_type or ""
            report.save()
        return Response({"success": True, "report_id": str(report.pk), "status": report.status, "action": action_type})





@api_view(["GET"])
@permission_classes([AllowAny])
def get_franchise_discussions(request):
    from apps.anime.infrastructure.models.anime import Franchise
    from apps.social.infrastructure.models.social import GroupChat, ChatMember, ChatTopic

    franchise_groups = (
        GroupChat.objects.filter(discussion_type="franchise")
        .select_related("created_by")
        .prefetch_related("members")
    )

    result = []
    for group in franchise_groups:
        topics = ChatTopic.objects.filter(chat=group).order_by("order")[:10]

        members_count = group.members.count()

        result.append(
            {
                "id": group.id,
                "name": group.name,
                "franchise_id": group.franchise_id,
                "members_count": members_count,
                "topics_count": topics.count(),
            }
        )

    return Response({"results": result})


from apps.social.presentation.views.social_views import get_user_posts, get_group_posts, get_hashtag_posts


from apps.social.application.post_view_access import guard_actions
guard_actions(globals())
