from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import datetime, time, timedelta
from apps.users.infrastructure.models.users import NotificationSettings, MessageNotification, EmailLog
import json
from typing import Optional
import logging



logger = logging.getLogger(__name__)
class NotificationService:
    def __init__(self, user):
        self.user = user
        self.settings = self._get_notification_settings()

    def _get_notification_settings(self):
        return NotificationSettings.objects.get_or_create(user=self.user)[0]

    def should_send_push(self, notification_type: str, chat=None) -> bool:
        if not self.settings.push_enabled:
            return False

        if self._is_do_not_disturb():
            return False

        type_mapping = {
            'message': self.settings.message_notifications,
            'group': self.settings.group_notifications,
            'call': self.settings.call_notifications,
            'mention': self.settings.mention_notifications,
            'reaction': self.settings.reaction_notifications,
        }

        if notification_type in type_mapping and not type_mapping[notification_type]:
            return False

        if chat:
            from apps.social.infrastructure.models.social_chat import PrivateChatSettings, GroupMemberSettings
            from apps.social.infrastructure.models.social import PrivateChat, GroupChat
            
            try:
                if isinstance(chat, PrivateChat):
                    chat_settings = PrivateChatSettings.objects.filter(chat=chat, user=self.user).first()
                    if chat_settings:
                        if not chat_settings.notifications_enabled:
                            return False
                        if chat_settings.is_muted:
                            return False
                elif isinstance(chat, GroupChat):
                    from apps.social.infrastructure.models.social import ChatMember
                    member = ChatMember.objects.filter(chat=chat, user=self.user).first()
                    if member:
                        member_settings = getattr(member, 'personal_settings', None)
                        if member_settings:
                            if not member_settings.notifications_enabled:
                                return False
                            if member_settings.mentions_only and notification_type == 'message':
                                return False
                            if member_settings.is_muted:
                                return False
            except Exception:
                pass

        if chat and self.settings.override_chat_settings:
            pass

        return True

    def should_send_email(self, notification_type: str) -> bool:
        if not self.settings.email_enabled:
            return False

        if self.settings.email_frequency != 'immediately':
            last_email = EmailLog.objects.filter(
                user=self.user,
                sent_at__gte=timezone.now() - self._get_frequency_interval()
            ).exists()
            if last_email:
                return False

        type_mapping = {
            'message': self.settings.message_notifications,
            'group': self.settings.group_notifications,
            'mention': self.settings.mention_notifications,
        }

        if notification_type in type_mapping and not type_mapping[notification_type]:
            return False

        return True

    def _is_do_not_disturb(self) -> bool:
        if not self.settings.do_not_disturb_start or not self.settings.do_not_disturb_end:
            return False

        now = timezone.now().time()
        start = self.settings.do_not_disturb_start
        end = self.settings.do_not_disturb_end

        if start < end:
            return start <= now <= end
        else:  
            return now >= start or now <= end

    def _get_frequency_interval(self) -> timedelta:
        intervals = {
            'hourly': timedelta(hours=1),
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
        }
        return intervals.get(self.settings.email_frequency, timedelta(0))

    def send_push_notification(self, title: str, body: str, data: dict = None, chat=None) -> bool:
        payload = {
            'head': title,
            'body': body,
            'icon': '/static/icons/icon-192x192.png',
            'badge': '/static/icons/badge-96x96.png',
        }

        if data:
            payload.update(data)

        sound_url = '/static/sounds/notification.mp3'
        if chat:
            try:
                from apps.social.infrastructure.models.social_chat import PrivateChatSettings, GroupMemberSettings
                from apps.social.infrastructure.models.social import PrivateChat, GroupChat
                
                if isinstance(chat, PrivateChat):
                    chat_settings = PrivateChatSettings.objects.filter(chat=chat, user=self.user).first()
                    if chat_settings and chat_settings.sound_enabled and chat_settings.notification_sound != 'none':
                        sound_map = {
                            'default': '/static/sounds/notification.mp3',
                            'soft': '/static/sounds/soft.mp3',
                            'loud': '/static/sounds/loud.mp3',
                            'gentle': '/static/sounds/gentle.mp3',
                            'alert': '/static/sounds/alert.mp3',
                        }
                        sound_url = sound_map.get(chat_settings.notification_sound, '/static/sounds/notification.mp3')
                elif isinstance(chat, GroupChat):
                    from apps.social.infrastructure.models.social import ChatMember
                    member = ChatMember.objects.filter(chat=chat, user=self.user).first()
                    if member and hasattr(member, 'personal_settings'):
                        member_settings = member.personal_settings
                        if member_settings.sound_enabled and member_settings.notification_sound != 'none':
                            sound_map = {
                                'default': '/static/sounds/notification.mp3',
                                'soft': '/static/sounds/soft.mp3',
                                'loud': '/static/sounds/loud.mp3',
                                'gentle': '/static/sounds/gentle.mp3',
                                'alert': '/static/sounds/alert.mp3',
                            }
                            sound_url = sound_map.get(member_settings.notification_sound, '/static/sounds/notification.mp3')
            except Exception:
                pass

        if self.settings.push_sound:
            payload['sound'] = sound_url

        logger.info(f"Push notification to {self.user.username}: {title} - {body}")
        return True  

    def send_email_notification(self, subject: str, message: str, html_message: str = None) -> bool:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )

            EmailLog.objects.create(
                user=self.user,
                subject=subject,
                sent_at=timezone.now()
            )

            return True
        except Exception as e:
            logger.info(f"Ошибка отправки email: {e}")
            return False

    def send_message_notification(self, message, chat) -> bool:
        sender_name = message.sender.get_full_name() or message.sender.username

        push_sent = False
        if self.should_send_push('message', chat):
            title = f"{sender_name}"
            body = message.text[:100] if self.settings.push_preview else "Новое сообщение"

            push_sent = self.send_push_notification(title, body, {
                'chat_id': chat.id,
                'message_id': message.id,
                'type': 'new_message'
            }, chat)

        email_sent = False
        if self.should_send_email('message'):
            subject = f"Новое сообщение от {sender_name}"
            html_message = f"""
            <h3>Новое сообщение в {chat.name}</h3>
            <p><strong>{sender_name}:</strong> {message.text}</p>
            <p><a href="{settings.SITE_URL}/chat/{chat.id}/">Открыть чат</a></p>
            """

            email_sent = self.send_email_notification(subject, f"У вас новое сообщение", html_message)

            if email_sent:
                MessageNotification.objects.create(
                    user=self.user,
                    message=message,
                    notified_via='email',
                    notified_at=timezone.now()
                )

        return push_sent or email_sent

    def send_mention_notification(self, message, chat, mentioned_users) -> bool:
        if self.user not in mentioned_users:
            return False

        sender_name = message.sender.get_full_name() or message.sender.username

        push_sent = False
        if self.should_send_push('mention', chat):
            title = f"Вас упомянули"
            body = f"{sender_name}: {message.text[:100]}..."

            push_sent = self.send_push_notification(title, body, {
                'chat_id': chat.id,
                'message_id': message.id,
                'type': 'mention'
            }, chat)

        email_sent = False
        if self.should_send_email('mention'):
            subject = f"Вас упомянули в {chat.name}"
            html_message = f"""
            <h3>Упоминание в {chat.name}</h3>
            <p><strong>{sender_name}:</strong> {message.text}</p>
            <p><a href="{settings.SITE_URL}/chat/{chat.id}/">Открыть чат</a></p>
            """

            email_sent = self.send_email_notification(subject, f"Вас упомянули", html_message)

        return push_sent or email_sent

    def send_call_notification(self, caller, call_type='audio') -> bool:
        caller_name = caller.get_full_name() or caller.username

        push_sent = False
        if self.should_send_push('call'):
            title = f"Входящий {call_type} звонок"
            body = f"Звонок от {caller_name}"

            push_sent = self.send_push_notification(title, body, {
                'caller_id': caller.id,
                'call_type': call_type,
                'type': 'incoming_call'
            })

        from apps.notifications.application.services import NotificationService
        NotificationService.create_notification(
            user=self.user,
            notification_type='call',
            title=f"Входящий {call_type} звонок",
            body=f"Звонок от {caller_name}",
            link=f"/chats/{caller.id}",
            icon='📞',
        )

        return push_sent