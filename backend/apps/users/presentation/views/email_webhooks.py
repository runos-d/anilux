import hashlib
import hmac
from datetime import datetime, timezone as dt_timezone

from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.infrastructure.models.users import SuppressedEmail, TransactionalEmailEvent


SUPPORTED = {"delivered", "soft_bounce", "hard_bounce", "blocked", "invalid", "deferred", "spam", "error"}
SUPPRESSING = {"hard_bounce", "blocked", "invalid", "spam"}


class BrevoEventSerializer(serializers.Serializer):
    event = serializers.CharField(max_length=40)
    email = serializers.EmailField()
    message_id = serializers.CharField(max_length=255, required=False, allow_blank=True)
    messageId = serializers.CharField(max_length=255, required=False, allow_blank=True)
    date = serializers.CharField(required=False, allow_blank=True)
    ts = serializers.IntegerField(required=False)
    code = serializers.CharField(max_length=100, required=False, allow_blank=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class BrevoTransactionalEventsView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            content_length = int(request.META.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            content_length = 64 * 1024 + 1
        if content_length > 64 * 1024:
            return Response({"error": "payload_too_large"}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        expected = settings.BREVO_WEBHOOK_BEARER_TOKEN
        provided = request.headers.get("Authorization", "")
        if not expected or not hmac.compare_digest(provided, f"Bearer {expected}"):
            return Response({"error": "unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
        if settings.ENVIRONMENT == "production" and not request.is_secure():
            return Response({"error": "https_required"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = BrevoEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        event_type = data["event"].replace("softBounce", "soft_bounce").replace("hardBounce", "hard_bounce")
        recipient = data["email"].strip().lower()
        message_id = data.get("message_id") or data.get("messageId") or ""
        occurred_at = parse_datetime(data.get("date", ""))
        if not occurred_at and data.get("ts"):
            occurred_at = datetime.fromtimestamp(data["ts"], tz=dt_timezone.utc)
        occurred_at = occurred_at or timezone.now()
        fingerprint = "|".join((message_id, event_type, recipient, occurred_at.isoformat()))
        dedupe = hashlib.sha256(fingerprint.encode()).hexdigest()
        event, created = TransactionalEmailEvent.objects.get_or_create(
            deduplication_key=dedupe,
            defaults={
                "provider_message_id": message_id,
                "event_type": event_type,
                "recipient": recipient,
                "occurred_at": occurred_at,
                "diagnostic_code": data.get("code", ""),
                "diagnostic_reason": data.get("reason", ""),
                "supported": event_type in SUPPORTED,
            },
        )
        if created and event_type in SUPPRESSING:
            SuppressedEmail.objects.update_or_create(email=recipient, defaults={"reason": event_type})
        return Response({"accepted": True, "duplicate": not created, "supported": event.supported})
