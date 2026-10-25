from django.db.models import BigIntegerField, Count, F, OuterRef, Q, Subquery, Window
from django.db.models.functions import Coalesce, RowNumber
from rest_framework.response import Response

from apps.social.infrastructure.models.social import ChatMember, Message
from apps.social.infrastructure.models.conversation import ConversationUserState


def prepare_chat_list(chats, user, kind):
    if not chats:
        return
    field = 'private_chat_id' if kind == 'private' else 'chat_id'
    floors = ConversationUserState.objects.filter(user=user, conversation_id=OuterRef('conversation_id'))
    qs = Message.objects.filter(**{field + '__in': [chat.pk for chat in chats]}, is_deleted=False).filter(
        seq__gt=Coalesce(Subquery(floors.values('cleared_through_seq')[:1]), 0, output_field=BigIntegerField()))
    if kind == 'group':
        joined = ChatMember.objects.filter(user=user, chat_id=OuterRef('chat_id')).values('joined_at')[:1]
        qs = qs.filter(Q(chat__history_visible=True) | Q(created_at__gte=Subquery(joined)))
    unread = dict(qs.exclude(sender=user).exclude(read_statuses__user=user).order_by().values(field)
                  .annotate(total=Count('pk')).values_list(field, 'total'))
    parent_field = 'private_chat_id' if kind == 'private' else 'group_chat_id'
    chat_ids = [chat.pk for chat in chats]
    floor_values = dict(ConversationUserState.objects.filter(user=user,
        **{'conversation__' + parent_field + '__in': chat_ids}).values_list(
            'conversation__' + parent_field, 'cleared_through_seq'))
    joined_values = dict(ChatMember.objects.filter(user=user, chat_id__in=chat_ids).values_list(
        'chat_id', 'joined_at')) if kind == 'group' and any(not chat.history_visible for chat in chats) else {}
    branches = []
    for chat in chats:
        latest = Message.objects.filter(**{field: chat.pk}, is_deleted=False,
                                        seq__gt=floor_values.get(chat.pk, 0))
        if kind == 'group' and not chat.history_visible:
            if chat.pk not in joined_values:
                continue
            latest = latest.filter(created_at__gte=joined_values[chat.pk])
        branches.append(latest.order_by('-seq', '-pk').values_list('pk', flat=True)[:1])
    last_ids = list(branches[0].union(*branches[1:], all=True)) if branches else []
    last = {getattr(message, field): message for message in
            Message.objects.filter(pk__in=last_ids).select_related('sender')}
    for chat in chats:
        chat._list_unread_count = unread.get(chat.pk, 0)
        chat._list_last_message = last.get(chat.pk)
    users = [message.sender for message in last.values()]
    for chat in chats:
        if kind == 'private':
            users.extend([chat.user1, chat.user2])
        else:
            if chat.created_by:
                users.append(chat.created_by)
            for member in chat.members.all():
                member._state.fields_cache['chat'] = chat
                if member.role:
                    member.role._state.fields_cache['chat'] = chat
                users.append(member.user)
    from core.online_status import online_status
    online = online_status.get_users_data([user.pk for user in users])
    for participant in users:
        participant._list_online_data = online.get(participant.pk)
    if kind == 'group':
        from apps.anime.infrastructure.models.anime import Anime, Franchise
        franchises = {f.pk: f.name for f in Franchise.objects.filter(pk__in={c.franchise_id for c in chats if c.franchise_id})}
        posters = Anime.objects.filter(franchise_id__in={c.franchise_id for c in chats if c.franchise_id}).filter(
            Q(poster__gt='') | Q(poster_url__gt='')).annotate(position=Window(
                expression=RowNumber(), partition_by=F('franchise_id'), order_by=[F('franchise_order').asc(), F('pk').asc()]
            )).filter(position=1).order_by()
        posters = {anime.franchise_id: anime.poster.url if anime.poster else anime.poster_url for anime in posters}
        for chat in chats:
            chat._list_franchise_poster = posters.get(chat.franchise_id)
            chat._list_franchise_name = franchises.get(chat.franchise_id)


class ChatListMixin:
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        chats = list(page if page is not None else queryset)
        prepare_chat_list(chats, request.user, self.chat_kind)
        data = self.get_serializer(chats, many=True).data
        return self.get_paginated_response(data) if page is not None else Response(data)
