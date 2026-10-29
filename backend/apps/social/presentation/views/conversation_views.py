import hashlib
import json

from django.db import transaction
from django.db.models import Q
from rest_framework import generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from apps.social.application import conversations as service
from apps.social.infrastructure.models.social import Message, Attachment, MessageAttachment
from apps.social.infrastructure.models.conversation import ChatEvent
from apps.social.presentation.serializers.social_serializers import MessageSerializer, PrivateChatSerializer, GroupChatSerializer


def request_chat(request, identifier, kind=None):
    return service.resolve_chat(identifier, request.user,
        kind or request.query_params.get('type') or request.data.get('chat_type'))


def detail(chat, request):
    serializer = PrivateChatSerializer if service.chat_kind(chat) == 'private' else GroupChatSerializer
    data = dict(serializer(chat, context={'request': request}).data)
    data.update(type=service.chat_kind(chat), public_id=chat.public_id,
                conversation_id=service.get_conversation(chat).pk,
                unread_count=service.unread_count(chat, request.user))
    state = service.ConversationUserState.objects.filter(conversation=service.get_conversation(chat), user=request.user).first()
    data['cleared_through_seq'] = state.cleared_through_seq if state else 0
    return data


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chat_detail(request, pk):
    return Response(detail(request_chat(request, pk), request))


def detail_state(chat, user):
    state = service.ConversationUserState.objects.filter(conversation=service.get_conversation(chat), user=user).first()
    return state.cleared_through_seq if state else 0


def filter_topic(qs, chat, topic):
    if topic not in (None, '', 'main', 0, '0'):
        topic_id = service.validate_topic(chat, topic)
        from apps.social.infrastructure.models.social_chat import ChatTopic
        general = getattr(chat, 'discussion_type', None) == 'franchise' and ChatTopic.objects.filter(pk=topic_id, anime__isnull=True).exists()
        qs = qs.filter(Q(topic_id=topic_id) | Q(topic__isnull=True)) if general else qs.filter(topic_id=topic_id)
    return qs


def history(chat, user, *, before=None, topic=None, around=None, limit=50):
    qs = filter_topic(service.visible_messages(chat, user), chat, topic)
    if around:
        try:
            anchor = qs.get(pk=int(around))
        except (ValueError, TypeError, Message.DoesNotExist):
            raise ValidationError({'around': 'Сообщение недоступно в этой теме'})
        after = list(qs.filter(seq__gt=anchor.seq).order_by('seq').values_list('seq', flat=True)[:limit // 2])
        qs = qs.filter(seq__lte=after[-1] if after else anchor.seq)
    if before:
        try:
            qs = qs.filter(seq__lt=int(before))
        except (ValueError, TypeError):
            raise ValidationError({'before': 'Некорректный курсор'})
    qs = qs.select_related('sender', 'private_chat', 'chat', 'reply_to__sender', 'reply_to__topic')
    qs = qs.prefetch_related('read_statuses', 'attachments', 'content_attachments')
    page = list(qs.order_by('-seq', '-pk')[:limit + 1])
    more = len(page) > limit
    return list(reversed(page[:limit])), more


class MessageListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get(self, request, chat_id=None):
        chat = request_chat(request, chat_id or request.query_params.get('chat_id'))
        watermark = service.get_conversation(chat).event_seq
        messages, more = history(chat, request.user, before=request.query_params.get('before'), topic=request.query_params.get('topic_id'),
                                 around=request.query_params.get('around'))
        return Response({'results': MessageSerializer(messages, many=True, context={'request': request}).data,
                         'has_more': more, 'next_cursor': messages[0].seq if more else None,
                         'event_cursor': watermark, 'conversation_id': service.get_conversation(chat).pk,
                         'cleared_through_seq': detail_state(chat, request.user)})

    def post(self, request, chat_id=None):
        data = request.data
        chat = request_chat(request, chat_id or data.get('chat_id') or data.get('private_chat') or data.get('chat'),
                            'private' if data.get('private_chat') else None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        files = [f for key in request.FILES for f in request.FILES.getlist(key) if key.startswith('media_')]
        direct_file = request.FILES.get('media')
        all_files = files + ([direct_file] if direct_file else [])
        service.validate_message_file_size(all_files)
        cards = []
        from apps.anime.infrastructure.models.anime import Anime
        from apps.playlists.infrastructure.models.playlists import Playlist
        from apps.reactor.infrastructure.models.reactor import ReactorPost
        from apps.social.infrastructure.models.social import Post
        from apps.anime.models import Excerpt
        for prefix, kind, model in [('excerpt', 'excerpt', Excerpt), ('anime', 'anime', Anime), ('playlist', 'playlist', Playlist), ('shorts', 'shorts', ReactorPost), ('post', 'post', Post)]:
            ids = (data.getlist(prefix + '_ids[]') or data.getlist(prefix + '_ids')) if hasattr(data, 'getlist') else data.get(prefix + '_ids[]', data.get(prefix + '_ids', []))
            if isinstance(ids, (str, int)):
                ids = [ids]
            if len(ids) > 10:
                raise ValidationError({'attachments': 'Слишком много вложений'})
            for object_id in ids:
                obj = model.objects.filter(pk=object_id).first()
                if obj is None:
                    raise ValidationError({'attachments': 'Объект вложения не найден'})
                if kind == 'excerpt':
                    if obj.author_id != request.user.pk or not obj.anime.is_available:
                        raise ValidationError({'excerpt_ids': 'Отрывок недоступен или принадлежит другому автору'})
                else:
                    service.check_shareable(obj, request.user)
                cards.append((kind, obj.pk))
        digests = []
        for f in all_files:
            digest = hashlib.sha256()
            for chunk in f.chunks():
                digest.update(chunk)
            f.seek(0)
            digests.append([f.name, digest.hexdigest()])
        fingerprint = hashlib.sha256(json.dumps({'text': serializer.validated_data.get('text', '').strip(),
            'reply': getattr(serializer.validated_data.get('reply_to'), 'pk', None),
            'topic': service.validate_topic(chat, data.get('topic_id')), 'files': digests, 'cards': cards,
            'shared': {k: getattr(serializer.validated_data.get(k), 'pk', None) for k in ('shared_post', 'shared_anime', 'shared_playlist', 'shared_shorts')}}, sort_keys=True).encode()).hexdigest()
        for f in all_files:
            service.validate_upload(f)
        stored_files = []

        def attach(message):
            if message.media:
                stored_files.append(message.media)
            for f in files:
                kind = service.validate_upload(f)
                att = Attachment.objects.create(message=message, type=kind, file=f,
                    file_name=f.name, file_size=f.size, mime_type=f.content_type)
                stored_files.append(att.file)
            for kind, object_id in cards:
                if kind == 'excerpt':
                    from apps.anime.application.excerpts import enable_attachment
                    enable_attachment(object_id, request.user)
                MessageAttachment.objects.create(message=message, content_type=kind, object_id=object_id)

        try:
            message, created = service.send_message(chat, request.user, serializer.validated_data,
                attachments=attach if all_files or cards else None, fingerprint=fingerprint)
        except Exception:
            for f in stored_files:
                f.delete(save=False)
            raise
        return Response(MessageSerializer(message, context={'request': request}).data, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def edit_message(request, message_id):
    message = service.change_message(message_id, request.user, text=request.data.get('text'), version=request.data.get('version'))
    return Response(MessageSerializer(message, context={'request': request}).data)


@api_view(['POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def delete_message(request, message_id):
    service.change_message(message_id, request.user, delete=True)
    return Response(status=204)


class MessageDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_id):
        service.change_message(message_id, request.user, delete=True)
        return Response(status=204)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_private_chat_read(request, chat_id):
    return Response(service.mark_read(request_chat(request, chat_id, 'private'), request.user, request.data.get('message_ids')))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_group_chat_read(request, chat_id):
    return Response(service.mark_read(request_chat(request, chat_id, 'group'), request.user, request.data.get('message_ids')))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_chat_read(request, chat_id):
    return Response(service.mark_read(request_chat(request, chat_id), request.user, request.data.get('message_ids')))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_events(request, chat_id):
    chat = request_chat(request, chat_id)
    try:
        cursor = int(request.query_params.get('after', 0))
    except ValueError:
        raise ValidationError({'after': 'Некорректный курсор'})
    conversation = service.get_conversation(chat)
    rows = list(ChatEvent.objects.filter(conversation=conversation, sequence__gt=cursor).select_related(
        'conversation__private_chat', 'conversation__group_chat').order_by('sequence')[:201])
    events = [payload for e in rows[:200] if (payload := service.event_for_user(e, request.user)) is not None]
    return Response({'events': events, 'has_more': len(rows) > 200,
                     'cursor': rows[min(len(rows), 200) - 1].sequence if rows else cursor})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_messages(request):
    chat = request_chat(request, request.query_params.get('chat_id'))
    query = request.query_params.get('q', '').strip()
    qs = filter_topic(service.visible_messages(chat, request.user), chat, request.query_params.get('topic_id'))
    from rest_framework.serializers import DateField
    for param, lookup in [('date_from', 'created_at__date__gte'), ('date_to', 'created_at__date__lte')]:
        if request.query_params.get(param):
            qs = qs.filter(**{lookup: DateField().run_validation(request.query_params[param])})
    if request.query_params.get('media_type'):
        qs = qs.filter(media_type=request.query_params['media_type'])
    from django.db.models import Q
    from apps.anime.infrastructure.models.anime import Anime
    matching_anime = Anime.objects.filter(Q(title_ru__icontains=query) | Q(title_en__icontains=query) | Q(title_jp__icontains=query)).values('pk')
    qs = qs.filter(
        Q(text__icontains=query) | Q(shared_anime__title_ru__icontains=query) |
        Q(shared_anime__title_en__icontains=query) | Q(shared_anime__title_jp__icontains=query) |
        Q(content_attachments__content_type='anime', content_attachments__object_id__in=matching_anime)
    ).distinct().order_by('-seq')[:50] if query else []
    return Response(MessageSerializer(qs, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_chats(request):
    from django.db.models import Count
    from apps.social.application.unread_count_service import unread_service
    from apps.social.infrastructure.models.conversation import Conversation
    rows = list(unread_service.queryset(request.user.pk).values('conversation_id').annotate(count=Count('pk')))
    conversations = {c.pk: c for c in Conversation.objects.filter(pk__in=[r['conversation_id'] for r in rows])
                     .select_related('private_chat__user1', 'private_chat__user2', 'group_chat')}
    from apps.social.application.chat_notification_preferences import notification_preferences
    preferences = notification_preferences([conversation.chat for conversation in conversations.values()], request.user)
    result = []
    for row in rows:
        conv = conversations.get(row['conversation_id'])
        if conv and preferences.get((conv.kind, conv.chat.pk), False):
            chat = conv.chat
            other = chat.other_user(request.user) if conv.kind == 'private' else None
            avatar = other.avatar if other else chat.avatar
            result.append({'id': chat.public_id, 'conversation_id': conv.pk, 'type': conv.kind,
                           'name': (other.display_name or other.username) if other else chat.name,
                           'avatar_url': avatar.url if avatar else None, 'unread_count': row['count']})
    return Response(result)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_reaction_new(request, message_id):
    return Response(service.react(message_id, request.user, request.data.get('emoji'), request.data.get('active')))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def message_reactions(request, message_id):
    from apps.social.infrastructure.models.social_chat import MessageReaction
    service.accessible_message(message_id, request.user)
    return Response([{'id': r.pk, 'message': message_id, 'emoji': r.emoji,
        'user': {'id': r.user_id, 'username': r.user.username}, 'created_at': r.created_at}
        for r in MessageReaction.objects.filter(message_id=message_id).select_related('user')])


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pin_message(request, message_id):
    service.pin(message_id, request.user, True)
    return Response({'success': True, 'status': 'pinned'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unpin_message(request, message_id):
    service.pin(message_id, request.user, False)
    return Response({'success': True, 'status': 'unpinned'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pinned_messages(request, chat_id):
    chat = request_chat(request, chat_id)
    qs = service.visible_messages(chat, request.user).filter(is_pinned=True).order_by('-seq')[:100]
    return Response(MessageSerializer(qs, many=True, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def bulk_delete_messages(request, chat_id):
    chat = request_chat(request, chat_id, 'group')
    ids = request.data.get('message_ids')
    if not isinstance(ids, list) or len(ids) > 1000 or any(type(i) is not int for i in ids):
        raise ValidationError({'message_ids': 'Ожидается список до 1000 сообщений'})
    if Message.objects.filter(service.message_scope(chat), pk__in=ids).count() != len(set(ids)):
        raise ValidationError({'message_ids': 'Сообщения должны принадлежать этому чату'})
    for pk in sorted(set(ids)):
        service.change_message(pk, request.user, delete=True)
    return Response({'deleted_count': len(set(ids))})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_chat_history(request, chat_id):
    kind = 'private' if '/private-chats/' in request.path else None
    for_all = request.data.get('for_all', False)
    if type(for_all) is not bool:
        raise ValidationError({'for_all': 'Ожидается логическое значение'})
    count = service.clear_history(request_chat(request, chat_id, kind), request.user, for_all=for_all)
    return Response({'status': 'cleared', 'deleted_count': count, 'for_all': for_all})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def forward_message(request, message_id):
    original = service.accessible_message(message_id, request.user)
    from apps.users.application.privacy import can_forward_message
    if not can_forward_message(original, request.user):
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Автор запретил пересылку сообщений')
    if original.chat_id and original.chat.restrict_saving_content and original.sender_id != request.user.pk:
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('В этом чате запрещено сохранять и пересылать чужие сообщения')
    chat = request_chat(request, request.data.get('chat_id') or request.data.get('target_chat_id') or request.data.get('private_chat_id'),
        'private' if request.data.get('private_chat_id') else None)
    values = {k: getattr(original, k) for k in ('text', 'media', 'media_type', 'shared_post',
              'shared_anime', 'shared_playlist', 'shared_shorts')}
    values.update(client_message_id=request.data.get('client_message_id'), topic_id=request.data.get('topic_id'),
                  forwarded_from=original)
    from django.apps import apps
    content_models = {'anime': 'anime.Anime', 'playlist': 'playlists.Playlist',
                      'shorts': 'reactor.ReactorPost', 'post': 'social.Post', 'excerpt': 'anime.Excerpt'}
    cards = list(original.content_attachments.all())
    for card in cards:
        model = apps.get_model(content_models[card.content_type]) if card.content_type in content_models else None
        content = model.objects.filter(pk=card.object_id).first() if model else None
        if content is None:
            raise ValidationError('Объект вложения больше недоступен')
        service.check_shareable(content, request.user)
    def copy_attachments(message):
        for a in original.attachments.all():
            Attachment.objects.bulk_create([Attachment(message=message, **{f.name: getattr(a, f.name)
                for f in Attachment._meta.fields if f.name not in ('id', 'public_id', 'message', 'uploaded_at')})])
        for a in cards:
            MessageAttachment.objects.create(message=message, content_type=a.content_type, object_id=a.object_id, metadata=a.metadata)
    fingerprint = hashlib.sha256(json.dumps({'forward': original.pk, 'version': original.version,
        'topic': values['topic_id']}, sort_keys=True).encode()).hexdigest()
    message, created = service.send_message(chat, request.user, values,
        attachments=copy_attachments, fingerprint=fingerprint)
    return Response(MessageSerializer(message, context={'request': request}).data, status=201 if created else 200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_attachment(request, message_id):
    from apps.social.infrastructure.chat_storage import private_file_url
    attachment = service.add_attachment(message_id, request.user, request.FILES.get('file'))
    return Response({'success': True, 'id': attachment.pk,
        'url': private_file_url(attachment.file, request), 'file_name': attachment.file_name,
        'file_size': attachment.file_size, 'mime_type': attachment.mime_type, 'type': attachment.type}, status=201)
