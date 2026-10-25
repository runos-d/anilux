from django.db.models import Sum, Q
import os
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from apps.social.infrastructure.models.social import PostCommentDislike, PostCommentLike, UploadedFile
from apps.social.infrastructure.models.social import Message, PrivateChat
import zipfile
from io import BytesIO
import json
import shutil


class StorageService:
    def __init__(self, user):
        self.user = user

    def get_storage_usage(self) -> dict:
        usage = {
            'messages': 0,
            'media': 0,
            'documents': 0,
            'audio': 0,
            'cache': 0,
            'total': 0
        }

        message_count = Message.objects.filter(
            Q(sender=self.user) |
            Q(chat__members__user=self.user) |
            Q(private_chat__user1=self.user) |
            Q(private_chat__user2=self.user)
        ).count()
        usage['messages'] = message_count * 500  

        media_files = UploadedFile.objects.filter(
            user=self.user,
            file_type__in=['image', 'video']
        ).aggregate(total=Sum('file_size'))
        usage['media'] = media_files['total'] or 0

        documents = UploadedFile.objects.filter(
            user=self.user,
            file_type='document'
        ).aggregate(total=Sum('file_size'))
        usage['documents'] = documents['total'] or 0

        audio = UploadedFile.objects.filter(
            user=self.user,
            file_type='audio'
        ).aggregate(total=Sum('file_size'))
        usage['audio'] = audio['total'] or 0

        usage['cache'] = self._estimate_cache_size()

        usage['total'] = sum(usage.values())

        usage['percentage'] = min(100, (usage['total'] / (2 * 1024 * 1024 * 1024)) * 100)

        return usage

    def _estimate_cache_size(self) -> int:
        cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', f'user_{self.user.id}')
        if os.path.exists(cache_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(cache_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except OSError:
                        pass  
            return total_size
        return 0

    def clear_cache(self) -> bool:
        cache_path = os.path.join(settings.MEDIA_ROOT, 'cache', f'user_{self.user.id}')
        if os.path.exists(cache_path):
            try:
                shutil.rmtree(cache_path)
                os.makedirs(cache_path)
            except OSError:
                return False

        return True

    def cleanup_old_media(self, days: int = 30) -> int:
        cutoff_date = timezone.now() - timedelta(days=days)

        old_media = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=cutoff_date,
            file_type__in=['image', 'video']
        )

        deleted_count = old_media.count()

        for media in old_media:
            self._delete_file(media.file)
            if media.thumbnail:
                self._delete_file(media.thumbnail)

        old_media.delete()

        return deleted_count

    def _delete_file(self, file_field):
        if file_field and file_field.path and os.path.exists(file_field.path):
            try:
                os.remove(file_field.path)
            except OSError:
                pass  

    def export_data(self, data_types: list = None) -> BytesIO:
        if data_types is None:
            data_types = ['messages', 'contacts', 'media', 'settings']

        export_data = {}

        if 'messages' in data_types:
            export_data['messages'] = self._export_messages()

        if 'contacts' in data_types:
            export_data['contacts'] = self._export_contacts()

        if 'media' in data_types:
            export_data['media'] = self._export_media_info()

        if 'settings' in data_types:
            export_data['settings'] = self._export_settings()

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for data_type, data in export_data.items():
                json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
                zip_file.writestr(f'{data_type}.json', json_data)

        buffer.seek(0)
        return buffer

    def _export_messages(self) -> list:
        messages = Message.objects.filter(
            Q(sender=self.user) |
            Q(chat__members__user=self.user) |
            Q(private_chat__user1=self.user) |
            Q(private_chat__user2=self.user)
        ).select_related('sender', 'chat', 'private_chat').order_by('created_at')

        export_messages = []
        for msg in messages:
            export_messages.append({
                'id': msg.id,
                'text': msg.text,
                'sender': msg.sender.username if msg.sender else None,
                'chat': msg.chat.name if msg.chat else None,
                'private_chat': True if msg.private_chat else False,
                'created_at': msg.created_at.isoformat(),
                'is_edited': msg.is_edited,
                'is_deleted': msg.is_deleted,
                'media_type': msg.media_type,
                'file_url': msg.file.url if msg.file else None,
            })

        return export_messages

    def _export_contacts(self) -> list:
        contacts = set()
        private_chats = PrivateChat.objects.filter(
            Q(user1=self.user) | Q(user2=self.user)
        )

        for chat in private_chats:
            contact = chat.user2 if chat.user1 == self.user else chat.user1
            contacts.add(contact)

        export_contacts = []
        for contact in contacts:
            export_contacts.append({
                'id': contact.id,
                'username': contact.username,
                'display_name': contact.display_name,
                'email': contact.email,
                'phone': contact.phone_number,
                'added_at': chat.created_at.isoformat() if 'chat' in locals() else None,
            })

        return export_contacts

    def _export_media_info(self) -> list:
        media_files = UploadedFile.objects.filter(user=self.user)

        export_media = []
        for media in media_files:
            export_media.append({
                'id': media.id,
                'filename': media.filename,
                'file_type': media.file_type,
                'file_size': media.file_size,
                'uploaded_at': media.uploaded_at.isoformat(),
                'url': media.file.url if media.file else None,
                'thumbnail_url': media.thumbnail.url if media.thumbnail else None,
            })

        return export_media

    def _export_settings(self) -> dict:
        settings_data = {}

        settings_data['profile'] = {
            'username': self.user.username,
            'display_name': self.user.display_name,
            'bio': self.user.bio,
            'avatar': self.user.avatar.url if self.user.avatar else None,
            'favorite_genres': self.user.favorite_genres,
        }

        if hasattr(self.user, 'profile_settings'):
            settings_data['profile_settings'] = {
                'theme': self.user.profile_settings.theme,
                'accent_color': self.user.profile_settings.accent_color,
                'language': self.user.profile_settings.language,
                'timezone': self.user.profile_settings.timezone,
                'date_format': self.user.profile_settings.date_format,
                'time_format': self.user.profile_settings.time_format,
            }

        if hasattr(self.user, 'notification_settings'):
            settings_data['notification_settings'] = {
                'push_enabled': self.user.notification_settings.push_enabled,
                'email_enabled': self.user.notification_settings.email_enabled,
                'email_frequency': self.user.notification_settings.email_frequency,
            }

        if hasattr(self.user, 'privacy_settings'):
            settings_data['privacy_settings'] = {
                'who_can_see_phone': self.user.privacy_settings.who_can_see_phone,
                'who_can_see_email': self.user.privacy_settings.who_can_see_email,
                'who_can_see_last_seen': self.user.privacy_settings.who_can_see_last_seen,
            }

        return settings_data

    def delete_account_data(self) -> dict:
        from apps.social.infrastructure.models.social import (
            Post, PostComment, Repost, PostLike, PostDislike,
            GroupMembership, ChatMember, ChatSettings,
            PrivateChatUserSettings, ChatFolder, MessageReadStatus,
            ChatTypingStatus, MessageReaction, Bookmark,
            UserMention, UserPostHidden, UserPostNotInterested,
            Favorite, UserAchievement, Follow, FeedView,
            UserNotificationSettings, ChatInviteLink,
            ChatWallpaper, ChatTheme, ScheduledMessage, MessageAttachment,
            Report, ContestEntry, ContestVote,
        )
        from apps.reactor.infrastructure.models.reactor import (
            ReactorPost, ReactorLike, ReactorComment,
        )
        from apps.playlists.infrastructure.models.playlists import (
            Playlist, FavoritePlaylist, FavoriteAnime,
        )
        from apps.anime.infrastructure.models.anime import (
            WatchProgress, UserEpisodeProgress, AnimeEpisodeNotification,
            UserActiveTab, UserDubRating, ClipTask,
        )
        from apps.notifications.infrastructure.models.notifications import (
            Notification, Reminder,
        )

        from apps.studios.infrastructure.models.studios import (
            StudioSubscription, StudioRating,
        )
        from apps.dubs.infrastructure.models.dubs import (
            DubGroupSubscription, DubGroupRating, UserDubPreference, DubReview,
        )
        from apps.users.infrastructure.models.users import (
            UserSession, UserSettings, UserProfileSettings,
            TwoFactorAuth, NotificationSettings, PrivacySettings,
            UserTheme, FontSettings, SyncSettings, DataExport,
            ChatBackground, SecurityLog, EmailLog,
            UserAnalytics, UserFavorite, FavoriteTheme, FavoriteEpisode,
            UserLibrary, SupportTicket, SupportMessage,
            Subscription, PromoCodeUsage,
        )

        stats = {
            'posts_deleted': 0,
            'comments_deleted': 0,
            'reposts_deleted': 0,
            'reactions_deleted': 0,
            'media_deleted': 0,
            'files_deleted': 0,
            'progress_deleted': 0,
            'favorites_deleted': 0,
            'library_deleted': 0,
            'chats_removed': 0,
            'notifications_deleted': 0,
        }

        user = self.user

        if user.avatar:
            self._delete_file(user.avatar)
            user.avatar = None
        if user.cover_image:
            self._delete_file(user.cover_image)
            user.cover_image = None

        user_files = UploadedFile.objects.filter(user=user)
        for file_obj in user_files:
            self._delete_file(file_obj.file)
            if file_obj.thumbnail:
                self._delete_file(file_obj.thumbnail)
        stats['files_deleted'] = user_files.count()
        user_files.delete()

        user_posts = Post.objects.filter(author=user)
        stats['posts_deleted'] = user_posts.count()
        user_posts.delete()

        user_comments = PostComment.objects.filter(author=user)
        stats['comments_deleted'] = user_comments.count()
        user_comments.delete()

        user_reposts = Repost.objects.filter(user=user)
        stats['reposts_deleted'] = user_reposts.count()
        user_reposts.delete()

        PostLike.objects.filter(user=user).delete()
        PostDislike.objects.filter(user=user).delete()
        PostCommentLike.objects.filter(user=user).delete()
        PostCommentDislike.objects.filter(user=user).delete()
        stats['reactions_deleted'] = (
            user.post_likes.count() + user.post_dislikes.count()
            + user.post_comment_likes.count() + user.post_comment_dislikes.count()
        )

        ReactorPost.objects.filter(user=user).delete()
        ReactorLike.objects.filter(user=user).delete()
        ReactorComment.objects.filter(user=user).delete()

        watch_progress = WatchProgress.objects.filter(user=user)
        stats['progress_deleted'] = watch_progress.count()
        watch_progress.delete()

        episode_progress = UserEpisodeProgress.objects.filter(user=user)
        stats['progress_deleted'] += episode_progress.count()
        episode_progress.delete()

        AnimeEpisodeNotification.objects.filter(user=user).delete()
        UserActiveTab.objects.filter(user=user).delete()
        ClipTask.objects.filter(user=user).delete()
        UserDubRating.objects.filter(user=user).delete()

        FavoriteAnime.objects.filter(user=user).delete()
        FavoritePlaylist.objects.filter(user=user).delete()
        FavoriteTheme.objects.filter(user=user).delete()
        FavoriteEpisode.objects.filter(user=user).delete()
        stats['favorites_deleted'] = (
            user.favorites.count() + user.favorite_anime.count()
            + user.favorite_themes.count() + user.favorite_episodes.count()
        )

        UserLibrary.objects.filter(user=user).delete()
        stats['library_deleted'] = user.library.count()

        Notification.objects.filter(user=user).delete()
        Reminder.objects.filter(user=user).delete()
        stats['notifications_deleted'] = (
            user.notifications.count() + user.reminders.count()
        )

        UserSession.objects.filter(user=user).delete()
        UserSettings.objects.filter(user=user).delete()
        UserProfileSettings.objects.filter(user=user).delete()
        TwoFactorAuth.objects.filter(user=user).delete()
        NotificationSettings.objects.filter(user=user).delete()
        PrivacySettings.objects.filter(user=user).delete()
        UserTheme.objects.filter(user=user).delete()
        FontSettings.objects.filter(user=user).delete()
        SyncSettings.objects.filter(user=user).delete()
        DataExport.objects.filter(user=user).delete()
        ChatBackground.objects.filter(user=user).delete()
        SecurityLog.objects.filter(user=user).delete()
        EmailLog.objects.filter(user=user).delete()
        UserAnalytics.objects.filter(user=user).delete()
        Subscription.objects.filter(user=user).delete()
        PromoCodeUsage.objects.filter(user=user).delete()

        ChatFolder.objects.filter(user=user).delete()
        ChatSettings.objects.filter(user=user).delete()
        PrivateChatUserSettings.objects.filter(user=user).delete()
        ChatWallpaper.objects.filter(user=user).delete()
        ChatTheme.objects.filter(user=user).delete()
        ScheduledMessage.objects.filter(sender=user).delete()

        ChatMember.objects.filter(user=user).delete()
        GroupMembership.objects.filter(user=user).delete()

        private_chats = PrivateChat.objects.filter(
            Q(user1=user) | Q(user2=user)
        )
        stats['chats_removed'] = private_chats.count()
        private_chats.delete()

        Follow.objects.filter(Q(follower=user) | Q(following=user)).delete()
        UserAchievement.objects.filter(user=user).delete()
        Bookmark.objects.filter(user=user).delete()
        UserMention.objects.filter(user=user).delete()
        UserPostHidden.objects.filter(user=user).delete()
        UserPostNotInterested.objects.filter(user=user).delete()
        UserNotificationSettings.objects.filter(user=user).delete()
        ChatInviteLink.objects.filter(Q(creator=user) | Q(target_user=user)).delete()
        MessageReaction.objects.filter(user=user).delete()
        MessageReadStatus.objects.filter(user=user).delete()
        ChatTypingStatus.objects.filter(user=user).delete()
        Report.objects.filter(Q(reporter=user) | Q(resolved_by=user)).delete()
        ContestEntry.objects.filter(participant=user).delete()
        ContestVote.objects.filter(voter=user).delete()
        MessageAttachment.objects.filter(user=user).delete()

        StudioSubscription.objects.filter(user=user).delete()
        StudioRating.objects.filter(user=user).delete()
        DubGroupSubscription.objects.filter(user=user).delete()
        DubGroupRating.objects.filter(user=user).delete()
        UserDubPreference.objects.filter(user=user).delete()
        DubReview.objects.filter(user=user).delete()

        media_files = UploadedFile.objects.filter(user=user, file_type__in=['image', 'video'])
        for media in media_files:
            self._delete_file(media.file)
            if media.thumbnail:
                self._delete_file(media.thumbnail)
        stats['media_deleted'] = media_files.count()
        media_files.delete()

        self.clear_cache()

        return stats

    def get_cleanup_recommendations(self) -> dict:
        recommendations = {}

        old_media_count = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=timezone.now() - timedelta(days=30),
            file_type__in=['image', 'video']
        ).count()

        if old_media_count > 0:
            recommendations['old_media'] = {
                'count': old_media_count,
                'size': self._calculate_old_media_size(),
                'action': 'Удалить медиафайлы старше 30 дней'
            }

        cache_size = self._estimate_cache_size()
        if cache_size > 50 * 1024 * 1024:  
            recommendations['cache'] = {
                'size': cache_size,
                'action': 'Очистить кэш приложения'
            }

        return recommendations

    def _calculate_old_media_size(self) -> int:
        old_media = UploadedFile.objects.filter(
            user=self.user,
            uploaded_at__lt=timezone.now() - timedelta(days=30),
            file_type__in=['image', 'video']
        ).aggregate(total=Sum('file_size'))

        return old_media['total'] or 0