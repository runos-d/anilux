from django.utils import timezone
from django.db.models import Count, Q
from typing import Optional, List
from datetime import timedelta
from django.db.models import Prefetch, Count
from apps.social.infrastructure.models.social import Bookmark, Post, PostLike, PostMedia, PostAttachment, UserPostHidden
from apps.social.infrastructure.models.social import Post, Group, Follow
from apps.users.infrastructure.models.users import User


class SystemPostService:
    SYSTEM_TYPES = {
        'level_up': 'достиг нового уровня',
        'contest_win': 'победил в конкурсе',
        'contest_participation': 'участвует в конкурсе',
        'group_created': 'создал новую группу',
        'contest_started': 'начался новый конкурс',
        'achievement_unlocked': 'получил достижение',
        'milestone_reached': 'достиг важной отметки',
    }
    
    @classmethod
    def create_level_up_post(cls, user: User, new_level: int) -> Post:
        return cls._create_system_post(
            user=user,
            system_type='level_up',
            title=f'🎉 Новый уровень!',
            text=f'{user.username} достиг {new_level} уровня! Поздравляем!',
        )
    
    @classmethod
    def create_contest_win_post(cls, user: User, contest_title: str, place: int) -> Post:
        place_emoji = {1: '🥇', 2: '🥈', 3: '🥉'}
        emoji = place_emoji.get(place, '🏆')
        
        return cls._create_system_post(
            user=user,
            system_type='contest_win',
            title=f'{emoji} Победа в конкурсе!',
            text=f'{user.username} занял(а) {place} место в конкурсе "{contest_title}"! Поздравляем!',
        )
    
    @classmethod
    def create_contest_participation_post(cls, user: User, contest_title: str) -> Post:
        return cls._create_system_post(
            user=user,
            system_type='contest_participation',
            title=f'🎯 Участие в конкурсе',
            text=f'{user.username} участвует в конкурсе "{contest_title}"!',
        )
    
    @classmethod
    def create_group_created_post(cls, user: User, group: Group) -> Post:
        return cls._create_system_post(
            user=user,
            system_type='group_created',
            title=f'👥 Новая группа',
            text=f'{user.username} создал(а) новую группу "{group.name}"!',
        )
    
    @classmethod
    def create_contest_started_post(cls, contest_title: str, organizer: User) -> Post:
        return cls._create_system_post(
            user=organizer,
            system_type='contest_started',
            title=f'🏆 Новый конкурс!',
            text=f'Начался новый конкурс "{contest_title}"! Участвуйте!',
        )
    
    @classmethod
    def create_achievement_post(cls, user: User, achievement_name: str, achievement_level: str) -> Post:
        level_emoji = {
            'bronze': '🥉',
            'silver': '🥈', 
            'gold': '🥇',
            'legendary': '⭐',
        }
        emoji = level_emoji.get(achievement_level, '🏅')
        
        return cls._create_system_post(
            user=user,
            system_type='achievement_unlocked',
            title=f'{emoji} Достижение получено!',
            text=f'{user.username} разблокировал(а) достижение "{achievement_name}"!',
        )
    
    @classmethod
    def create_milestone_post(cls, user: User, milestone_type: str, value: int) -> Post:
        milestone_texts = {
            'followers': f'{user.username} достиг {value} подписчиков!',
            'posts': f'{user.username} опубликовал(а) {value} постов!',
            'likes': f'{user.username} получил(а) {value} лайков!',
        }
        
        text = milestone_texts.get(milestone_type, f'{user.username} достиг новой отметки: {value}!')
        
        return cls._create_system_post(
            user=user,
            system_type='milestone_reached',
            title=f'🎯 Важная отметка!',
            text=text,
        )
    
    @classmethod
    def _create_system_post(cls, user: User, system_type: str, title: str, text: str) -> Post:
        post = Post.objects.create(
            author=user,
            post_type='system',
            system_type=system_type,
            title=title,
            text=text,
            status='published',
            visibility='public',
            allow_comments=False,
            published_at=timezone.now(),
        )
        return post


class FeedGenerationService:
    WEIGHTS = {
        'subscriptions': 0.70,
        'groups': 0.15,
        'recommended': 0.10,
        'promoted': 0.05,
    }
    
    @classmethod
    def get_feed_queryset(cls, user: User, limit: int = 20, cursor: str = None, offset: int = 0):
        from apps.social.infrastructure.models.social import GroupMembership, UserPostHidden

        subscriptions = Follow.objects.filter(
            follower=user
        ).values_list('following_id', flat=True)

        hidden_post_ids = list(UserPostHidden.objects.filter(
            user=user
        ).values_list('post_id', flat=True))

        base_prefetch = [
            Prefetch('media_files', queryset=PostMedia.objects.all().order_by('order')),
            Prefetch('attachments', queryset=PostAttachment.objects.all()),
            Prefetch('hashtag_links__hashtag'),
            Prefetch('likes', queryset=PostLike.objects.filter(user=user), to_attr='user_likes'),
            Prefetch('bookmarks', queryset=Bookmark.objects.filter(user=user), to_attr='user_bookmarks'),
        ]

        base_filter = Q(status='published') & ~Q(is_deleted=True) & ~Q(post_type='system')
        exclude_filter = Q(id__in=hidden_post_ids)
        from apps.social.application.post_access import readable_posts

        posts = (readable_posts(Post.objects.all(), user)
            .filter(base_filter)
            .exclude(exclude_filter)
            .select_related('author', 'anime', 'playlist', 'group')
            .prefetch_related(*base_prefetch)
            .annotate(playlist_items_count=Count('playlist__items'))
            .order_by('-created_at', '-id')
        )
        if cursor:
            try:
                ts, pk = cursor.split(',', 1)
                posts = posts.filter(Q(created_at__lt=ts) | Q(created_at=ts, id__lt=pk))
            except Exception:
                pass
        return posts[:limit]
    
    @classmethod
    def _mix_posts(cls, own_posts: List[Post], subscription_posts: List[Post],
                   group_posts: List[Post], recommended_posts: List[Post], limit: int) -> List[Post]:
        import random

        random.shuffle(subscription_posts)
        random.shuffle(group_posts)
        random.shuffle(recommended_posts)

        sub_count = int(limit * cls.WEIGHTS['subscriptions'])
        group_count = int(limit * cls.WEIGHTS['groups'])
        rec_count = limit - sub_count - group_count

        result = []
        result.extend(own_posts)              
        result.extend(subscription_posts[:sub_count])
        result.extend(group_posts[:group_count])
        result.extend(recommended_posts[:rec_count])

        seen_ids = set()
        unique_result = []
        for post in result:
            if post.id not in seen_ids:
                seen_ids.add(post.id)
                unique_result.append(post)

        unique_result.sort(key=lambda x: x.created_at, reverse=True)

        return unique_result
    
    @classmethod
    def get_user_feed_posts(cls, user: User, page: int = 1, per_page: int = 20):
        from django.db.models import Count
        
        offset = (page - 1) * per_page
        posts = cls.get_feed_queryset(user, limit=per_page, offset=offset)
        
        pinned_posts = Post.objects.filter(
            author=user,
            is_pinned=True,
            status='published',
            is_deleted=False,
        ).exclude(
            post_type='system'
        ).annotate(
            playlist_items_count=Count('playlist__items')
        ).select_related('author', 'anime', 'playlist')
        
        return {
            'pinned': pinned_posts,
            'posts': posts,
        }
    
    @classmethod
    def get_group_feed(cls, group: Group, page: int = 1, per_page: int = 20):
        from django.db.models import Count
        
        offset = (page - 1) * per_page
        
        posts = Post.objects.filter(
            group=group,
            status='published',
            is_deleted=False,
        ).exclude(
            post_type='system'
        ).annotate(
            playlist_items_count=Count('playlist__items')
        ).select_related(
            'author', 'anime', 'playlist'
        ).order_by('-is_pinned', '-created_at')[offset:offset + per_page]
        
        return posts
    
    @classmethod
    def get_profile_posts(cls, user: User, page: int = 1, per_page: int = 20):
        from django.db.models import Count
        
        offset = (page - 1) * per_page
        
        posts = Post.objects.filter(
            author=user,
            status='published',
            is_deleted=False,
        ).exclude(
            post_type='system'
        ).annotate(
            playlist_items_count=Count('playlist__items')
        ).select_related(
            'author', 'anime', 'playlist', 'group'
        ).order_by('-is_pinned', '-created_at')[offset:offset + per_page]
        
        return posts


class TrendingService:
    @classmethod
    def get_hot_posts(cls, hours: int = 24, limit: int = 20) -> List[Post]:
        from django.db.models import F, Count
        
        time_threshold = timezone.now() - timedelta(hours=hours)
        
        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=time_threshold,
            post_type__in=['text', 'image', 'video', 'anime', 'playlist']
        ).annotate(
            playlist_items_count=Count('playlist__items')
        ).select_related(
            'author', 'anime', 'group', 'playlist', 'reactor_post'
        ).prefetch_related(
            'media_files', 'hashtag_links__hashtag'
        ).order_by(
            '-likes_count', '-comments_count', '-created_at'
        )[:limit]
        
        return list(posts)

    @classmethod
    def get_top_posts(cls, days: int = 7, limit: int = 20) -> List[Post]:
        from django.db.models import Count
        
        time_threshold = timezone.now() - timedelta(days=days)
        
        posts = Post.objects.filter(
            status='published',
            is_deleted=False,
            created_at__gte=time_threshold,
            post_type__in=['text', 'image', 'video', 'anime', 'playlist']
        ).annotate(
            playlist_items_count=Count('playlist__items')
        ).order_by('-likes_count', '-comments_count', '-created_at')[:limit]
        
        return list(posts)
