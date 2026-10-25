from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.social.infrastructure.models.social import GroupChat, ChatMember
from apps.social.infrastructure.models.social_chat import ChatTopic
from apps.social.presentation.serializers.social_serializers import GroupChatSerializer
from . import conversations as service


def _get_poster_url(obj, request=None):
    if obj is None:
        return None
    if getattr(obj, 'poster', None):
        return request.build_absolute_uri(obj.poster.url) if request else obj.poster.url
    return getattr(obj, 'poster_url', None)


def ensure_franchise_group(franchise_id, user):
    from apps.anime.infrastructure.models.anime import Franchise, Anime
    franchise = get_object_or_404(Franchise.objects.select_for_update(), pk=franchise_id)
    parts = list(Anime.objects.filter(franchise=franchise).order_by('franchise_order', 'year', 'pk'))
    chat = GroupChat.objects.filter(franchise_id=franchise.pk).order_by('pk').first()
    if chat is None:
        chat = GroupChat.objects.create(franchise_id=franchise.pk, name=franchise.name,
            description=franchise.description or '', is_public=True, discussion_type='franchise', folder_type='discussions')
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    service.check_access(chat, user)
    if chat.discussion_type != 'franchise':
        chat.discussion_type = 'franchise'
        chat.save(update_fields=['discussion_type'])
    ChatTopic.objects.get_or_create(chat=chat, anime=None, defaults={'title': franchise.name, 'order': 0})
    for index, part in enumerate(parts, 1):
        ChatTopic.objects.get_or_create(chat=chat, anime=part,
            defaults={'title': part.title_ru or part.title_en or f'Part {part.pk}', 'order': index})
    return chat, franchise, parts


def ensure_anime_group(anime_id, user):
    from apps.anime.infrastructure.models.anime import Anime
    anime = get_object_or_404(Anime.objects.select_related('franchise'), pk=anime_id)
    if anime.franchise_id:
        chat, franchise, parts = ensure_franchise_group(anime.franchise_id, user)
        return chat, anime, franchise, parts
    anime = Anime.objects.select_for_update().get(pk=anime.pk)
    chat = GroupChat.objects.filter(anime_id=anime.pk).order_by('pk').first()
    if chat is None:
        chat = GroupChat.objects.create(anime_id=anime.pk, name=anime.title_ru or anime.title_en,
            description=(anime.description or '')[:500], is_public=True, discussion_type='anime', folder_type='discussions')
    chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
    service.check_access(chat, user)
    return chat, anime, None, []


def discussion_data(chat, request, anime=None, franchise=None, parts=None):
    data = dict(GroupChatSerializer(chat, context={'request': request}).data)
    poster = _get_poster_url(franchise or anime, request)
    if not poster and parts:
        poster = next((_get_poster_url(part, request) for part in parts if _get_poster_url(part)), None)
    if not data.get('avatar'):
        data['avatar'] = poster
    topics = [{'id': topic.pk, 'chat_id': chat.public_id, 'title': topic.title, 'slug': topic.slug,
        'order': topic.order, 'anime_id': topic.anime_id,
        'anime_title': (topic.anime.title_ru or topic.anime.title_en) if topic.anime else None,
        'poster_url': _get_poster_url(topic.anime, request) if topic.anime else poster}
        for topic in ChatTopic.objects.filter(chat=chat).select_related('anime').order_by('order', 'pk')]
    data.update(topics=topics, user_joined=ChatMember.objects.filter(chat=chat, user=request.user).exists(),
        current_topic_id=next((topic['id'] for topic in topics if anime and topic['anime_id'] == anime.pk), None))
    if franchise:
        data.update(franchise_id=franchise.pk, franchise_poster=poster)
    return data


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_franchise_discussion_group(request, franchise_id):
    chat, franchise, parts = ensure_franchise_group(franchise_id, request.user)
    return Response(discussion_data(chat, request, franchise=franchise, parts=parts))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def join_franchise_discussion_group(request, franchise_id):
    chat, franchise, parts = ensure_franchise_group(franchise_id, request.user)
    service.join_group(chat, request.user)
    return Response(discussion_data(chat, request, franchise=franchise, parts=parts))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def get_anime_discussion_group(request, anime_id):
    chat, anime, franchise, parts = ensure_anime_group(anime_id, request.user)
    return Response(discussion_data(chat, request, anime=anime, franchise=franchise, parts=parts))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_anime_discussion_group(request, anime_id):
    chat, anime, franchise, parts = ensure_anime_group(anime_id, request.user)
    _, created = service.join_group(chat, request.user)
    return Response(discussion_data(chat, request, anime=anime, franchise=franchise, parts=parts), status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def join_anime_discussion_group(request, anime_id):
    chat, anime, franchise, parts = ensure_anime_group(anime_id, request.user)
    service.join_group(chat, request.user)
    return Response(discussion_data(chat, request, anime=anime, franchise=franchise, parts=parts))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def leave_anime_discussion_group(request, anime_id):
    chat, _, _, _ = ensure_anime_group(anime_id, request.user)
    service.leave_group(chat, request.user)
    return Response({'action': 'left', 'chat_id': chat.public_id})
