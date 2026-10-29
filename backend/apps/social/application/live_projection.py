"""Batch current plain-message projections; rich content keeps the general reader.

There is no completed-result cache. Every batch reloads membership, bans,
clear/history bounds, read receipts and the current message from the database.
"""
import asyncio
import threading
from dataclasses import dataclass
from weakref import WeakKeyDictionary

from channels.db import database_sync_to_async
from django.db.models import Count, Exists, OuterRef, PositiveBigIntegerField, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.social.application import conversations as service
from apps.social.infrastructure.models.conversation import ChatEvent, ConversationUserState
from apps.social.infrastructure.models.social import ChatMember, GroupChat, PrivateChat, Message
from apps.social.infrastructure.models.social_chat import ChatBan
from apps.users.infrastructure.models.users import User
from core.socket_auth import SocketAuthBatcher

_formatters = threading.local()


def plain_payload(message):
    # Cache only viewer-free field metadata, not messages or access decisions.
    # to_representation takes its instance as an argument and does not retain it.
    formatter = getattr(_formatters, 'plain', None)
    if formatter is None:
        from apps.social.presentation.serializers.social_serializers import MessageSerializer
        formatter = _formatters.plain = MessageSerializer()
    return formatter.to_representation(message)


@dataclass(frozen=True)
class Projection:
    event_id: int
    user_id: int


@dataclass(frozen=True)
class ChatRead:
    kind: str
    chat_id: int
    user_id: int


def read_access_records(records):
    users = set(User.objects.filter(pk__in={row.user_id for row in records}, is_active=True).values_list('pk',flat=True))
    group_ids = {row.chat_id for row in records if row.kind == 'group'}
    private_ids = {row.chat_id for row in records if row.kind == 'private'}
    groups = dict(GroupChat.objects.filter(pk__in=group_ids).values_list('pk','is_public')) if group_ids else {}
    private = {pk:(a,b) for pk,a,b in PrivateChat.objects.filter(pk__in=private_ids).values_list('pk','user1_id','user2_id')} if private_ids else {}
    members = {(chat,uid):banned for chat,uid,banned in ChatMember.objects.filter(chat_id__in=group_ids,user_id__in=users).values_list('chat_id','user_id','is_banned')} if group_ids else {}
    banned = set(ChatBan.objects.filter(chat_id__in=group_ids,user_id__in=users).filter(
        Q(until_date__isnull=True)|Q(until_date__gt=timezone.now())).values_list('chat_id','user_id')) if group_ids else set()
    result={}
    for row in records:
        if row.kind == 'private':
            allowed=row.user_id in private.get(row.chat_id,())
        else:
            key=(row.chat_id,row.user_id)
            allowed=(row.chat_id in groups and key not in banned and
                (members.get(key) is False or key not in members and groups[row.chat_id]))
        result[row]=bool(row.user_id in users and allowed)
    return result


def plain_message(message):
    return (message and not message.is_deleted and message.message_type == 'regular'
        and not any((message.reply_to_id, message.forwarded_from_id, message.shared_post_id,
            message.shared_anime_id, message.shared_playlist_id, message.shared_shorts_id, message.media))
        and not message.attachments.all() and not message.content_attachments.all())


def plain_projections(event, message, users):
    chat = event.conversation.chat
    candidates = User.objects.filter(pk__in={user.pk for user in users}, is_active=True)
    state = ConversationUserState.objects.filter(conversation_id=event.conversation_id, user_id=OuterRef('pk'))
    candidates = candidates.annotate(projection_cleared=Coalesce(Subquery(state.values('cleared_through_seq')[:1]),
        Value(0), output_field=PositiveBigIntegerField()))
    if isinstance(chat, GroupChat):
        members = ChatMember.objects.filter(chat=chat, user_id=OuterRef('pk'))
        bans = ChatBan.objects.filter(chat=chat, user_id=OuterRef('pk')).filter(
            Q(until_date__isnull=True) | Q(until_date__gt=timezone.now()))
        candidates = candidates.annotate(projection_banned=Exists(bans),
            projection_member_banned=Subquery(members.values('is_banned')[:1]),
            projection_joined=Subquery(members.values('joined_at')[:1])).filter(projection_banned=False)
        membership = Q(projection_member_banned=False)
        if chat.is_public:
            membership |= Q(projection_member_banned__isnull=True)
        candidates = candidates.filter(membership)
    else:
        candidates = candidates.filter(pk__in=(chat.user1_id, chat.user2_id))
    unread = Message.objects.filter(conversation_id=event.conversation_id, is_deleted=False,
        seq__gt=OuterRef('projection_cleared')).exclude(sender_id=OuterRef('pk')).exclude(read_statuses__user_id=OuterRef('pk'))
    if isinstance(chat, GroupChat) and not chat.history_visible:
        candidates = candidates.filter(projection_joined__isnull=False)
        unread = unread.filter(created_at__gte=OuterRef('projection_joined'))
    unread = unread.order_by().values('conversation_id').annotate(total=Count('pk')).values('total')[:1]
    columns = ['pk', 'projection_cleared', 'projection_unread']
    if isinstance(chat, GroupChat):
        columns.append('projection_joined')
    rows = candidates.annotate(projection_unread=Subquery(unread)).values(*columns)
    common = plain_payload(message)
    readers = {receipt.user_id for receipt in message.read_statuses.all()}
    projected = {}
    for row in rows:
        uid = row['pk']
        if message.seq <= row['projection_cleared']:
            continue
        if isinstance(chat, GroupChat) and not chat.history_visible and message.created_at < row['projection_joined']:
            continue
        mine = message.sender_id == uid
        if isinstance(chat, GroupChat):
            read_by_other = mine and bool(readers - {uid})
        else:
            other = chat.user2_id if chat.user1_id == uid else chat.user1_id
            read_by_other = mine and other in readers
        projected[uid] = dict(service.event_envelope(event), unread_count=row['projection_unread'] or 0,
            message=dict(common, is_mine=mine, is_read_by_other=read_by_other))
    return projected


def project_records(records):
    users = {user.pk: user for user in User.objects.filter(pk__in={row.user_id for row in records}, is_active=True)}
    events = {event.pk: event for event in ChatEvent.objects.select_related(
        'conversation__private_chat', 'conversation__group_chat').filter(pk__in={row.event_id for row in records})}
    output = {row: None for row in records}
    for event_id, event in events.items():
        wanted = {row.user_id for row in records if row.event_id == event_id} & set(event.recipients) & users.keys()
        message = None
        if event.kind == 'new_message' and event.conversation_id:
            message = Message.objects.select_related('sender', 'private_chat', 'chat', 'pinned_by').prefetch_related(
                'read_statuses', 'attachments', 'content_attachments').filter(pk=(event.payload.get('message') or {}).get('id'),
                    conversation_id=event.conversation_id).first()
        if wanted and plain_message(message):
            projected = plain_projections(event, message, [users[uid] for uid in wanted])
        else:
            projected = {uid: service.event_for_user(event, users[uid]) for uid in wanted}
        for uid in wanted:
            output[Projection(event_id, uid)] = projected.get(uid)
    return output


_loops = WeakKeyDictionary()
_access_loops = WeakKeyDictionary()


async def can_read_chat(chat, user):
    loop=asyncio.get_running_loop()
    if loop not in _access_loops:
        _access_loops[loop]=SocketAuthBatcher(
            validator=database_sync_to_async(read_access_records,thread_sensitive=False),flush_delay=0.02,coalesce_between_batches=True)
    return await _access_loops[loop].check(ChatRead(service.chat_kind(chat),chat.pk,user.pk))


async def live_event(payload, user):
    if payload.get('action') != 'new_message' or not payload.get('event_id'):
        return await database_sync_to_async(service.live_event_for_user)(payload, user.pk, user=user)
    loop = asyncio.get_running_loop()
    if loop not in _loops:
        _loops[loop] = SocketAuthBatcher(
            validator=database_sync_to_async(project_records, thread_sensitive=False), flush_delay=0.02,coalesce_between_batches=True)
    return await _loops[loop].check(Projection(int(payload['event_id']), user.pk))
