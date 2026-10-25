from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)


class SoftJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError, AuthenticationFailed) as e:
            logger.debug(f"SoftJWTAuthentication: token invalid for {request.path}: {e}")
            return None
