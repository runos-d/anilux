from django.db.models import Q, Count, Exists, OuterRef, F
from apps.social.infrastructure.models.social import Message
from apps.social.infrastructure.models.conversation import ConversationUserState

class UnreadCountService:
    def queryset(self, user_id):
        hidden = ConversationUserState.objects.filter(conversation_id=OuterRef('conversation_id'), user_id=user_id).filter(
            Q(hidden=True) | Q(cleared_through_seq__gte=OuterRef('seq')))
        from apps.social.infrastructure.models.social_chat import ChatBan
        from django.utils import timezone
        bans = ChatBan.objects.filter(chat_id=OuterRef('chat_id'), user_id=user_id).filter(
            Q(until_date__isnull=True) | Q(until_date__gt=timezone.now()))
        return Message.objects.filter(
            Q(private_chat__user1_id=user_id) | Q(private_chat__user2_id=user_id) |
            Q(chat__members__user_id=user_id, chat__members__is_banned=False), is_deleted=False,
        ).exclude(sender_id=user_id).exclude(read_statuses__user_id=user_id).filter(~Exists(hidden), ~Exists(bans)).filter(Q(private_chat__isnull=False) |
            Q(chat__history_visible=True) | Q(created_at__gte=F('chat__members__joined_at')))

    def initialize(self, user_id):
        return self.get_total(user_id)

    def increment(self, chat_id, user_ids):
        return None

    def decrement(self, chat_id, user_id):
        return self.get_total(user_id)

    def get_total(self, user_id):
        return self.queryset(user_id).count()

    def get_for_chat(self, user_id, chat_id, chat_type=None):
        qs = self.queryset(user_id)
        if chat_type == 'private':
            return qs.filter(private_chat_id=chat_id).count()
        if chat_type == 'group':
            return qs.filter(chat_id=chat_id).count()
        return qs.filter(Q(private_chat__public_id=chat_id) | Q(chat__public_id=chat_id)).count()

    def get_all_chats(self, user_id):
        return {row['conversation_id']: row['count'] for row in self.queryset(user_id)
                .values('conversation_id').annotate(count=Count('pk'))}

unread_service = UnreadCountService()
