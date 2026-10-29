from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)


class SoftJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        from apps.users.application.token_sessions import validate_token_session
        user = super().get_user(validated_token)
        validate_token_session(validated_token, user)
        return user

    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed) as e:
            logger.debug(f"SoftJWTAuthentication: token invalid for {request.path}: {e}")
            return None
