from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken


class SessionTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        from apps.users.application.token_sessions import bind_refresh
        refresh = bind_refresh(RefreshToken(data['refresh']), self.user, self.context['request'])
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class SessionTokenObtainPairView(TokenObtainPairView):
    serializer_class = SessionTokenObtainPairSerializer


class SafeTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        try:
            refresh = self.token_class(attrs["refresh"])
            user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
            lookup = {api_settings.USER_ID_FIELD: user_id}
            if user_id is None or not get_user_model().objects.filter(is_active=True, **lookup).exists():
                raise InvalidToken("Token user no longer exists")
            user = get_user_model().objects.get(**lookup)
            from apps.users.application.token_sessions import validate_token_session
            validate_token_session(refresh, user)
            return super().validate(attrs)
        except (get_user_model().DoesNotExist, AuthenticationFailed) as exc:
            raise InvalidToken("Token user no longer exists") from exc


class SafeTokenRefreshView(TokenRefreshView):
    serializer_class = SafeTokenRefreshSerializer
