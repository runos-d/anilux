from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenRefreshView


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh = self.token_class(attrs["refresh"])
            user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
            lookup = {api_settings.USER_ID_FIELD: user_id}
            if user_id is None or not get_user_model().objects.filter(is_active=True, **lookup).exists():
                raise InvalidToken("Token user no longer exists")
            return super().validate(attrs)
        except get_user_model().DoesNotExist as exc:
            raise InvalidToken("Token user no longer exists") from exc


class SafeTokenRefreshView(TokenRefreshView):
    serializer_class = SafeTokenRefreshSerializer
