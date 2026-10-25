from rest_framework.permissions import BasePermission


class IsPremiumUser(BasePermission):
    message = 'Для скачивания необходима подписка. Активировать подписку можно в настройках профиля.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        from apps.users.infrastructure.models.users import Subscription
        try:
            sub = request.user.subscription
            return sub.is_premium
        except Subscription.DoesNotExist:
            return False


def check_user_premium(user):
    if not user:
        return False
    if not hasattr(user, 'is_authenticated'):
        return False
    if not user.is_authenticated:
        return False
    try:
        sub = user.subscription
        if sub is None:
            return False
        return bool(getattr(sub, 'is_premium', False))
    except Exception:
        return False


def check_premium_or_403(user):
    return check_user_premium(user)
