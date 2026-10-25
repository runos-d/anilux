from django.shortcuts import get_object_or_404
from django.conf import settings as django_settings
from .chat_lookup import ChatLookupMixin
from datetime import timedelta
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.http import Http404
from django.db import models, transaction
from django.db.models import Q, F, Value, OuterRef, Subquery
from django.db.models.functions import Greatest
from asgiref.sync import async_to_sync
from rest_framework import generics, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from apps.social.application.unread_count_service import unread_service
from rest_framework.exceptions import APIException, PermissionDenied
from apps.social.application.post_access import readable_posts
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
)
from apps.social.infrastructure.models.social import MessageReadStatus
from apps.users.infrastructure.models.users import User
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
    ChatMemberSerializer,
    PrivateChatSerializer,
    PrivateChatCreateSerializer,
    FollowSerializer,
    PostCommentSerializer,
    PostCommentCreateSerializer,
)
from apps.social.application.chat_settings_service import SettingsCache
from apps.social.application.permissions import IsChatOwner
from apps.social.presentation.services.social_service import SocialService
from core.redis_events import (
    publish_post_created,
    publish_message_sent,
)
import logging

logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_unread_chats(request):
    try:
        if request.user and request.user.is_authenticated:
            chats_data = SocialService.build_unread_chats_data(request.user)
        else:
            chats_data = []
        return Response(chats_data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_chat_read(request, chat_id):
    return _mark_chat_as_read(request, chat_id)


def _mark_chat_as_read(request, chat_id):
    try:
        user = request.user
        result = SocialService.mark_chat_as_read(user, chat_id)
        if result is None:
            return Response({"error": "Чат не найден"}, status=404)
        return Response(result)
    except Exception as e:
        import traceback

        logger.debug(traceback.format_exc())
        return Response({"error": str(e)}, status=500)





@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_unread_count(request):
    user = request.user
    chat_id = request.query_params.get("chat_id")
    
    if chat_id:
        count = unread_service.get_for_chat(user.id, chat_id)
        return Response({"unread_count": count})
    else:
        total = unread_service.get_total(user.id)
        return Response({"unread_count": total})

class CombinedChatsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GroupChat.objects.none()

    def list(self, request):
        from .chat_lists import prepare_chat_list
        user = request.user
        data = []
        for kind, view_class in [('group', GroupChatViewSet), ('private', PrivateChatViewSet)]:
            view = view_class(request=request, action='list')
            queryset = view.get_queryset()
            if kind == 'group':
                queryset = queryset.filter(members__user=user)
            chats = list(queryset)
            prepare_chat_list(chats, user, kind)
            for chat in chats:
                last = chat._list_last_message
                item = {
                    'id': chat.public_id, 'public_id': chat.public_id, 'code': chat.code, 'type': kind,
                    'last_message_text': last.text if last else None,
                    'last_message_sender': last.sender.username if last else None,
                    'unread_count': chat._list_unread_count,
                    'updated_at': (chat.last_message_at or chat.created_at).isoformat(),
                    'created_at': chat.created_at.isoformat(),
                }
                if kind == 'private':
                    other = chat.user2 if chat.user1_id == user.pk else chat.user1
                    settings = next((setting for setting in chat.settings.all() if setting.user_id == user.pk), None)
                    avatar = settings.custom_avatar if settings and settings.custom_avatar else other.avatar
                    item.update(name=settings.custom_name if settings else None,
                        avatar_url=request.build_absolute_uri(avatar.url) if avatar else None,
                        other_user={'id': other.pk, 'username': other.username,
                            'display_name': other.display_name or other.username,
                            'avatar': request.build_absolute_uri(other.avatar.url) if other.avatar else None,
                            'is_online': bool(other._list_online_data)})
                else:
                    avatar = chat.avatar or (chat.anime.poster if chat.anime else None)
                    item.update(name=chat.name,
                        avatar_url=request.build_absolute_uri(avatar.url) if avatar else getattr(chat, '_list_franchise_poster', None),
                        franchise_id=chat.franchise_id, discussion_type=chat.discussion_type,
                        participants_usernames=[member.user.username for member in chat.members.all() if not member.is_banned])
                data.append(item)
        data.sort(key=lambda item: item['updated_at'], reverse=True)
        return Response(data)


def _resolve_chat_from_code_or_id(pk, user):
    try:
        num = int(pk)
    except (TypeError, ValueError):
        return None, None

    if 10000000 <= num <= 99999999:
        try:
            chat = GroupChat.objects.get(code=num, members__user=user)
            return chat, "group"
        except GroupChat.DoesNotExist:
            try:
                chat = GroupChat.objects.get(code=num, is_public=True)
                return chat, "group"
            except GroupChat.DoesNotExist:
                try:
                    chat = PrivateChat.objects.get(Q(code=num) & (Q(user1=user) | Q(user2=user)))
                    return chat, "private"
                except (PrivateChat.DoesNotExist, AttributeError):
                    pass

    try:
        chat = GroupChat.objects.get(public_id=pk, members__user=user)
        return chat, "group"
    except GroupChat.DoesNotExist:
        pass

    try:
        chat = GroupChat.objects.get(public_id=pk, is_public=True)
        return chat, "group"
    except GroupChat.DoesNotExist:
        pass

    try:
        chat = PrivateChat.objects.get(
            Q(public_id=pk) & (Q(user1=user) | Q(user2=user))
        )
        return chat, "private"
    except PrivateChat.DoesNotExist:
        pass

    return None, None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_chat_detail(request, pk):
    chat_type = request.query_params.get("type")
    try:
        logger.debug(f"Запрос деталей чата {pk} от пользователя {request.user.id}, type={chat_type}")
        chat = None

        if chat_type == "private":
            try:
                chat = PrivateChat.objects.get(
                    Q(public_id=pk) & (Q(user1=request.user) | Q(user2=request.user))
                )
                chat_type = "private"
            except PrivateChat.DoesNotExist:
                pass
        elif chat_type == "group":
            try:
                chat = GroupChat.objects.get(public_id=pk, members__user=request.user)
                chat_type = "group"
            except GroupChat.DoesNotExist:
                try:
                    chat = GroupChat.objects.get(public_id=pk, is_public=True)
                    chat_type = "group"
                except GroupChat.DoesNotExist:
                    pass

        if not chat:
            chat, chat_type = _resolve_chat_from_code_or_id(pk, request.user)

        if chat:
            pk = chat.pk

        if not chat:
            logger.debug(f"Чат {pk} не найден")
            return Response(
                {
                    "error": "Чат не найден",
                    "message": f"Чат с ID/кодом {pk} не существует или у вас нет к нему доступа",
                    "user_id": request.user.id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if chat_type == "private":
            try:
                private_chat = PrivateChat.objects.get(
                    Q(public_id=pk) & (Q(user1=request.user) | Q(user2=request.user))
                )
                logger.debug(f"Найден личный чат: {private_chat.id}")

                other_user = private_chat.other_user(request.user)

                try:
                    user_settings = PrivateChatUserSettings.objects.get(
                        chat=private_chat, user=request.user
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

                from core.online_status import online_status

                is_online = online_status.is_online(other_user.id)

                try:
                    from apps.social.application.unread_count_service import unread_service

                    unread_count_for_other = unread_service.get_for_chat(
                        other_user.id, private_chat.id
                    )
                except Exception as e:
                    logger.error(f"Ошибка подсчёта непрочитанных: {e}")
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

                try:
                    if request and request.user.is_authenticated:
                        settings = private_chat.get_user_settings(request.user)
                        other_user = private_chat.other_user(request.user)
                        if other_user:
                            other_settings = private_chat.get_user_settings(other_user)
                            current_user_blocked = settings.get("is_blocked", False)
                            other_user_blocked = other_settings.get("is_blocked", False)
                            chat_data["is_blocked"] = {
                                "blocked": current_user_blocked or other_user_blocked,
                                "current_user_blocked": current_user_blocked,
                                "other_user_blocked": other_user_blocked,
                            }
                        else:
                            chat_data["is_blocked"] = {
                                "blocked": False,
                                "current_user_blocked": False,
                                "other_user_blocked": False,
                            }
                    else:
                        chat_data["is_blocked"] = {
                            "blocked": False,
                            "current_user_blocked": False,
                            "other_user_blocked": False,
                        }
                except Exception as e:
                    logger.info(f"Error computing is_blocked for private chat: {e}")
                    chat_data["is_blocked"] = {
                        "blocked": False,
                        "current_user_blocked": False,
                        "other_user_blocked": False,
                    }

                logger.debug(
                    f"Возвращаем данные личного чата: name={custom_name}, avatar_url={custom_avatar_url}"
                )
                return Response(chat_data)

            except PrivateChat.DoesNotExist:
                logger.debug(f"Личный чат {pk} не найден или нет доступа (type=private)")
                return Response(
                    {
                        "error": "Чат не найден",
                        "message": f"Личный чат с ID {pk} не существует или у вас нет к нему доступа",
                        "user_id": request.user.id,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        if chat_type == "group":
            try:
                group_chat = GroupChat.objects.get(id=pk, members__user=request.user)
                logger.debug(f"Найден групповой чат: {group_chat.id}")

                serializer = GroupChatSerializer(group_chat, context={"request": request})
                data = serializer.data
                data["type"] = "group"

                logger.debug("Возвращаем данные группового чата")
                return Response(data)

            except GroupChat.DoesNotExist:
                try:
                    group_chat = GroupChat.objects.get(id=pk, is_public=True)
                    logger.debug(f"Найден публичный групповой чат: {group_chat.id}")
                    serializer = GroupChatSerializer(group_chat, context={"request": request})
                    data = serializer.data
                    data["type"] = "group"
                    return Response(data)
                except GroupChat.DoesNotExist:
                    logger.debug(f"Групповой чат {pk} не найден или нет доступа (type=group)")
                    return Response(
                        {
                            "error": "Чат не найден",
                            "message": f"Групповой чат с ID {pk} не существует или у вас нет к нему доступа",
                            "user_id": request.user.id,
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

        try:
            private_chat = PrivateChat.objects.get(
                Q(id=pk) & (Q(user1=request.user) | Q(user2=request.user))
            )
            logger.debug(f"Найден личный чат: {private_chat.id}")

            other_user = private_chat.other_user(request.user)

            try:
                user_settings = PrivateChatUserSettings.objects.get(
                    chat=private_chat, user=request.user
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

            from core.online_status import online_status

            is_online = online_status.is_online(other_user.id)

            try:
                from apps.social.application.unread_count_service import unread_service

                unread_count_for_other = unread_service.get_for_chat(
                    other_user.id, private_chat.id
                )
            except Exception as e:
                logger.error(f"Ошибка подсчёта непрочитанных: {e}")
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

            try:
                if request and request.user.is_authenticated:
                    settings = private_chat.get_user_settings(request.user)
                    other_user = private_chat.other_user(request.user)
                    if other_user:
                        other_settings = private_chat.get_user_settings(other_user)
                        current_user_blocked = settings.get("is_blocked", False)
                        other_user_blocked = other_settings.get("is_blocked", False)
                        chat_data["is_blocked"] = {
                            "blocked": current_user_blocked or other_user_blocked,
                            "current_user_blocked": current_user_blocked,
                            "other_user_blocked": other_user_blocked,
                        }
                    else:
                        chat_data["is_blocked"] = {
                            "blocked": False,
                            "current_user_blocked": False,
                            "other_user_blocked": False,
                        }
                else:
                    chat_data["is_blocked"] = {
                        "blocked": False,
                        "current_user_blocked": False,
                        "other_user_blocked": False,
                    }
            except Exception as e:
                logger.info(f"Error computing is_blocked for private chat: {e}")
                chat_data["is_blocked"] = {
                    "blocked": False,
                    "current_user_blocked": False,
                    "other_user_blocked": False,
                }

            logger.debug(
                f"Возвращаем данные личного чата: name={custom_name}, avatar_url={custom_avatar_url}"
            )
            return Response(chat_data)

        except PrivateChat.DoesNotExist:
            logger.debug(f"Личный чат {pk} не найден или нет доступа")
            pass

        try:
            group_chat = GroupChat.objects.get(id=pk, members__user=request.user)
            logger.debug(f"Найден групповой чат: {group_chat.id}")

            serializer = GroupChatSerializer(group_chat, context={"request": request})
            data = serializer.data
            data["type"] = "group"

            logger.debug("Возвращаем данные группового чата")
            return Response(data)

        except GroupChat.DoesNotExist:
            try:
                group_chat = GroupChat.objects.get(id=pk, is_public=True)
                logger.debug(f"Найден публичный групповой чат: {group_chat.id}")

                serializer = GroupChatSerializer(group_chat, context={"request": request})
                data = serializer.data
                data["type"] = "group"

                logger.debug("Возвращаем данные публичного группового чата")
                return Response(data)
            except GroupChat.DoesNotExist:
                logger.debug(f"Групповой чат {pk} не найден или нет доступа")
                pass

        return Response(
            {
                "error": "Чат не найден",
                "message": f"Чат с ID {pk} не существует или у вас нет к нему доступа",
                "user_id": request.user.id,
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    except Exception as e:
        logger.error(f"Ошибка в get_chat_detail: {str(e)}")
        import traceback

        logger.debug(traceback.format_exc())

        return Response(
            {"error": f"Ошибка сервера: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CommentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentCreateSerializer
        return CommentSerializer

    def get_queryset(self):
        content_type_str = self.request.query_params.get("content_type")
        object_id = self.request.query_params.get("object_id")

        if not content_type_str or not object_id:
            return Comment.objects.none()

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            return Comment.objects.filter(
                content_type=content_type, object_id=object_id, is_deleted=False
            ).select_related("author")
        except ContentType.DoesNotExist:
            return Comment.objects.none()

    def perform_create(self, serializer):
        content_type_str = self.request.data.get("content_type")
        object_id = self.request.data.get("object_id")

        try:
            content_type = ContentType.objects.get(model=content_type_str)
            serializer.save(
                author=self.request.user,
                content_type=content_type,
                object_id=object_id
            )
        except ContentType.DoesNotExist:
            raise serializer.ValidationError("Invalid content_type")


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.filter(is_deleted=False)
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if self.get_object().author != self.request.user:
            self.permission_denied(self.request, message="Cannot edit others' comments")
        serializer.save()




class FollowViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return Follow.objects.filter(follower=self.request.user)

    def get_followers_queryset(self):
        return Follow.objects.filter(following=self.request.user)

    def get_following_queryset(self):
        return Follow.objects.filter(follower=self.request.user)

    @action(detail=False, methods=["get"])
    def check(self, request):
        following_id = request.query_params.get("following_id")
        if not following_id:
            return Response({"error": "following_id required"}, status=400)

        try:
            target_user = User.objects.get(id=following_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        is_following = Follow.objects.filter(
            follower=request.user, following=target_user
        ).exists()

        return Response(
            {"is_following": is_following, "following_id": following_id}
        )

    @action(detail=False, methods=["get"])
    def followers(self, request):
        follows = self.get_followers_queryset().select_related("follower")
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
        return Response(data)

    @action(detail=False, methods=["get"])
    def following(self, request):
        follows = self.get_following_queryset().select_related("following")
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
        return Response(data)

    @action(detail=False, methods=["get"])
    def is_following(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "user_id required"}, status=400)

        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        is_following = Follow.objects.filter(
            follower=request.user, following=target_user
        ).exists()

        return Response({"is_following": is_following})




from apps.social.presentation.views.post_comments import PostCommentViewSet


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    from apps.social.application.post_comments import react_comment
    return Response(react_comment(request, comment_id, 'like'))



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_dislike(request, comment_id):
    from apps.social.application.post_comments import react_comment
    return Response(react_comment(request, comment_id, 'dislike'))



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def pin_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    if post.author != request.user:
        return Response({"error": "Нельзя закреплять чужие посты"}, status=403)

    Post.objects.filter(author=request.user, is_pinned=True).update(
        is_pinned=False, pinned_at=None
    )

    post.is_pinned = True
    post.pinned_at = timezone.now()
    post.save(update_fields=["is_pinned", "pinned_at"])

    return Response({"success": True, "message": "Пост закреплён", "is_pinned": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unpin_post(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    if post.author != request.user:
        return Response({"error": "Нельзя откреплять чужие посты"}, status=403)

    post.is_pinned = False
    post.pinned_at = None
    post.save(update_fields=["is_pinned", "pinned_at"])

    return Response({"success": True, "message": "Пост откреплён", "is_pinned": False})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_post(request, post_id):
    from types import SimpleNamespace
    from apps.social.presentation.views.views_all_actions import ReportViewSet
    payload = {**request.data, 'content_type': 'post', 'content_id': post_id}
    proxy = SimpleNamespace(user=request.user, data=payload)
    view = ReportViewSet()
    view.request = proxy
    return view.create(proxy)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_bookmark(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    folder = request.data.get("folder", "")

    existing_bookmark = Bookmark.objects.filter(user=request.user, post=post).first()

    if existing_bookmark:
        existing_bookmark.folder = folder
        existing_bookmark.save(update_fields=["folder"])
        return Response(
            {
                "success": True,
                "message": "Закладка обновлена",
                "bookmarked": True,
                "folder": folder,
            }
        )

    Bookmark.objects.create(user=request.user, post=post, folder=folder)

    return Response(
        {
            "success": True,
            "message": "Пост добавлен в закладки",
            "bookmarked": True,
            "folder": folder,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def remove_bookmark(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    deleted, _ = Bookmark.objects.filter(user=request.user, post=post).delete()

    if deleted:
        return Response(
            {"success": True, "message": "Пост удалён из закладок", "bookmarked": False}
        )

    return Response(
        {"success": True, "message": "Пост не был в закладках", "bookmarked": False}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_bookmarks_folders(request):
    folders_data = Bookmark.objects.filter(user=request.user).values_list(
        "folder", flat=True
    )
    folders = list(set(folders_data))
    folders = [f for f in folders if f]

    default_folders = ["watch_later", "favorite", "recipes"]
    all_folders = list(set(folders + default_folders))

    result = []
    for folder in all_folders:
        count = Bookmark.objects.filter(user=request.user, folder=folder).count()
        result.append({"name": folder, "count": count})

    total_count = Bookmark.objects.filter(user=request.user).count()
    result.insert(0, {"name": "all", "count": total_count})

    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_likers(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    likes = PostLike.objects.filter(post=post).select_related("user__profile")[:100]

    users = []
    for like in likes:
        users.append(
            {
                "id": like.user.id,
                "username": like.user.username,
                "avatar": like.user.profile.avatar.url
                if hasattr(like.user, "profile") and like.user.profile.avatar
                else None,
                "liked_at": like.created_at.isoformat(),
            }
        )

    return Response({"count": post.likes_count, "users": users})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_dislikers(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    if not request.user.is_staff and not request.user.is_superuser:
        return Response({"error": "Доступ запрещён"}, status=403)

    dislikes = PostDislike.objects.filter(post=post).select_related("user__profile")[
        :100
    ]

    users = []
    for dislike in dislikes:
        users.append(
            {
                "id": dislike.user.id,
                "username": dislike.user.username,
                "avatar": dislike.user.profile.avatar.url
                if hasattr(dislike.user, "profile") and dislike.user.profile.avatar
                else None,
                "disliked_at": dislike.created_at.isoformat(),
            }
        )

    return Response({"count": post.dislikes_count, "users": users})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def repost_post(request, post_id):
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    if original_post.author == request.user:
        return Response({"error": "Нельзя репостнуть свой пост"}, status=400)

    if original_post.post_type == "system":
        return Response({"error": "Нельзя репостнуть системный пост"}, status=400)

    if original_post.visibility == "private":
        return Response({"error": "Нельзя репостнуть приватный пост"}, status=400)

    comment = request.data.get("comment", "")
    chat_id = request.data.get("chat_id")
    repost_type = request.data.get("type", "feed")

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
                return Response({"error": "Чат не найден"}, status=404)

        if chat_type == "group":
            if not chat.members.filter(user=request.user).exists():
                return Response({"error": "Вы не состоите в этом чате"}, status=403)
        else:
            if chat.user1 != request.user and chat.user2 != request.user:
                return Response({"error": "Вы не состоите в этом чате"}, status=403)

        message = Message.objects.create(
            sender=request.user,
            shared_post=original_post,
            text=comment,
            chat=chat if chat_type == "group" else None,
            private_chat=chat if chat_type == "private" else None,
        )

        original_post.shares_count += 1
        original_post.save(update_fields=["shares_count"])

        from apps.social.presentation.serializers.social_serializers import MessageSerializer

        return Response(
            {
                "success": True,
                "message_text": "Пост переслан в чат",
                "message_id": message.id,
                "message": MessageSerializer(
                    message, context={"request": request}
                ).data,
            }
        )

    existing_repost = Repost.objects.filter(
        user=request.user, original_post=original_post
    ).first()

    if existing_repost:
        return Response({"error": "Вы уже репостнули этот пост"}, status=400)

    with transaction.atomic():
        new_post = Post.objects.create(
            author=request.user,
            post_type="repost",
            text=comment,
            status="published",
            visibility="public",
            allow_comments=True,
            original_post=original_post,
            repost_comment=comment,
        )

        Repost.objects.create(
            user=request.user, original_post=original_post, comment=comment
        )

        original_post.reposts_count += 1
        original_post.save(update_fields=["reposts_count"])

    return Response(
        {
            "success": True,
            "message": "Пост репостнут",
            "repost_id": new_post.id,
            "original_post_id": original_post.id,
            "post": PostSerializer(new_post, context={"request": request}).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def unrepost_post(request, post_id):
    try:
        original_post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    repost = Repost.objects.filter(
        user=request.user, original_post=original_post
    ).first()

    if not repost:
        return Response({"error": "Вы не репостнули этот пост"}, status=400)

    Post.objects.filter(author=request.user, type="repost").filter(
        attachments__content_type="repost", attachments__object_id=original_post.id
    ).delete()

    repost.delete()

    original_post.reposts_count = max(0, original_post.reposts_count - 1)
    original_post.save(update_fields=["reposts_count"])

    return Response({"success": True, "message": "Репост удалён"})




@api_view(["GET"])
@permission_classes([AllowAny])
def get_comment_replies(request, comment_id):
    try:
        comment = PostComment.objects.get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    max_depth = 3
    replies = (
        PostComment.objects.filter(parent=comment, is_deleted=False)
        .select_related("author")
        .annotate(likes_count_annotation=Count("likes"))
        .order_by("-likes_count_annotation", "created_at")[:20]
    )

    for reply in replies:
        if reply.level >= max_depth:
            reply.has_more_replies = True

    serializer = PostCommentSerializer(replies, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_comment(request, comment_id):
    from types import SimpleNamespace
    from apps.social.presentation.views.views_all_actions import ReportViewSet
    payload = {**request.data, 'content_type': 'comment', 'content_id': comment_id}
    proxy = SimpleNamespace(user=request.user, data=payload)
    view = ReportViewSet()
    view.request = proxy
    return view.create(proxy)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_feed_statistics(request):
    user = request.user

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
    period = request.query_params.get("period", "day")

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

    serializer = PostSerializer(queryset, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_posts(request, user_id):
    from apps.social.application.post_feed import chronological_page
    user = get_object_or_404(User, pk=user_id)
    return Response(chronological_page(request, Post.objects.filter(author=user), f'user:{user.pk}'))


@api_view(["GET"])
@permission_classes([AllowAny])
def get_group_posts(request, group_id):
    from apps.social.application.post_feed import chronological_page
    group = get_object_or_404(Group, pk=group_id)
    if group.is_private and (not request.user.is_authenticated or (group.creator_id != request.user.pk and not GroupMembership.objects.filter(group=group, user=request.user).exists())):
        return Response({'detail': 'Группа недоступна'}, status=403)
    return Response(chronological_page(request, Post.objects.filter(group=group), f'group:{group.pk}'))




@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_reports(request):
    import logging
    logger = logging.getLogger(__name__)

    try:
        status_filter = request.query_params.get("status")
        content_type_filter = request.query_params.get("content_type")
        page = int(request.query_params.get("page", 1))
        per_page = int(request.query_params.get("per_page", 20))

        queryset = Report.objects.select_related(
            'reporter', 'resolved_by'
        ).order_by('-created_at')

        if status_filter and status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        if content_type_filter:
            queryset = queryset.filter(content_type=content_type_filter)

        total = queryset.count()
        reports_page = queryset[(page - 1) * per_page:page * per_page]

        reports = []
        for report in reports_page:
            report_data = {
                'id': report.id,
                'reporter': {
                    'id': report.reporter.id,
                    'username': report.reporter.username,
                    'display_name': report.reporter.display_name
                },
                'content_type': report.content_type,
                'content_id': report.content_id,
                'reason': report.reason,
                'reason_display': dict(Report.REASON_CHOICES).get(report.reason),
                'comment': report.comment,
                'status': report.status,
                'status_display': dict(Report.STATUS_CHOICES).get(report.status),
                'created_at': report.created_at.isoformat(),
                'resolved_by': {
                    'id': report.resolved_by.id,
                    'username': report.resolved_by.username
                } if report.resolved_by else None,
                'resolved_at': report.resolved_at.isoformat() if report.resolved_at else None,
            }
            reports.append(report_data)

        return Response({
            'count': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'results': reports,
        })
    except Exception as e:
        logger.error(f"Error in get_reports: {e}", exc_info=True)
        return Response({"error": "Ошибка при загрузке жалоб", "detail": str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminUser])
def resolve_report(request, report_id):
    import logging
    logger = logging.getLogger(__name__)

    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        return Response({"error": "Жалоба не найдена"}, status=404)

    status = request.data.get("status")
    if status not in ["resolved", "rejected"]:
        return Response({"error": "Неверный статус"}, status=400)

    report.status = status
    report.resolved_by = request.user
    report.resolved_at = timezone.now()
    report.save()

    logger.info(f"Report {report_id} resolved by {request.user.username} as {status}")

    return Response({
        "success": True,
        "message": "Жалоба рассмотрена",
        "report": {
            "id": report.id,
            "status": report.status,
            "resolved_by": request.user.username,
            "resolved_at": report.resolved_at.isoformat()
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def hide_post_from_feed(request, post_id):
    try:
        Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    return Response({"success": True, "message": "Пост скрыт из ленты"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_post_not_interested(request, post_id):
    try:
        Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    return Response({"success": True, "message": "Пост отмечен как неинтересный"})




@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_post(request, post_id):
    from apps.social.application.post_commands import edit_post as command
    post = command(request, post_id, PostUpdateSerializer)
    return Response({'success': True, 'post': PostSerializer(post, context={'request': request}).data})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def edit_comment(request, comment_id):
    try:
        comment = PostComment.objects.select_related('parent').get(id=comment_id)
    except PostComment.DoesNotExist:
        return Response({"error": "Комментарий не найден"}, status=404)

    if comment.author != request.user:
        return Response({"error": "Нельзя редактировать чужие комментарии"}, status=403)

    if (timezone.now() - comment.created_at).total_seconds() > 600:
        return Response({"error": "Время на редактирование истекло"}, status=400)

    content = request.data.get("content")
    if not content:
        return Response({"error": "Комментарий не может быть пустым"}, status=400)

    if len(content) > 2000:
        return Response({"error": "Максимум 2000 символов"}, status=400)

    comment.content = content
    comment.is_edited = True
    comment.save()

    if comment.parent:
        comment.parent.replies_count = comment.parent.replies.filter(is_deleted=False).count()
        comment.parent.save(update_fields=["replies_count"])

    return Response(
        {
            "success": True,
            "message": "Комментарий обновлён",
            "comment": PostCommentSerializer(
                comment, context={"request": request}
            ).data,
        }
    )




@api_view(["GET"])
@permission_classes([AllowAny])
def get_hashtag_posts(request, tag_name):
    from apps.social.application.post_feed import chronological_page
    tag = tag_name.lstrip('#')
    data = chronological_page(request, Post.objects.filter(hashtag_links__hashtag__name__iexact=tag).distinct(), f'tag:{tag}')
    data['hashtag'] = tag
    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def search_hashtags(request):
    query = request.query_params.get("q", "")
    limit = int(request.query_params.get("limit", 10))

    if len(query) < 2:
        return Response({"results": []})

    hashtags = Hashtag.objects.filter(name__icontains=query).order_by("-posts_count")[
        :limit
    ]

    results = []
    for tag in hashtags:
        results.append({"id": tag.id, "name": tag.name, "posts_count": tag.posts_count})

    return Response({"results": results})




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def track_post_view(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    if post.author == request.user:
        return Response({"success": True, "message": "Просмотр засчитан (автор)"})

    existing_view = FeedView.objects.filter(user=request.user, post=post).first()

    if existing_view:
        return Response({"success": True, "message": "Уже просмотрено"})

    FeedView.objects.create(user=request.user, post=post)

    post.views_count += 1
    post.save(update_fields=["views_count"])

    return Response(
        {
            "success": True,
            "message": "Просмотр засчитан",
            "views_count": post.views_count,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_post_viewers(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return Response({"error": "Пост не найден"}, status=404)

    views = FeedView.objects.filter(post=post).select_related("user__profile")[:100]

    users = []
    for view in views:
        users.append(
            {
                "id": view.user.id,
                "username": view.user.username,
                "avatar": view.user.profile.avatar.url
                if hasattr(view.user, "profile") and view.user.profile.avatar
                else None,
                "viewed_at": view.viewed_at.isoformat(),
            }
        )

    return Response({"count": post.views_count, "users": users})




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_user_notification_settings(request):
    profile = request.user.profile if hasattr(request.user, "profile") else None

    settings = {
        "notify_likes": getattr(profile, "notify_likes", True) if profile else True,
        "notify_comments": getattr(profile, "notify_comments", True)
        if profile
        else True,
        "notify_mentions": True,
        "email_digest": getattr(profile, "email_digest", "never")
        if profile
        else "never",
    }

    return Response(settings)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_user_notification_settings(request):
    from apps.users.presentation.serializers.users_serializers import UserNotificationSettingsSerializer

    profile = request.user.profile if hasattr(request.user, "profile") else None
    if not profile:
        return Response({"error": "Профиль не найден"}, status=404)

    serializer = UserNotificationSettingsSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    validated = serializer.validated_data

    for field, value in validated.items():
        setattr(profile, field, value)

    profile.save()

    return Response({"success": True, "message": "Настройки обновлены"})

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            self.permission_denied(
                self.request, message="Cannot delete others' comments"
            )
        instance.is_deleted = True
        instance.save()


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Group.objects.all()
        if self.request.query_params.get('my_groups') == 'true':
            queryset = queryset.filter(Q(creator=self.request.user) | Q(memberships__user=self.request.user)).distinct()
        return queryset

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GroupCreateSerializer
        return GroupSerializer

    def perform_create(self, serializer):
        group = serializer.save(creator=self.request.user)

        GroupMembership.objects.create(user=self.request.user, group=group, role='admin')

        group.update_members_count()

        return group

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        group = self.get_object()
        if group.memberships.filter(user=request.user).exists():
            return Response(
                {"detail": "Already a member"}, status=status.HTTP_400_BAD_REQUEST
            )

        membership = GroupMembership.objects.create(user=request.user, group=group)
        group.update_members_count()
        return Response(GroupMembershipSerializer(membership).data)

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        group = self.get_object()
        membership = group.memberships.filter(user=request.user).first()
        if not membership:
            return Response(
                {"detail": "Not a member"}, status=status.HTTP_400_BAD_REQUEST
            )

        membership.delete()
        group.update_members_count()
        return Response({"detail": "Left group"})

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        group = self.get_object()
        memberships = group.memberships.all()
        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response(serializer.data)


class GroupSearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))

        if not search:
            return Response({"results": []})

        queryset = Group.objects.filter(
            Q(name__icontains=search) | Q(description__icontains=search),
            is_private=False,
        ).select_related("creator")

        queryset = queryset[:limit]

        serializer = GroupSerializer(queryset, many=True)

        return Response({"results": serializer.data, "count": len(serializer.data)})


class PostViewSet(ModelViewSet):
    queryset = Post.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'
    lookup_value_regex = r'\d+'

    def get_permissions(self):
        if self.action == 'public_retrieve':
            return [AllowAny()]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        import hashlib
        from apps.social.application.post_feed import chronological_page
        signature = '&'.join(f'{key}={request.query_params.getlist(key)}' for key in sorted(request.query_params)
                             if key not in ('cursor', 'page', 'page_size', 'limit'))
        queryset = self.filter_queryset(self._filtered_posts()).select_related(None).prefetch_related(None)
        return Response(chronological_page(request, queryset, 'posts:'+hashlib.sha256(signature.encode()).hexdigest(),
                                           include_own_pending=True))

    def get_object(self):
        from apps.social.application.post_access import resolve_post_id
        self.kwargs['pk'] = resolve_post_id(self.kwargs['pk'])
        return super().get_object()


    def retrieve(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)

        try:
            instance = self.get_object()
            logger.info(f"Retrieving post {instance.id} for user {request.user.id}")

            serializer = self.get_serializer(instance, context={"request": request})
            return Response(serializer.data)
        except (APIException, Http404):
            raise
        except Post.DoesNotExist:
            logger.warning(f"Post {kwargs.get('pk')} not found")
            return Response({"error": "Пост не найден"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Error retrieving post {kwargs.get('pk')}: {e}\n{error_traceback}")
            return Response(
                {"error": f"Ошибка получения поста: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        from apps.social.application.post_commands import delete_post
        from apps.social.application.post_access import resolve_post_id
        post = delete_post(resolve_post_id(kwargs['pk']), request.user)
        return Response({'success': True, 'post_id': str(post.pk)})

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        from apps.social.application.post_commands import publish_post
        from apps.social.application.post_access import resolve_post_id
        return Response(PostSerializer(publish_post(resolve_post_id(pk), request.user), context={'request': request}).data)

    @action(detail=True, methods=['post'], url_path='cancel-pending-edit')
    def cancel_pending(self, request, pk=None):
        from apps.social.application.post_commands import cancel_pending_edit
        from apps.social.application.post_access import resolve_post_id
        return Response(PostSerializer(cancel_pending_edit(resolve_post_id(pk), request.user), context={'request': request}).data)

    def get_serializer_class(self):
        if self.action == "create":
            return PostCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PostUpdateSerializer
        return PostSerializer

    @action(detail=True, methods=["get"], permission_classes=[AllowAny])
    def public_retrieve(self, request, pk=None):
        try:
            from apps.social.application.post_access import resolve_post_id
            post = self.get_queryset().get(id=resolve_post_id(pk))

            if post.visibility == "private":
                return Response(
                    {"error": "Пост недоступен"}, status=status.HTTP_403_FORBIDDEN
                )

            if post.group and post.group.is_private:
                return Response(
                    {"error": "Группа недоступна"}, status=status.HTTP_403_FORBIDDEN
                )

            from apps.social.presentation.serializers.social_serializers import PostSerializer

            serializer = PostSerializer(post, context={"request": request})
            return Response(serializer.data)
        except Post.DoesNotExist:
            return Response(
                {"error": "Пост не найден"}, status=status.HTTP_404_NOT_FOUND
            )

    def _filtered_posts(self):
        queryset = (
            Post.objects.filter(is_deleted=False)
            .select_related("author", "anime", "group", "playlist", "reactor_post", "original_post")
            .prefetch_related(
                "media_files",
                "attachments",
                "hashtag_links__hashtag",
            )
            .order_by("-created_at")
        )

        group_filter = self.request.query_params.get("group")
        if group_filter and group_filter != "true":
            try:
                group_id = int(group_filter)
                queryset = queryset.filter(group_id=group_id)
            except (ValueError, TypeError):
                pass
        elif group_filter == "true":
            queryset = queryset.exclude(group__isnull=True)

        anime_id = self.request.query_params.get("anime")
        if anime_id:
            try:
                queryset = queryset.filter(anime_id=anime_id)
            except (ValueError, TypeError):
                pass

        if self.request.query_params.get("feed") == "true":
            queryset = queryset.exclude(group__isnull=False)

        user = self.request.user
        if self.request.query_params.get('pending') == 'true':
            from apps.social.application.post_access import group_access
            return queryset.filter(group_access(user), author=user).filter(Q(status__in=['processing', 'failed']) | ~Q(pending_edit={}))
        if self.request.query_params.get('mine') == 'true':
            queryset = queryset.filter(author=user)
        if self.request.query_params.get('client_post_id'):
            queryset = queryset.filter(author=user, client_post_id=self.request.query_params['client_post_id'])
        return queryset

    def get_queryset(self):
        queryset = self._filtered_posts()
        user = self.request.user
        permitted = readable_posts(queryset, user, include_own_pending=True)
        from apps.social.application.post_feed import read_queryset
        return read_queryset(permitted, user)

    def create(self, request, *args, **kwargs):
        from apps.social.application.post_commands import create_post
        post, created = create_post(request, PostCreateSerializer)
        return Response(PostSerializer(post, context={'request': request}).data, status=201 if created else 200)

    def update(self, request, *args, **kwargs):
        from apps.social.application.post_commands import edit_post
        from apps.social.application.post_access import resolve_post_id
        post = edit_post(request, resolve_post_id(kwargs['pk']), PostUpdateSerializer, partial=kwargs.pop('partial', False))
        return Response(PostSerializer(post, context={'request': request}).data)


class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        chat_id = self.kwargs.get("chat_id")
        topic_id = self.request.query_params.get("topic_id")

        try:
            chat = GroupChat.objects.get(id=chat_id)
            is_member = ChatMember.objects.filter(
                chat=chat, user=self.request.user
            ).exists()
            if not is_member and not chat.is_public:
                return Message.objects.none()

            qs = Message.objects.filter(chat=chat, is_deleted=False).select_related(
                "sender", "reply_to__sender"
            )

            if topic_id is not None and topic_id != "":
                if topic_id == "main" or topic_id == "0":
                    pass
                else:
                    try:
                        tid = topic_id
                        qs = qs.filter(topic_id=tid)
                    except ValueError:
                        pass

            return qs
        except GroupChat.DoesNotExist:
            try:
                private_chat = PrivateChat.objects.get(id=chat_id)
                if self.request.user not in [private_chat.user1, private_chat.user2]:
                    return Message.objects.none()
                return Message.objects.filter(
                    private_chat=private_chat, is_deleted=False
                ).select_related("sender", "reply_to__sender")
            except PrivateChat.DoesNotExist:
                return Message.objects.none()

    def perform_create(self, serializer):
        from apps.social.application.chat_cache import ChatCacheService

        chat_id = (
            self.kwargs.get("chat_id")
            or self.request.data.get("chat_id")
            or self.request.data.get("private_chat")
            or self.request.data.get("chat")
        )
        topic_id = self.request.data.get("topic_id")

        if not chat_id:
            raise PermissionError("Не указан ID чата")

        try:
            chat = None
            private_chat = None

            try:
                chat = GroupChat.objects.get(id=chat_id)
                member = ChatMember.objects.filter(
                    chat=chat, user=self.request.user
                ).first()
                if not member:
                    if chat.is_public:
                        member, _ = ChatMember.objects.get_or_create(
                            chat=chat,
                            user=self.request.user,
                        )
                    else:
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
                    chat=chat,
                    private_chat=private_chat,
                    sender=self.request.user,
                    topic_id=topic_id,
                )


            except GroupChat.DoesNotExist:
                try:
                    private_chat = PrivateChat.objects.get(id=chat_id)
                    if self.request.user not in [
                        private_chat.user1,
                        private_chat.user2,
                    ]:
                        raise PermissionError("Нет доступа к чату")

                    settings = private_chat.get_user_settings(self.request.user)

                    other_user = private_chat.user1 if private_chat.user2 == self.request.user else private_chat.user2
                    other_settings = private_chat.get_user_settings(other_user)

                    if settings.get("is_blocked", False):
                        raise PermissionError("Чат заблокирован. Вы не можете отправлять сообщения.")
                    if other_settings.get("is_blocked", False):
                        raise PermissionError("Чат заблокирован. Пользователь не может получать сообщения.")

                    if settings.get("blocked", False):
                        raise PermissionError("Чат заблокирован")

                    message = serializer.save(
                        private_chat=private_chat,
                        sender=self.request.user,
                        topic_id=topic_id,
                    )

                except PrivateChat.DoesNotExist:
                    raise PermissionError("Чат не найден")

            if chat:
                chat.last_message_at = timezone.now()
                chat.save(update_fields=["last_message_at"])
            elif private_chat:
                private_chat.last_message_at = timezone.now()
                private_chat.save(update_fields=["last_message_at"])

            from apps.social.infrastructure.models.social import MessageAttachment, Attachment
            import os
            from mimetypes import guess_type

            data = self.request.data
            if hasattr(self.request, 'POST') and self.request.POST:
                attachment_ids = data.getlist('attachment_ids[]') or data.getlist('attachment_ids') or []
            else:
                attachment_ids = data.get('attachment_ids[]') or data.get('attachment_ids') or []
            if isinstance(attachment_ids, str):
                attachment_ids = [attachment_ids]

            media_files_uploaded = []
            for key in self.request.FILES.keys():
                if key.startswith('media_'):
                    media_files_uploaded.append(self.request.FILES[key])

            first_media_file = None
            first_media_type = None

            for media_file in media_files_uploaded:
                content_type = media_file.content_type or ''
                ext = os.path.splitext(media_file.name)[1].lower()

                if content_type.startswith('image/') or ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    att_type = 'image'
                elif content_type.startswith('video/') or ext in ['.mp4', '.webm', '.mov', '.avi']:
                    att_type = 'video'
                else:
                    att_type = 'file'

                Attachment.objects.create(
                    message=message,
                    type=att_type,
                    file=media_file,
                    file_name=media_file.name,
                    file_size=media_file.size,
                    mime_type=content_type or guess_type(media_file.name)[0] or ''
                )

                if first_media_file is None:
                    first_media_file = media_file
                    first_media_type = att_type

            if first_media_file:
                message.media = first_media_file
                message.media_type = first_media_type
                message.save(update_fields=['media', 'media_type'])

            if hasattr(self.request, 'POST') and self.request.POST:
                anime_ids = data.getlist('anime_ids[]') or data.getlist('anime_ids') or []
            else:
                anime_ids = data.get('anime_ids[]') or data.get('anime_ids') or []
            if isinstance(anime_ids, str):
                anime_ids = [anime_ids]
            for anime_id in anime_ids:
                if anime_id:
                    try:
                        from apps.anime.infrastructure.models.anime import Anime
                        anime = Anime.objects.get(id=anime_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='anime',
                            object_id=anime_id,
                            metadata={'title': anime.title_ru or anime.title_en}
                        )
                    except Anime.DoesNotExist:
                        pass

            if hasattr(self.request, 'POST') and self.request.POST:
                playlist_ids = data.getlist('playlist_ids[]') or data.getlist('playlist_ids') or []
            else:
                playlist_ids = data.get('playlist_ids[]') or data.get('playlist_ids') or []
            if isinstance(playlist_ids, str):
                playlist_ids = [playlist_ids]
            for playlist_id in playlist_ids:
                if playlist_id:
                    try:
                        from apps.playlists.infrastructure.models.playlists import Playlist
                        playlist = Playlist.objects.get(id=playlist_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='playlist',
                            object_id=playlist_id,
                            metadata={'title': playlist.title}
                        )
                    except Playlist.DoesNotExist:
                        pass

            if hasattr(self.request, 'POST') and self.request.POST:
                shorts_ids = data.getlist('shorts_ids[]') or data.getlist('shorts_ids') or []
            else:
                shorts_ids = data.get('shorts_ids[]') or data.get('shorts_ids') or []
            if isinstance(shorts_ids, str):
                shorts_ids = [shorts_ids]
            for shorts_id in shorts_ids:
                if shorts_id:
                    try:
                        from apps.reactor.infrastructure.models.reactor import ReactorPost
                        shorts = ReactorPost.objects.get(id=shorts_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='shorts',
                            object_id=shorts_id,
                            metadata={'title': shorts.title}
                        )
                    except ReactorPost.DoesNotExist:
                        pass

            if hasattr(self.request, 'POST') and self.request.POST:
                post_ids = data.getlist('post_ids[]') or data.getlist('post_ids') or []
            else:
                post_ids = data.get('post_ids[]') or data.get('post_ids') or []
            if isinstance(post_ids, str):
                post_ids = [post_ids]
            for post_id in post_ids:
                if post_id:
                    try:
                        post = Post.objects.get(id=post_id)
                        MessageAttachment.objects.create(
                            message=message,
                            content_type='post',
                            object_id=post_id,
                            metadata={'text': post.text[:100] if post.text else ''}
                        )
                    except Post.DoesNotExist:
                        pass

            ChatCacheService.add_message_to_cache(chat_id, message)

            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            message_data = MessageSerializer(message, context={"request": self.request}).data
            message_data.pop("is_mine", None)
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "chat_message",
                    "message": message_data,
                    "sender_id": self.request.user.id,
                },
            )

            from core.redis_events import event_publisher

            participant_ids = _chat_participant_ids(
                chat=message.chat, private_chat=message.private_chat
            )
            event_publisher.publish_event(
                "new_message",
                {
                    "message": message_data,
                    "chat_id": int(chat_id),
                    "chat_type": "private" if message.private_chat_id else "group",
                },
                target_users=[uid for uid in participant_ids if uid != self.request.user.id],
            )

            for uid in participant_ids:
                if uid == self.request.user.id:
                    continue
                try:
                    unread = unread_service.get_for_chat(uid, chat_id)
                except Exception:
                    unread = 0
                event_publisher.publish_event(
                    "unread_updated",
                    {"user_id": uid, "chat_id": int(chat_id), "unread_count": unread},
                    target_users=[uid],
                )

            from apps.social.application.tasks import process_message_post_save

            process_message_post_save.delay(message.id)

        except PermissionError as e:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied(str(e))
        except Exception as e:
            logger.error(f"Ошибка при сохранении: {e}")
            raise


class MessageDetailView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.filter(is_deleted=False)
    lookup_url_kwarg = "message_id"

    def destroy(self, request, *args, **kwargs):
        message = self.get_object()
        _soft_delete_message(message, request.user)
        return Response({"message": "Сообщение удалено"}, status=204)


def _soft_delete_message(message, user):
    from apps.social.application.chat_services import can_delete_message

    if not can_delete_message(user, message):
        raise PermissionDenied("Вы можете удалять только свои сообщения")

    message.is_deleted = True
    message.deleted_at = timezone.now()
    message.deleted_by = user
    message.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    try:
        chat_id = message.chat_id or message.private_chat_id
        if chat_id:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "message_deleted",
                    "message_id": message.id,
                    "chat_id": chat_id,
                },
            )
            _publish_chat_event(
                message, "message_deleted", {"message_id": message.id, "chat_id": chat_id}
            )
    except Exception as e:
        logger.error(f"Error sending WebSocket message: {e}")
    return message


def _chat_participant_ids(chat=None, private_chat=None):
    if private_chat is not None:
        return [private_chat.user1_id, private_chat.user2_id]
    if chat is not None:
        return list(
            ChatMember.objects.filter(chat=chat).values_list("user_id", flat=True)
        )
    return []


def _publish_chat_event(message, event_type, data):
    from core.redis_events import event_publisher

    event_publisher.publish_event(
        event_type,
        data,
        target_users=_chat_participant_ids(
            chat=message.chat, private_chat=message.private_chat
        ),
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    message = Message.objects.filter(id=message_id, is_deleted=False).first()
    if message is None:
        return Response({"error": "Сообщение не найдено"}, status=404)

    _soft_delete_message(message, request.user)
    return Response({"message": "Сообщение удалено"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def edit_message(request, message_id):
    message = Message.objects.filter(id=message_id, is_deleted=False).first()
    if message is None:
        return Response({"error": "Сообщение не найдено"}, status=404)

    if not message.can_edit(request.user):
        raise PermissionDenied("Редактировать можно только свои сообщения (48 часов)")

    text = (request.data.get("text") or "").strip()
    if not text:
        return Response({"error": "Текст не может быть пустым"}, status=400)

    message.text = text
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save(update_fields=["text", "is_edited", "edited_at"])

    data = MessageSerializer(message, context={"request": request}).data

    try:
        chat_id = message.chat_id or message.private_chat_id
        if chat_id:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{chat_id}",
                {
                    "type": "message_edited",
                    "message": data,
                },
            )
            _publish_chat_event(message, "message_edited", {"message": data})
    except Exception as e:
        logger.error(f"Error sending WebSocket message: {e}")

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_message_read(request, message_id):
    message = Message.objects.filter(id=message_id, is_deleted=False).first()
    if message is None:
        return Response({"error": "Сообщение не найдено"}, status=404)

    if message.private_chat_id:
        chat = message.private_chat
        if request.user.id not in (chat.user1_id, chat.user2_id):
            raise PermissionDenied("Нет доступа к чату")
    elif message.chat_id:
        if not ChatMember.objects.filter(
            chat_id=message.chat_id, user=request.user
        ).exists():
            raise PermissionDenied("Нет доступа к чату")
    else:
        raise PermissionDenied("Нет доступа к сообщению")

    from apps.social.infrastructure.models.social import MessageReadStatus

    MessageReadStatus.objects.get_or_create(message=message, user=request.user)
    try:
        unread_service.decrement(message.chat_id or message.private_chat_id, request.user.id)
    except Exception as e:
        logger.error(f"Error decrementing unread count: {e}")

    try:
        _publish_chat_event(
            message,
            "messages_read",
            {
                "chat_id": message.chat_id or message.private_chat_id,
                "message_ids": [message.id],
                "user_id": request.user.id,
                "read_at": timezone.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"Error publishing read event: {e}")

    return Response({"success": True})


class ChatRoleViewSet(ModelViewSet):
    serializer_class = ChatRoleSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if response.status_code >= 400:
            transaction.set_rollback(True)
        return response

    def parent_chat(self):
        if not hasattr(self, '_parent_chat'):
            from apps.social.application.conversations import resolve_chat
            chat = resolve_chat(self.kwargs['chat_pk'], self.request.user, 'group')
            if self.request.method not in ('GET', 'HEAD', 'OPTIONS'):
                chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
                member = ChatMember.objects.filter(chat=chat, user=self.request.user).first()
                from apps.social.application.chat_services import PermissionChecker
                if not PermissionChecker(self.request.user, chat)._is_owner():
                    raise PermissionDenied('Роли может менять только владелец')
            self._parent_chat = chat
        return self._parent_chat

    def get_queryset(self):
        return ChatRole.objects.filter(chat=self.parent_chat())

    def perform_create(self, serializer):
        serializer.save(chat=self.parent_chat(), created_by=self.request.user)
        self.publish_change()

    def perform_update(self, serializer):
        serializer.save()
        self.publish_change()

    def perform_destroy(self, instance):
        instance.delete()
        self.publish_change()

    def publish_change(self):
        from apps.social.application.conversations import record_event
        record_event(self.parent_chat(), 'member_updated', {})


from .chat_lists import ChatListMixin


class GroupChatViewSet(ChatListMixin, ChatLookupMixin, ModelViewSet):
    chat_kind = "group"
    queryset = GroupChat.objects.all()
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return GroupChatCreateSerializer
        return GroupChatSerializer
    def get_queryset(self):
        from apps.social.infrastructure.models.social_chat import ChatBan
        from django.utils import timezone
        banned = ChatBan.objects.filter(user=self.request.user).filter(Q(until_date__isnull=True) | Q(until_date__gt=timezone.now()))
        queryset = GroupChat.objects.filter(
            Q(members__user=self.request.user, members__is_banned=False) | Q(folder_type='discussions', is_public=True)
        ).exclude(pk__in=banned.values('chat_id')).exclude(pk__in=ChatMember.objects.filter(user=self.request.user, is_banned=True).values('chat_id')).select_related(
            'created_by', 'anime').prefetch_related('members', 'members__user', 'members__role', 'members__personal_settings').distinct().order_by('-last_message_at', '-created_at')
        search = self.request.query_params.get('search', '').strip()[:200]
        if search and self.action == 'list':
            from apps.anime.models import Anime, Franchise
            matching_anime = Anime.objects.filter(Q(title_ru__icontains=search) |
                Q(title_en__icontains=search) | Q(title_jp__icontains=search))
            queryset = queryset.filter(Q(name__icontains=search) | Q(anime__title_ru__icontains=search) |
                Q(anime__title_en__icontains=search) | Q(anime__title_jp__icontains=search) |
                Q(franchise_id__in=Franchise.objects.filter(name__icontains=search).values('id')) |
                Q(franchise_id__in=matching_anime.filter(franchise__isnull=False).values('franchise_id')))
        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        read_serializer = GroupChatSerializer(
            serializer.instance,
            context={"request": request},
        )
        return Response(
            read_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        chat = self.get_object()
        from apps.social.application.chat_services import PermissionChecker
        if chat.has_hidden_members and not PermissionChecker(request.user, chat).has_permission('can_manage_chat').allowed:
            raise PermissionDenied('Список участников скрыт')
        members_qs = ChatMember.objects.filter(chat=chat).select_related('user', 'role', 'chat')
        serializer = ChatMemberSerializer(members_qs, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        try:
            chat = serializer.save(created_by=self.request.user)

            ChatAdminLog.objects.create(
                chat=chat,
                user=self.request.user,
                action="chat_created",
                details={"chat_name": chat.name},
            )
        except Exception as e:
            logger.error(f"Ошибка создания группового чата: {e}")
            import traceback
            
            logger.debug(traceback.format_exc())
            raise

    @action(detail=True, methods=["post"])
    def leave_group_chat(self, request, pk=None):
        from apps.social.application.conversations import leave_group
        chat = self.get_object()
        leave_group(chat, request.user)
        return Response({'chat_id': chat.public_id, 'action': 'left'})

    @action(detail=True, methods=["post"])
    def delete_group_chat(self, request, pk=None):
        return self.destroy(request, pk=pk)

    def destroy(self, request, *args, **kwargs):
        from apps.social.application.conversations import delete_group
        chat = self.get_object()
        public_id = chat.public_id
        delete_group(chat, request.user)
        return Response({'chat_id': public_id, 'action': 'deleted'})


class PrivateChatViewSet(ChatListMixin, ChatLookupMixin, ModelViewSet):
    chat_kind = "private"

    queryset = PrivateChat.objects.all()
    lookup_field = 'pk'
    permission_classes = [IsAuthenticated]
    serializer_class = PrivateChatSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return PrivateChatCreateSerializer
        return PrivateChatSerializer

    def get_queryset(self):
        try:
            qs = (
                PrivateChat.objects.filter(
                    Q(user1=self.request.user) | Q(user2=self.request.user)
                )
                .select_related("user1", "user2")
                .prefetch_related('settings')
                .order_by("-last_message_at", "-created_at")
            )

            if self.action == 'list':
                from apps.social.infrastructure.models.conversation import ConversationUserState
                hidden = ConversationUserState.objects.filter(
                    user=self.request.user, hidden=True).values('conversation__private_chat_id')
                qs = qs.exclude(pk__in=hidden.filter(conversation__private_chat_id__isnull=False))
            return qs
        except Exception as e:
            logger.error(f"Ошибка получения личного чата: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return PrivateChat.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()

        created = getattr(serializer, "_created", True)
        chat_data = PrivateChatSerializer(chat, context={"request": request}).data

        if created:
            other_user = chat.user1 if chat.user2_id == request.user.id else chat.user2
            from apps.social.application.conversations import record_event
            record_event(chat, 'chat_created', {}, recipients=[request.user.pk, other_user.pk])

        return Response(
            chat_data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="administrator")
    def administrator(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return Response(
                {"detail": "Администратор открывает обращения в режиме поддержки."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = (
            self.get_queryset()
            .filter(is_support=True)
            .order_by("created_at")
            .first()
        )
        admin = existing.other_user(request.user) if existing else None
        if admin is None:
            admins = User.objects.filter(is_active=True).exclude(pk=request.user.pk).filter(
                Q(is_staff=True) | Q(is_superuser=True)
            )
            configured_id = getattr(django_settings, "SUPPORT_ADMIN_USER_ID", None)
            if configured_id:
                admin = admins.filter(pk=configured_id).first()
            admin = admin or admins.order_by("-is_superuser", "pk").first()
        if admin is None:
            return Response(
                {"detail": "Аккаунт администратора поддержки не настроен."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer = PrivateChatCreateSerializer(
            data={"user_id": admin.pk}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        chat = serializer.save()
        created = getattr(serializer, "_created", True)
        if not chat.is_support:
            chat.is_support = True
            chat.save(update_fields=["is_support"])

        prefix = "user1" if chat.user1_id == request.user.pk else "user2"
        type(chat).objects.filter(pk=chat.pk).update(**{
            f"{prefix}_archived": False,
            f"{prefix}_pinned": True,
        })
        from apps.social.application.conversations import get_conversation
        from apps.social.infrastructure.models.conversation import ConversationUserState
        from apps.social.infrastructure.models.social_chat import PrivateChatSettings
        conversation = get_conversation(chat)
        ConversationUserState.objects.filter(
            conversation=conversation, user=request.user
        ).update(hidden=False)
        PrivateChatSettings.objects.update_or_create(
            chat=chat,
            user=request.user,
            defaults={"is_hidden": False, "is_archived": False, "is_pinned": True},
        )
        chat.refresh_from_db()

        if created:
            from apps.social.application.conversations import record_event
            record_event(chat, "chat_created", {}, recipients=[request.user.pk, admin.pk])

        return Response(
            PrivateChatSerializer(chat, context={"request": request}).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        from apps.social.application.conversations import clear_history
        chat = self.get_object()
        clear_history(chat, request.user, hide=True)
        return Response({'chat_id': chat.public_id, 'action': 'deleted_for_both'})

from apps.social.application.post_view_access import guard_actions as _guard_post_actions
_guard_post_actions(globals())
