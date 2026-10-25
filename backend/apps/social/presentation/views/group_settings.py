from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.social.infrastructure.models.social import GroupChat
from apps.social.infrastructure.models.social_chat import ChatSlowMode
from apps.social.application import conversations as service


class GroupSettingsInput(serializers.Serializer):
    slow_mode_enabled = serializers.BooleanField(required=False)
    slow_mode_delay = serializers.IntegerField(min_value=0, max_value=3600, required=False)
    has_hidden_members = serializers.BooleanField(required=False)
    restrict_saving_content = serializers.BooleanField(required=False)
    can_send_media = serializers.BooleanField(required=False)
    can_send_stickers = serializers.BooleanField(required=False)
    can_send_polls = serializers.BooleanField(required=False)
    can_invite_users = serializers.BooleanField(required=False)
    can_pin_messages = serializers.BooleanField(required=False)
    history_visible = serializers.BooleanField(required=False)

    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({key: 'Неизвестная настройка' for key in unknown})
        return super().to_internal_value(data)


def settings_data(chat):
    mode = ChatSlowMode.objects.filter(chat=chat).first()
    return dict({key: getattr(chat, key) for key in GroupSettingsInput().fields if key not in ('slow_mode_enabled', 'slow_mode_delay')},
                slow_mode_enabled=mode.enabled if mode else chat.slow_mode_delay > 0,
                slow_mode_delay=mode.delay if mode else chat.slow_mode_delay)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
@transaction.atomic
def group_settings(request, chat_id):
    chat = service.resolve_chat(chat_id, request.user, 'group')
    if request.method != 'GET':
        chat = GroupChat.objects.select_for_update().get(pk=chat.pk)
        service.require_permission(chat, request.user, 'can_manage_chat')
        serializer = GroupSettingsInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        if 'slow_mode_enabled' in data or 'slow_mode_delay' in data:
            mode, _ = ChatSlowMode.objects.get_or_create(chat=chat, defaults={'enabled': chat.slow_mode_delay > 0, 'delay': chat.slow_mode_delay or 30})
            mode.enabled = data.pop('slow_mode_enabled', mode.enabled)
            mode.delay = data.pop('slow_mode_delay', mode.delay)
            mode.save()
            data['slow_mode_delay'] = mode.delay if mode.enabled else 0
        for key, value in data.items():
            setattr(chat, key, value)
        if data:
            chat.save(update_fields=list(data))
    return Response(settings_data(chat))
