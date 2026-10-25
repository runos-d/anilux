from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.social.infrastructure.models.social import Achievement, UserAchievement, Post, Follow, Repost
from apps.users.infrastructure.models.users import User


class AchievementService:
    def check_and_award(self, user):
        new_achievements = []

        achievements = Achievement.objects.all()

        for achievement in achievements:
            if UserAchievement.objects.filter(
                user=user,
                achievement=achievement,
                is_unlocked=True
            ).exists():
                continue

            progress = self._check_achievement_condition(user, achievement)

            if progress >= achievement.condition_value:
                user_achievement, created = UserAchievement.objects.get_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'progress': progress,
                        'is_unlocked': True,
                        'unlocked_at': timezone.now()
                    }
                )

                if created:
                    achievement.unlocked_count += 1
                    achievement.save(update_fields=['unlocked_count'])
                    new_achievements.append(user_achievement)
            else:
                UserAchievement.objects.update_or_create(
                    user=user,
                    achievement=achievement,
                    defaults={
                        'progress': progress,
                        'is_unlocked': False
                    }
                )

        return new_achievements

    def _check_achievement_condition(self, user, achievement):
        condition_type = achievement.condition_type

        if condition_type == 'posts_count':
            return Post.objects.filter(author=user, is_deleted=False).count()

        elif condition_type == 'followers_count':
            return Follow.objects.filter(following=user).count()

        elif condition_type == 'following_count':
            return Follow.objects.filter(follower=user).count()

        elif condition_type == 'likes_received':
            return Post.objects.filter(author=user).aggregate(
                total=Count('likes')
            )['total'] or 0

        elif condition_type == 'reposts_count':
            return Repost.objects.filter(user=user).count()

        elif condition_type == 'reposts_received':
            return Post.objects.filter(author=user).aggregate(
                total=Count('reposts')
            )['total'] or 0

        elif condition_type == 'comments_count':
            from apps.social.infrastructure.models.social import Comment
            return Comment.objects.filter(author=user, is_deleted=False).count()

        elif condition_type == 'registration_days':
            days = (timezone.now() - user.date_joined).days
            return days

        elif condition_type == 'profile_completed':
            score = 0
            if user.display_name:
                score += 25
            if user.avatar:
                score += 25
            if user.bio:
                score += 25
            if user.website:
                score += 25
            return score

        return 0


achievement_service = AchievementService()
