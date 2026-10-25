from rest_framework import permissions
from apps.social.infrastructure.models.social import ChatMember

class IsChatOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'chat'):
            return obj.chat.created_by == request.user
        return False


class HasChatPermission(permissions.BasePermission):
    def __init__(self, permission):
        self.permission = permission

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, 'members'):
            try:
                member = obj.members.get(user=request.user)
                return member.effective_permissions.get(self.permission, False)
            except ChatMember.DoesNotExist:
                return False

        elif hasattr(obj, 'chat'):
            try:
                member = obj.chat.members.get(user=request.user)
                return member.effective_permissions.get(self.permission, False)
            except ChatMember.DoesNotExist:
                return False

        return False


class IsChatMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if hasattr(obj, 'members'):
            return obj.members.filter(user=request.user).exists()

        elif hasattr(obj, 'chat'):
            return obj.chat.members.filter(user=request.user).exists()

        return False