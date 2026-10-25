from django.db.models import Q, Count
from django.db import models
import logging

logger = logging.getLogger(__name__)

class SocialService:
    @staticmethod
    def build_unread_chats_data(user):
        from apps.social.infrastructure.models.social import (
            Message, MessageReadStatus, GroupChat, PrivateChat, ChatMember
        )
        
        chats_data = []
        member_chat_ids = ChatMember.objects.filter(user=user).values_list("chat_id", flat=True)
        private_chat_ids = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)
        ).values_list("id", flat=True)
        
        unread_messages = (
            Message.objects.filter(
                Q(chat_id__in=member_chat_ids) | Q(private_chat_id__in=private_chat_ids)
            )
            .exclude(sender=user)
            .exclude(read_statuses__user=user)
            .values('chat_id', 'private_chat_id')
            .annotate(unread_count=Count('id'))
        )
        
        group_chats = {c.id: c for c in GroupChat.objects.filter(id__in=member_chat_ids)}
        private_chats = {c.id: c for c in PrivateChat.objects.filter(id__in=private_chat_ids)}
        
        for item in unread_messages:
            chat_id = item.get('chat_id') or item.get('private_chat_id')
            if not chat_id:
                continue
                
            if item.get('chat_id'):
                chat = group_chats.get(chat_id)
                if chat:
                    avatar_url = None
                    try:
                        avatar_url = chat.avatar.url if chat.avatar else None
                    except Exception:
                        avatar_url = None
                    chats_data.append({
                        "id": chat.id,
                        "type": "group",
                        "name": chat.name,
                        "avatar_url": avatar_url,
                        "unread_count": item['unread_count'],
                    })
            else:
                chat = private_chats.get(chat_id)
                if chat:
                    other_user = chat.user1 if chat.user2 == user else chat.user2
                    avatar_url = None
                    try:
                        avatar_url = other_user.avatar.url if other_user.avatar else None
                    except Exception:
                        avatar_url = None
                    chats_data.append({
                        "id": chat.id,
                        "type": "private",
                        "name": other_user.display_name or other_user.username,
                        "avatar_url": avatar_url,
                        "unread_count": item['unread_count'],
                    })
        
        return chats_data
    
    @staticmethod
    def mark_chat_as_read(user, chat_id):
        from apps.social.infrastructure.models.social import (
            Message, MessageReadStatus, GroupChat, PrivateChat
        )
        
        chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
        if chat:
            unread_messages = Message.objects.filter(chat=chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )
            MessageReadStatus.objects.bulk_create(
                [MessageReadStatus(message=msg, user=user) for msg in unread_messages],
                ignore_conflicts=True
            )
            return {"message": "Групповой чат отмечен как прочитанный"}
        
        private_chat = PrivateChat.objects.filter(
            Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
        ).first()
        if private_chat:
            unread_messages = Message.objects.filter(private_chat=private_chat).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            )
            MessageReadStatus.objects.bulk_create(
                [MessageReadStatus(message=msg, user=user) for msg in unread_messages],
                ignore_conflicts=True
            )
            return {"message": "Личный чат отмечен как прочитанный"}
        
        return None
    
    @staticmethod
    def get_unread_count_data(user, chat_id=None):
        from apps.social.infrastructure.models.social import (
            Message, MessageReadStatus, GroupChat, PrivateChat, ChatMember
        )
        
        if chat_id:
            chat = GroupChat.objects.filter(id=chat_id, members__user=user).first()
            if chat:
                count = Message.objects.filter(chat=chat).exclude(
                    Q(sender=user) | Q(read_statuses__user=user)
                ).count()
                return {"unread_count": count}
            
            private_chat = PrivateChat.objects.filter(
                Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
            ).first()
            if private_chat:
                count = Message.objects.filter(private_chat=private_chat).exclude(
                    Q(sender=user) | Q(read_statuses__user=user)
                ).count()
                return {"unread_count": count}
            
            return {"unread_count": 0}
        else:
            member_chat_ids = ChatMember.objects.filter(user=user).values_list("chat_id", flat=True)
            private_chat_ids = PrivateChat.objects.filter(
                Q(user1=user) | Q(user2=user)
            ).values_list("id", flat=True)
            
            group_unread = Message.objects.filter(chat_id__in=member_chat_ids).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            ).count()
            
            private_unread = Message.objects.filter(private_chat_id__in=private_chat_ids).exclude(
                Q(sender=user) | Q(read_statuses__user=user)
            ).count()
            
            return {"unread_count": group_unread + private_unread}