import re
from urllib.parse import urlparse

from channels.middleware import BaseMiddleware
from django.conf import settings


def _origin_allowed(origin: str) -> bool:
    if not origin:
        return True
    if getattr(settings, "CORS_ALLOW_ALL_ORIGINS", False):
        return True
    allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
    if origin in allowed:
        return True
    regexes = getattr(settings, "CORS_ALLOWED_ORIGIN_REGEXES", [])
    for pattern in regexes:
        if re.fullmatch(pattern, origin):
            return True
    return False


class WebSocketCORSMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            headers = dict(scope.get("headers", []))
            origin = headers.get(b"origin", b"").decode("utf-8", errors="ignore")
            if not _origin_allowed(origin):
                await send({"type": "websocket.close", "code": 4403})
                return
        await super().__call__(scope, receive, send)