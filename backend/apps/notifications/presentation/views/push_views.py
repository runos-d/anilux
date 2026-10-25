import base64
from hashlib import sha256
from urllib.parse import urlsplit
from django.conf import settings
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.notifications.infrastructure.models.notifications import PushSubscription


class PushConfig(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        enabled = bool(settings.WEB_PUSH_PUBLIC_KEY and settings.WEB_PUSH_PRIVATE_KEY and settings.WEB_PUSH_SUBJECT)
        return Response({'enabled': enabled, 'public_key': settings.WEB_PUSH_PUBLIC_KEY if enabled else ''})


def valid_endpoint(endpoint):
    try:
        url = urlsplit(endpoint)
        return (url.scheme == 'https' and not url.username and not url.password and
                url.port in (None, 443) and url.hostname and any(
                    url.hostname == host or host.startswith('.') and url.hostname.endswith(host)
                    for host in settings.WEB_PUSH_ALLOWED_HOSTS))
    except ValueError:
        return False


class SubscriptionWrite(serializers.Serializer):
    endpoint = serializers.CharField(max_length=4096)
    keys = serializers.DictField(child=serializers.CharField(max_length=200))

    def validate_endpoint(self, value):
        if not valid_endpoint(value):
            raise serializers.ValidationError('Неизвестный сервер push-уведомлений.')
        return value

    def validate_keys(self, value):
        for name, length in [('p256dh', 65), ('auth', 16)]:
            try:
                raw = base64.b64decode(value[name] + '=' * (-len(value[name]) % 4), altchars=b'-_', validate=True)
                if len(raw) != length or (name == 'p256dh' and raw[0] != 4):
                    raise ValueError()
            except (KeyError, ValueError):
                raise serializers.ValidationError('Некорректные ключи подписки.')
        return value


class DeviceSubscription(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubscriptionWrite(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        digest = sha256(data['endpoint'].encode()).hexdigest()
        existing = PushSubscription.objects.filter(endpoint_hash=digest).first()
        if existing and existing.user_id != request.user.pk and (
                existing.p256dh != data['keys']['p256dh'] or existing.auth != data['keys']['auth']):
            raise serializers.ValidationError('Подписка принадлежит другому устройству.')
        PushSubscription.objects.update_or_create(endpoint_hash=digest, defaults={
            'user': request.user, 'endpoint': data['endpoint'], 'p256dh': data['keys']['p256dh'],
            'auth': data['keys']['auth'], 'user_agent': request.META.get('HTTP_USER_AGENT', '')[:255],
            'is_active': True,
        })
        return Response({'enabled': True})

    def delete(self, request):
        endpoint = request.data.get('endpoint', '')
        if not isinstance(endpoint, str):
            raise serializers.ValidationError('Некорректная подписка.')
        PushSubscription.objects.filter(user=request.user, endpoint_hash=sha256(endpoint.encode()).hexdigest()).delete()
        return Response(status=204)
