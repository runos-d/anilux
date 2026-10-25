from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count
from apps.social.infrastructure.models.social import Message, Attachment, EmailLog, GroupChat, PrivateChat, ChatMember, ChatAdminLog
from apps.users.infrastructure.models.users import User
import logging

logger = logging.getLogger(__name__)



@shared_task
def process_bulk_members(chat_id: int, user_ids: list, inviter_id: int):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        inviter = User.objects.get(id=inviter_id)

        added_count = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                if not ChatMember.objects.filter(chat=chat, user=user).exists():
                    ChatMember.objects.create(
                        user=user,
                        chat=chat,
                        can_send_messages=chat.can_send_media,
                        can_send_media=chat.can_send_media
                    )
                    added_count += 1
            except User.DoesNotExist:
                continue

        ChatAdminLog.objects.create(
            chat=chat,
            user=inviter,
            action='member_joined',
            details={'count': added_count, 'method': 'bulk_add_task'}
        )

        return {'success': True, 'added_count': added_count}
    
    except (GroupChat.DoesNotExist, User.DoesNotExist) as e:
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_messages(days: int = 30):
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_messages = Message.objects.filter(
        created_at__lt=cutoff_date,
        is_pinned=False,
        is_deleted=False
    )
    
    count = old_messages.count()
    
    old_messages.update(
        is_deleted=True,
        deleted_at=timezone.now()
    )
    
    logger.info(f"Cleaned up {count} old messages")
    return {'status': 'completed', 'deleted_count': count}


@shared_task
def cleanup_expired_bans():
    from apps.social.infrastructure.models.social_chat import ChatBan
    
    now = timezone.now()
    
    expired_bans = ChatBan.objects.filter(
        until_date__isnull=False,
        until_date__lt=now
    )
    
    count = expired_bans.count()
    expired_bans.delete()
    
    logger.info(f"Removed {count} expired bans")
    return {'status': 'completed', 'removed_count': count}


@shared_task
def cleanup_expired_restrictions():
    from apps.social.infrastructure.models.social_chat import ChatRestriction
    
    now = timezone.now()
    
    expired_restrictions = ChatRestriction.objects.filter(
        until_date__isnull=False,
        until_date__lt=now
    )
    
    count = expired_restrictions.count()
    expired_restrictions.delete()
    
    logger.info(f"Removed {count} expired restrictions")
    return {'status': 'completed', 'removed_count': count}


@shared_task
def cleanup_old_invites():
    from apps.social.infrastructure.models.social_chat import ChatInviteLink
    
    now = timezone.now()
    
    expired_invites = ChatInviteLink.objects.filter(
        expires_at__isnull=False,
        expires_at__lt=now,
        is_revoked=False
    )
    
    count = expired_invites.count()
    expired_invites.update(is_revoked=True)
    
    logger.info(f"Revoked {count} expired invites")
    return {'status': 'completed', 'revoked_count': count}


@shared_task
def update_members_count():
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        actual_count = chat.members.count()
        from apps.social.infrastructure.models.social_chat import GroupChatSettings
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        settings.members_count = actual_count
        settings.save(update_fields=['members_count'])
        updated_count += 1
    
    logger.info(f"Updated members count for {updated_count} chats")
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def update_online_counts():
    from core.online_status import online_status
    from apps.social.infrastructure.models.social_chat import GroupChatSettings
    
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        online_count = sum(
            1 for member in chat.members.all()
            if online_status.is_online(member.user_id)
        )
        
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        settings.online_count = online_count
        settings.save(update_fields=['online_count'])
        updated_count += 1
    
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def process_scheduled_messages():
    from apps.social.infrastructure.models.social_chat import ScheduledMessage
    
    now = timezone.now()
    
    scheduled = ScheduledMessage.objects.filter(
        status='scheduled',
        scheduled_at__lte=now
    )
    
    sent_count = 0
    failed_count = 0
    
    for scheduled_msg in scheduled:
        try:
            msg_data = {
                'sender': scheduled_msg.sender,
                'text': scheduled_msg.text,
                'media': scheduled_msg.media if scheduled_msg.media else None,
                'media_type': scheduled_msg.media_type,
            }
            
            if scheduled_msg.chat:
                msg_data['chat'] = scheduled_msg.chat
            elif scheduled_msg.private_chat:
                msg_data['private_chat'] = scheduled_msg.private_chat
            
            Message.objects.create(**msg_data)
            
            scheduled_msg.status = 'sent'
            scheduled_msg.sent_at = now
            scheduled_msg.save(update_fields=['status', 'sent_at'])
            
            if scheduled_msg.is_recurring and scheduled_msg.recurring_interval:
                next_date = now + timedelta(days=scheduled_msg.recurring_interval)
                ScheduledMessage.objects.create(
                    sender=scheduled_msg.sender,
                    chat=scheduled_msg.chat,
                    private_chat=scheduled_msg.private_chat,
                    text=scheduled_msg.text,
                    scheduled_at=next_date,
                    is_recurring=True,
                    recurring_interval=scheduled_msg.recurring_interval
                )
            
            sent_count += 1
            
        except Exception as e:
            scheduled_msg.status = 'failed'
            scheduled_msg.error_message = str(e)
            scheduled_msg.save(update_fields=['status', 'error_message'])
            failed_count += 1
            logger.error(f"Error sending scheduled message {scheduled_msg.id}: {e}")
    
    return {
        'status': 'completed',
        'sent_count': sent_count,
        'failed_count': failed_count
    }


@shared_task
def update_chat_statistics():
    from apps.social.infrastructure.models.social_chat import GroupChatSettings
    
    chats = GroupChat.objects.all()
    updated_count = 0
    
    for chat in chats:
        settings, _ = GroupChatSettings.objects.get_or_create(chat=chat)
        
        settings.messages_count = Message.objects.filter(chat=chat).count()
        settings.members_count = chat.members.count()
        
        last_msg = Message.objects.filter(chat=chat).order_by('-created_at').first()
        if last_msg:
            settings.last_message_at = last_msg.created_at
        
        today = timezone.now().replace(hour=0, minute=0, second=0)
        settings.daily_messages = Message.objects.filter(
            chat=chat,
            created_at__gte=today
        ).count()
        
        settings.save()
        updated_count += 1
    
    logger.info(f"Updated statistics for {updated_count} chats")
    return {'status': 'completed', 'updated_count': updated_count}


@shared_task
def detect_suspicious_activity():
    from apps.social.infrastructure.models.social_chat import SecurityLog
    
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    suspicious_ips = SecurityLog.objects.filter(
        action='login',
        created_at__gte=one_hour_ago
    ).values('ip_address').annotate(
        count=Count('id')
    ).filter(count__gte=5)
    
    marked_count = 0
    for entry in suspicious_ips:
        SecurityLog.objects.filter(
            ip_address=entry['ip_address'],
            created_at__gte=one_hour_ago
        ).update(is_suspicious=True)
        marked_count += 1
    
    logger.info(f"Marked {marked_count} IPs as suspicious")
    return {'status': 'completed', 'marked_count': marked_count}


@shared_task
def send_daily_digest():
    from apps.social.infrastructure.models.social import UserNotificationSettings
    
    users_with_digest = UserNotificationSettings.objects.filter(
        email_digest='daily'
    ).select_related('user')
    
    sent_count = 0
    for settings in users_with_digest:
        try:
            send_email_digest.delay(settings.user.id, 'daily')
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending digest to user {settings.user.id}: {e}")
    
    return {'status': 'completed', 'sent_count': sent_count}


@shared_task
def send_weekly_digest():
    from apps.social.infrastructure.models.social import UserNotificationSettings
    
    users_with_digest = UserNotificationSettings.objects.filter(
        email_digest='weekly'
    ).select_related('user')
    
    sent_count = 0
    for settings in users_with_digest:
        try:
            send_email_digest.delay(settings.user.id, 'weekly')
            sent_count += 1
        except Exception as e:
            logger.error(f"Error sending digest to user {settings.user.id}: {e}")
    
    return {'status': 'completed', 'sent_count': sent_count}


@shared_task
def invalidate_settings_cache():
    from apps.social.application.chat_services import settings_cache
    
    recent_chats = GroupChat.objects.filter(
        last_message_at__gte=timezone.now() - timedelta(hours=1)
    )
    
    count = 0
    for chat in recent_chats:
        settings_cache.invalidate_all_for_chat('group', chat.id)
        count += 1
    
    return {'status': 'completed', 'invalidated_count': count}


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def backup_chat_task(backup_id: int):
    from apps.social.application.chat_backups import build_backup
    from apps.social.infrastructure.models.social_chat import ChatBackup
    try:
        backup = build_backup(backup_id)
        return {'success': True, 'backup_id': backup.pk, 'messages_count': backup.messages_count,
                'members_count': backup.members_count, 'file_size': backup.file_size}
    except ChatBackup.DoesNotExist:
        return {'success': False, 'error': 'Backup not found'}


@shared_task
def requeue_pending_chat_backups():
    from apps.social.infrastructure.models.social_chat import ChatBackup
    cutoff = timezone.now() - timedelta(minutes=6)
    ids = list(ChatBackup.objects.filter(status='creating').filter(
        Q(processing_started_at__isnull=True) | Q(processing_started_at__lt=cutoff)
    ).order_by('created_at').values_list('pk', flat=True)[:100])
    for backup_id in ids:
        backup_chat_task.delay(backup_id)
    return {'queued': len(ids)}




@shared_task
def send_push_notification(user_id, notification_data):
    from apps.notifications.application.services import notification_service

    try:
        user = User.objects.get(id=user_id)
        notification_service.send_push(user, notification_data)
        return {'status': 'sent', 'user_id': user_id}
    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_email_digest(user_id, digest_type='daily'):
    try:
        user = User.objects.get(id=user_id)

        if digest_type == 'daily':
            since = timezone.now() - timedelta(days=1)
        else:
            since = timezone.now() - timedelta(weeks=1)

        unread_messages = []

        group_chats = GroupChat.objects.filter(members__user=user)
        for chat in group_chats:
            messages = Message.objects.filter(
                chat=chat,
                created_at__gte=since,
                is_deleted=False
            ).exclude(sender=user).count()

            if messages > 0:
                unread_messages.append({
                    'type': 'group',
                    'chat_id': chat.id,
                    'chat_name': chat.name,
                    'count': messages
                })

        private_chats = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)  
        )

        for chat in private_chats:
            messages = Message.objects.filter(
                private_chat=chat,
                created_at__gte=since,
                is_deleted=False
            ).exclude(sender=user).count()

            if messages > 0:
                other_user = chat.user1 if chat.user2 == user else chat.user2
                unread_messages.append({
                    'type': 'private',
                    'chat_id': chat.id,
                    'chat_name': other_user.username,
                    'count': messages
                })

        if not unread_messages:
            return {'status': 'skipped', 'message': 'No unread messages'}

        subject = f'Ваш {digest_type} дайджест на AniStream'
        message = render_to_string('emails/digest.html', {
            'user': user,
            'digest_type': digest_type,
            'messages': unread_messages,
            'site_url': settings.SITE_URL
        })

        send_mail(
            subject,
            '',  
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=message,
            fail_silently=False
        )

        EmailLog.objects.create(
            user=user,
            email_type=f'{digest_type}_digest',
            subject=subject,
            to_email=user.email,
            content=message,
            status='sent',
            sent_at=timezone.now()
        )

        return {'status': 'sent', 'user_id': user_id, 'messages_count': len(unread_messages)}

    except User.DoesNotExist:
        return {'status': 'error', 'message': 'User not found'}
    except Exception as e:
        try:
            EmailLog.objects.create(
                user_id=user_id,
                email_type=f'{digest_type}_digest',
                subject='Ошибка дайджеста',
                to_email='',
                content='',
                status='failed',
                error_message=str(e)
            )
        except Exception:
            pass

        return {'status': 'error', 'message': str(e)}


@shared_task
def send_mention_notification(message_id, mentioned_user_id):
    try:
        message = Message.objects.get(id=message_id)
        mentioned_user = User.objects.get(id=mentioned_user_id)

        notification_data = {
            'type': 'mention',
            'title': f'Вас упомянул {message.sender.username}',
            'body': message.text[:100] if message.text else 'Медиа-сообщение',
            'data': {
                'message_id': message.id,
                'chat_id': message.chat_id or message.private_chat_id,
                'sender_id': message.sender_id
            }
        }

        send_push_notification.delay(mentioned_user_id, notification_data)

        from apps.notifications.application.services import NotificationService
        NotificationService.create_notification(
            user=mentioned_user,
            notification_type='mention',
            title=f'Вас упомянул {message.sender.username}',
            content=message.text[:100] if message.text else 'Медиа-сообщение',
            link=f"/chats/{message.chat_id or message.private_chat_id}",
            icon='@',
            content_object=message,
        )

        from core.online_status import online_status
        if not online_status.is_online(mentioned_user_id):
            subject = f'Вас упомянули в чате'
            message_text = render_to_string('emails/mention.html', {
                'user': mentioned_user,
                'sender': message.sender,
                'message': message,
                'site_url': settings.SITE_URL
            })

            send_mail(
                subject,
                '',
                settings.DEFAULT_FROM_EMAIL,
                [mentioned_user.email],
                html_message=message_text,
                fail_silently=True
            )

            EmailLog.objects.create(
                user=mentioned_user,
                email_type='mention',
                subject=subject,
                to_email=mentioned_user.email,
                content=message_text,
                status='sent',
                message_id=message_id
            )

        return {'status': 'sent', 'user_id': mentioned_user_id}

    except (Message.DoesNotExist, User.DoesNotExist):
        return {'status': 'error', 'message': 'Message or user not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def cleanup_old_messages():
    cutoff_date = timezone.now() - timedelta(days=30)

    old_messages = Message.objects.filter(
        created_at__lt=cutoff_date,
        is_pinned=False,
        is_deleted=False
    )

    count = old_messages.count()

    old_messages.update(
        is_deleted=True,
        deleted_at=timezone.now()
    )

    return {'status': 'completed', 'deleted_count': count}


@shared_task
def cleanup_unused_attachments():
    unused_attachments = Attachment.objects.filter(
        Q(message__is_deleted=True) | Q(message__isnull=True)  
    )

    count = unused_attachments.count()

    for attachment in unused_attachments:
        if attachment.file:
            attachment.file.delete(save=False)
        if attachment.thumbnail:
            attachment.thumbnail.delete(save=False)

    unused_attachments.delete()

    return {'status': 'completed', 'deleted_count': count}


@shared_task
def generate_thumbnail_for_attachment(attachment_id):
    try:
        attachment = Attachment.objects.get(id=attachment_id)

        if attachment.type != 'image':
            return {'status': 'skipped', 'message': 'Not an image'}

        from PIL import Image
        import io
        from django.core.files.uploadedfile import InMemoryUploadedFile

        img = Image.open(attachment.file)

        attachment.width = img.width
        attachment.height = img.height
        attachment.save(update_fields=['width', 'height'])

        img.thumbnail((200, 200), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        buffer.seek(0)

        thumbnail_file = InMemoryUploadedFile(
            buffer,
            None,
            f'{attachment.id}_thumb.jpg',
            'image/jpeg',
            buffer.getbuffer().nbytes,
            None
        )
        attachment.thumbnail.save(f'{attachment.id}_thumb.jpg', thumbnail_file)
        attachment.save(update_fields=['thumbnail'])

        return {'status': 'completed', 'attachment_id': attachment_id}

    except Attachment.DoesNotExist:
        return {'status': 'error', 'message': 'Attachment not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def send_chat_invite_notification(chat_id, user_id, inviter_id):
    try:
        chat = GroupChat.objects.get(id=chat_id)
        user = User.objects.get(id=user_id)
        inviter = User.objects.get(id=inviter_id)

        notification_data = {
            'type': 'chat_invite',
            'title': f'Приглашение в чат {chat.name}',
            'body': f'{inviter.username} приглашает вас в чат',
            'data': {
                'chat_id': chat.id,
                'chat_name': chat.name,
                'inviter_id': inviter.id
            }
        }

        send_push_notification.delay(user_id, notification_data)

        return {'status': 'sent', 'user_id': user_id}

    except (GroupChat.DoesNotExist, User.DoesNotExist):
        return {'status': 'error', 'message': 'Chat or user not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def index_message_for_search(message_id):
    try:
        message = Message.objects.get(id=message_id)

        try:
            from elasticsearch import Elasticsearch
            es = Elasticsearch()
            es.index(
                index='messages',
                id=message_id,
                body={
                    'text': message.text,
                    'chat_id': message.chat_id,
                    'sender_id': message.sender_id,
                    'created_at': message.created_at,
                }
            )
        except ImportError:
            pass
        except Exception as e:
            logger.info(f"Elasticsearch indexing failed: {e}")

        return {'status': 'indexed', 'message_id': message_id}

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def archive_old_chats():
    from django.db.models import Count

    cutoff_date = timezone.now() - timedelta(days=90)

    inactive_group_chats = GroupChat.objects.annotate(
        message_count=Count('group_messages')
    ).filter(
        created_at__lt=cutoff_date,
        message_count__gt=0
    )


    return {'status': 'completed', 'checked_count': inactive_group_chats.count()}


@shared_task
def process_new_message(message_id):
    try:
        message = Message.objects.get(id=message_id)

        index_message_for_search.delay(message_id)

        if message.text:
            import re
            mentions = re.findall(r'@(\w+)', message.text)
            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    send_mention_notification.delay(message_id, mentioned_user.id)
                except User.DoesNotExist:
                    continue

        if message.media and message.media_type in ['image', 'video']:
            try:
                from apps.social.infrastructure.models.social import Attachment
                from PIL import Image
                import os
                
                file_size = message.media.size
                mime_type = getattr(message.media.file, 'content_type', 'application/octet-stream')
                
                attachment = Attachment.objects.create(
                    message=message,
                    type=message.media_type,
                    file=message.media,
                    file_name=os.path.basename(message.media.name),
                    file_size=file_size,
                    mime_type=mime_type,
                )
                
                if message.media_type == 'image':
                    try:
                        img = Image.open(message.media.path)
                        width, height = img.size
                        attachment.width = width
                        attachment.height = height
                        
                        thumb_size = (300, 300)
                        img.thumbnail(thumb_size)
                        thumb_path = f'attachments/thumbnails/thumb_{message.id}_{attachment.id}.jpg'
                        full_thumb_path = os.path.join(settings.MEDIA_ROOT, thumb_path)
                        img.save(full_thumb_path, 'JPEG', quality=85)
                        attachment.thumbnail = thumb_path
                        attachment.save()
                    except Exception as thumb_error:
                        logger.info(f"Failed to generate thumbnail: {thumb_error}")
                
            except Exception as attach_error:
                logger.info(f"Failed to create attachment: {attach_error}")

        process_message_post_save.delay(message_id)

        return {'status': 'completed', 'message_id': message_id}

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task
def process_message_post_save(message_id):
    import logging
    from apps.social.infrastructure.models.social import Message, PrivateChat, GroupChat
    from apps.social.application.unread_count_service import unread_service
    from django.utils import timezone

    logger = logging.getLogger(__name__)

    try:
        message = Message.objects.select_related('sender', 'chat', 'private_chat').get(id=message_id)
        sender = message.sender
        chat_id = message.chat_id or message.private_chat_id

        if not chat_id:
            return {'status': 'error', 'message': 'No chat ID'}

        if message.chat:
            recipient_ids = list(message.chat.members.exclude(user=sender).values_list('user_id', flat=True))
            if recipient_ids:
                unread_service.increment(chat_id, recipient_ids)
        elif message.private_chat:
            receiver = message.private_chat.user1 if message.private_chat.user2 == sender else message.private_chat.user2
            unread_service.increment(chat_id, [receiver.id])

        return {'status': 'success', 'message_id': message_id}

    except Message.DoesNotExist:
        return {'status': 'error', 'message': 'Message not found'}
    except Exception as e:
        logger.error(f"Error in process_message_post_save: {e}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def update_followers_feeds(post_id: int, author_id: int):
    from apps.social.infrastructure.models.social import Follow
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        follower_ids = list(Follow.objects.filter(
            following_id=author_id
        ).values_list('follower_id', flat=True))

        timestamp = timezone.now().timestamp()

        for follower_id in follower_ids:
            feed_cache.add_post_to_feed(follower_id, post_id, timestamp)

        logger.info(f"Updated feeds for {len(follower_ids)} followers of user {author_id}")
        return {'success': True, 'followers_count': len(follower_ids)}

    except Exception as e:
        logger.error(f"Error updating followers feeds: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_feed_posts():
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        feed_cache.invalidate_all_feeds()

        logger.info("Old feed posts cleaned up")
        return {'success': True}

    except Exception as e:
        logger.error(f"Error cleaning up feed: {e}")
        return {'error': str(e)}


@shared_task
def send_post_like_notification(post_id: int, user_id: int):
    from apps.social.infrastructure.models.social import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.select_related('author').get(id=post_id)
        user = post.author

        if user.id == user_id:
            return {'success': True, 'message': 'Self-like notification skipped'}

        if post.likes_count > 1:
            return {'success': True, 'message': 'Not first like'}

        try:
            from apps.notifications.infrastructure.models.notifications import Notification
            Notification.objects.create(
                user=user,
                type='like',
                title='Новый лайк',
                content=f'Ваш пост получил лайк',
                link=f'/post/{post_id}'
            )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error sending like notification: {e}")
        return {'error': str(e)}


@shared_task
def send_post_comment_notification(post_id: int, comment_id: int, author_id: int):
    from apps.social.infrastructure.models.social import Post, PostComment
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        comment = PostComment.objects.get(id=comment_id)

        try:
            from apps.notifications.infrastructure.models.notifications import Notification

            if post.author.id != author_id:
                Notification.objects.create(
                    user=post.author,
                    type='comment',
                    title='Новый комментарий',
                    content=f'К вашему посту оставили комментарий',
                    link=f'/post/{post_id}#comment-{comment_id}'
                )

            if comment.parent and comment.parent.author.id != author_id:
                Notification.objects.create(
                    user=comment.parent.author,
                    type='reply',
                    title='Новый ответ',
                    content=f'Вам ответили на комментарий',
                    link=f'/post/{post_id}#comment-{comment_id}'
                )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except (Post.DoesNotExist, PostComment.DoesNotExist) as e:
        return {'error': str(e)}
    except Exception as e:
        logger.error(f"Error sending comment notification: {e}")
        return {'error': str(e)}


@shared_task
def send_post_repost_notification(post_id: int, user_id: int):
    from apps.social.infrastructure.models.social import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        
        from apps.users.infrastructure.models.users import User
        from apps.notifications.infrastructure.models.notifications import Notification
        
        reposter = User.objects.get(id=user_id)
        
        if post.author_id == user_id:
            return {'success': True, 'message': 'Self-repost notification skipped'}
        
        Notification.objects.create(
            user=post.author,
            type='repost',
            title='Репост вашего поста',
            content=f'{reposter.username} репостнул ваш пост',
            link=f'/post/{post_id}'
        )
        
        return {'success': True}
    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending repost notification: {e}")
        return {'error': str(e)}


@shared_task
def notify_moderators_new_report(report_id: int):
    from apps.social.infrastructure.models.social import Report, Post, PostComment
    from apps.users.infrastructure.models.users import User
    from apps.notifications.infrastructure.models.notifications import Notification
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    try:
        report = Report.objects.select_related('reporter').get(id=report_id)

        moderator_username = getattr(settings, 'REPORTS_MODERATOR_USERNAME', 'moderator')
        moderator_email = getattr(settings, 'REPORTS_MODERATOR_EMAIL', '')

        moderator = User.objects.filter(username=moderator_username).first()

        if not moderator and moderator_email:
            moderator = User.objects.filter(email=moderator_email).first()

        if not moderator:
            moderator = User.objects.filter(is_staff=True, is_superuser=True).first()

        if not moderator:
            logger.warning(f"No moderator account found for report {report_id}")
            return {'error': 'No moderator account found'}

        content_type_display = 'Пост' if report.content_type == 'post' else 'Комментарий' if report.content_type == 'comment' else 'Пользователь'
        reason_display = dict(Report.REASON_CHOICES).get(report.reason, report.reason)

        content_preview = ''
        content_author = ''
        if report.content_type == 'post':
            try:
                post = Post.objects.get(id=report.content_id)
                content_preview = post.text[:100] if post.text else ''
                content_author = post.author.username
            except Post.DoesNotExist:
                pass
        elif report.content_type == 'comment':
            try:
                comment = PostComment.objects.get(id=report.content_id)
                content_preview = comment.content[:100] if comment.content else ''
                content_author = comment.author.username if comment.author else 'Удалён'
            except PostComment.DoesNotExist:
                pass
        elif report.content_type == 'user':
            try:
                target_user = User.objects.get(id=report.content_id)
                content_author = target_user.username
            except User.DoesNotExist:
                pass

        Notification.objects.create(
            user=moderator,
            type='system',
            title=f'🚨 Новая жалоба: {content_type_display}',
            content=f'Причина: {reason_display}\nАвтор: @{content_author}\nЖалоба от: @{report.reporter.username}',
            link=f'/moderation/reports/{report_id}'
        )

        logger.info(f"Moderator {moderator.username} notified about report {report_id}")
        return {'success': True, 'moderator_id': moderator.id}

    except Report.DoesNotExist:
        logger.error(f"Report {report_id} not found")
        return {'error': 'Report not found'}
    except Exception as e:
        logger.error(f"Error notifying moderators: {e}")
        return {'error': str(e)}


@shared_task
def send_mention_in_post_notification(post_id: int, user_id: int, mentioned_by_id: int):
    from apps.users.infrastructure.models.users import User
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = User.objects.get(id=user_id)
        mentioned_by = User.objects.get(id=mentioned_by_id)

        try:
            from apps.notifications.infrastructure.models.notifications import Notification
            Notification.objects.create(
                user=user,
                type='mention',
                title='Упоминание',
                content=f'{mentioned_by.username} упомянул вас в посте',
                link=f'/post/{post_id}'
            )
        except ImportError:
            logger.warning("Notifications app not available")

        return {'success': True}

    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending mention notification: {e}")
        return {'error': str(e)}


@shared_task
def update_post_popularity():
    from apps.social.infrastructure.models.social import Post
    import logging

    logger = logging.getLogger(__name__)

    try:
        yesterday = timezone.now() - timedelta(days=1)

        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=yesterday
        )

        logger.info(f"Updated popularity for {posts.count()} posts")
        return {'success': True, 'posts_count': posts.count()}

    except Exception as e:
        logger.error(f"Error updating popularity: {e}")
        return {'error': str(e)}


@shared_task
def reindex_post_for_search(post_id: int):
    import logging

    logger = logging.getLogger(__name__)

    try:
        logger.info(f"Reindexing post {post_id} for search")
        return {'success': True}

    except Exception as e:
        logger.error(f"Error reindexing post: {e}")
        return {'error': str(e)}


@shared_task
def process_post_hashtags(post_id: int):
    from django.db import models
    from apps.social.infrastructure.models.social import Post, PostHashtag, Hashtag
    import re
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        hashtags = re.findall(r'#([\w\-\u0400-\u04FF]+)', post.text)

        for tag_name in hashtags:
            tag, created = Hashtag.objects.get_or_create(name=tag_name.lower())
            PostHashtag.objects.get_or_create(post=post, hashtag=tag)

            Hashtag.objects.filter(id=tag.id).update(
                posts_count=models.F('posts_count') + 1
            )

        return {'success': True, 'hashtags_count': len(hashtags)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error processing hashtags: {e}")
        return {'error': str(e)}


@shared_task
def process_post_mentions(post_id: int):
    from apps.social.infrastructure.models.social import Post, UserMention
    from apps.users.infrastructure.models.users import User
    import re
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        mentions = re.findall(r'@(\w+)', post.text)

        for username in mentions:
            try:
                user = User.objects.get(username=username)
                if user != post.author:
                    UserMention.objects.get_or_create(post=post, user=user)
            except User.DoesNotExist:
                pass

        return {'success': True, 'mentions_count': len(mentions)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error processing mentions: {e}")
        return {'error': str(e)}


@shared_task
def calculate_post_popularity(post_id: int):
    from apps.social.infrastructure.models.social import Post
    import math
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)

        age_hours = (timezone.now() - post.created_at).total_seconds() / 3600
        if age_hours < 0.1:
            age_hours = 0.1

        score = (
            post.likes_count * 1 +
            post.comments_count * 2 +
            post.reposts_count * 3
        ) / math.pow(age_hours + 2, 1.5)

        from .feed_cache import feed_cache
        feed_cache.add_to_popular(post_id, score)

        return {'success': True, 'score': score}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error calculating popularity: {e}")
        return {'error': str(e)}


@shared_task
def sync_feed_views_to_db(post_id: int):
    from apps.social.infrastructure.models.social import Post
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        post = Post.objects.get(id=post_id)
        cached_views = feed_cache.get_views_count(post_id)

        if cached_views > 0:
            post.views_count = cached_views
            post.save(update_fields=['views_count'])

        return {'success': True, 'views_synced': cached_views}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error syncing views: {e}")
        return {'error': str(e)}


@shared_task
def send_like_notification(post_id: int, user_id: int):
    from apps.social.infrastructure.models.social import Post
    from apps.users.infrastructure.models.users import User
    from apps.notifications.infrastructure.models.notifications import Notification

    try:
        post = Post.objects.get(id=post_id)
        user = User.objects.get(id=user_id)

        if post.author == user:
            return {'skipped': 'Cannot notify yourself'}

        profile = getattr(post.author, 'profile', None)
        if profile and not getattr(profile, 'notify_likes', True):
            return {'skipped': 'User disabled like notifications'}

        if post.likes_count > 1:
            return {'skipped': 'Not the first like'}

        Notification.objects.create(
            user=post.author,
            type='like',
            title='Новый лайк',
            content=f'{user.username} лайкнул ваш пост',
            link=f'/post/{post.id}'
        )

        return {'success': True, 'notification_id': post.id}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending like notification: {e}")
        return {'error': str(e)}


@shared_task
def send_comment_notification(post_id: int, comment_id: int, parent_comment_id: int = None):
    from apps.social.infrastructure.models.social import Post, PostComment
    from apps.users.infrastructure.models.users import User
    from apps.notifications.infrastructure.models.notifications import Notification

    try:
        post = Post.objects.get(id=post_id)
        comment = PostComment.objects.get(id=comment_id)

        recipients = set()

        if post.author != comment.author:
            recipients.add(post.author)

        if parent_comment_id:
            try:
                parent_comment = PostComment.objects.get(id=parent_comment_id)
                if parent_comment.author != comment.author:
                    recipients.add(parent_comment.author)
            except PostComment.DoesNotExist:
                pass

        if comment.parent:
            ancestors = comment.parent.get_ancestors()
            for ancestor in ancestors:
                if ancestor.author != comment.author:
                    recipients.add(ancestor.author)

        for recipient in recipients:
            profile = getattr(recipient, 'profile', None)
            if profile and not getattr(profile, 'notify_comments', True):
                continue

            Notification.objects.create(
                user=recipient,
                type='comment',
                title='Новый комментарий',
                content=f'{comment.author.username} прокомментировал ваш пост',
                link=f'/post/{post.id}?comment={comment.id}'
            )

        return {'success': True, 'notifications_sent': len(recipients)}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except PostComment.DoesNotExist:
        return {'error': 'Comment not found'}
    except Exception as e:
        logger.error(f"Error sending comment notification: {e}")
        return {'error': str(e)}


@shared_task
def send_mention_notification(post_id: int, mentioned_user_id: int):
    from apps.social.infrastructure.models.social import Post
    from apps.users.infrastructure.models.users import User
    from apps.notifications.infrastructure.models.notifications import Notification

    try:
        post = Post.objects.get(id=post_id)
        mentioned_user = User.objects.get(id=mentioned_user_id)

        if post.author == mentioned_user:
            return {'skipped': 'Cannot notify yourself'}

        Notification.objects.create(
            user=mentioned_user,
            type='mention',
            title='Упоминание',
            content=f'{post.author.username} упомянул вас в посте',
            link=f'/post/{post.id}'
        )

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending mention notification: {e}")
        return {'error': str(e)}


@shared_task
def send_repost_notification(original_post_id: int, user_id: int):
    from apps.social.infrastructure.models.social import Post
    from apps.users.infrastructure.models.users import User
    from apps.notifications.infrastructure.models.notifications import Notification

    try:
        original_post = Post.objects.get(id=original_post_id)
        user = User.objects.get(id=user_id)

        if original_post.author == user:
            return {'skipped': 'Cannot notify yourself'}

        Notification.objects.create(
            user=original_post.author,
            type='repost',
            title='Новый репост',
            content=f'{user.username} сделал репост вашего поста',
            link=f'/post/{original_post.id}'
        )

        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Error sending repost notification: {e}")
        return {'error': str(e)}


@shared_task
def update_post_popularity_scores():
    from apps.social.infrastructure.models.social import Post
    from django.utils import timezone
    import math

    try:
        since = timezone.now() - timedelta(days=7)
        posts = Post.objects.filter(
            status='published',
            created_at__gte=since
        )

        updated_count = 0
        for post in posts:
            age_hours = max(1, (timezone.now() - post.created_at).total_seconds() / 3600)
            score = (post.likes_count + post.comments_count + post.reposts_count) / math.sqrt(age_hours)

            from .feed_cache import feed_cache
            feed_cache.set_post_popularity(post.id, score)
            updated_count += 1

        return {'success': True, 'posts_updated': updated_count}

    except Exception as e:
        logger.error(f"Error updating popularity: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_old_feed_cache():
    from .feed_cache import feed_cache
    import logging

    logger = logging.getLogger(__name__)

    try:
        from apps.social.infrastructure.models.social import Post
        from django.utils import timezone

        cutoff_date = timezone.now() - timedelta(days=7)
        old_posts = Post.objects.filter(
            status='published',
            created_at__lt=cutoff_date
        ).values_list('id', flat=True)[:1000]

        cleaned = 0
        for post_id in old_posts:
            feed_cache.invalidate_post(post_id)
            cleaned += 1

        logger.info(f"Cleaned {cleaned} old posts from feed cache")
        return {'success': True, 'posts_cleaned': cleaned}

    except Exception as e:
        logger.error(f"Error cleaning feed cache: {e}")
        return {'error': str(e)}


@shared_task
def index_post_for_search(post_id: int):
    import logging

    logger = logging.getLogger(__name__)

    try:
        from apps.social.infrastructure.models.social import Post
        from apps.social.presentation.serializers.social_serializers import PostSerializer

        post = Post.objects.get(id=post_id)

        data = {
            'id': post.id,
            'title': post.title or '',
            'content': post.text or '',
            'author_id': post.author_id,
            'author_username': post.author.username,
            'type': post.post_type,
            'created_at': post.created_at.isoformat(),
            'likes_count': post.likes_count,
            'comments_count': post.comments_count,
        }

        hashtags = post.hashtags.values_list('name', flat=True)
        data['hashtags'] = list(hashtags)


        logger.info(f"Indexed post {post_id} for search")
        return {'success': True}

    except Post.DoesNotExist:
        return {'error': 'Post not found'}
    except Exception as e:
        logger.error(f"Error indexing post: {e}")
        return {'error': str(e)}



@shared_task
def update_library_status_auto():
    from apps.users.infrastructure.models.users import UserLibrary
    from apps.anime.infrastructure.models.anime import Anime, UserEpisodeProgress
    import logging

    logger = logging.getLogger(__name__)

    try:
        now = timezone.now()
        one_month_ago = now - timedelta(days=30)
        
        updated_completed = 0
        updated_dropped = 0
        
        library_items = UserLibrary.objects.filter(
            status='started'
        ).select_related('anime')
        
        for item in library_items:
            anime = item.anime
            if not anime or not anime.episodes:
                continue
                
            watched_count = UserEpisodeProgress.objects.filter(
                user=item.user,
                anime=anime,
                status__in=['watched', 'skipped']
            ).count()
            
            if watched_count >= anime.episodes:
                item.status = 'completed'
                item.completed_at = now
                item.save(update_fields=['status', 'completed_at'])
                updated_completed += 1
                logger.info(f"User {item.user_id} anime {anime.id} marked as completed")
        
        stale_items = UserLibrary.objects.filter(
            status='started',
            updated_at__lt=one_month_ago
        )
        
        for item in stale_items:
            recent_progress = UserEpisodeProgress.objects.filter(
                user=item.user,
                anime=item.anime,
                last_watched__gte=one_month_ago
            ).exists()
            
            if not recent_progress:
                item.status = 'dropped'
                item.save(update_fields=['status'])
                updated_dropped += 1
                logger.info(f"User {item.user_id} anime {item.anime_id} marked as dropped (inactive)")
        
        logger.info(f"Library update completed: {updated_completed} completed, {updated_dropped} dropped")
        return {
            'success': True,
            'updated_completed': updated_completed,
            'updated_dropped': updated_dropped
        }

    except Exception as e:
        logger.error(f"Error updating library status: {e}")
        return {'error': str(e)}


@shared_task
def create_message_read_status(message_id: int, user_id: int):
    from apps.social.infrastructure.models.social import MessageReadStatus
    try:
        status, created = MessageReadStatus.objects.get_or_create(
            message_id=message_id,
            user_id=user_id
        )
        return {'success': True, 'created': created}
    except MessageReadStatus.MultipleObjectsReturned:
        return {'success': True, 'created': False}
    except Exception as e:
        return {'error': str(e)}


@shared_task
def convert_post_media_to_webp(post_media_id: int, field_name: str = 'file'):
    from apps.social.infrastructure.models.social import PostMedia

    try:
        post_media = PostMedia.objects.get(id=post_media_id)
        target = getattr(post_media, field_name, None)
        if not target:
            return {'status': 'skipped', 'message': 'No file'}

        if target.name.lower().endswith('.webp'):
            return {'status': 'skipped', 'message': 'Already WebP'}

        from apps.social.application.image_processor import convert_to_webp

        if field_name == 'thumbnail':
            webp_file = convert_to_webp(target, max_size=(400, 400), quality=80)
        else:
            webp_file = convert_to_webp(target, max_size=(1920, 1920), quality=85)

        if webp_file:
            setattr(post_media, field_name, webp_file)
            post_media.save(update_fields=[field_name])

        return {'status': 'completed', 'post_media_id': post_media_id}
    except PostMedia.DoesNotExist:
        return {'status': 'error', 'message': 'PostMedia not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
