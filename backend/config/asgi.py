import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.conf import settings
from core.asgi_limits import BoundedApplication
from core.telemetry import OperationalTelemetry

from config.ws_middleware import WebSocketCORSMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django_asgi_app = get_asgi_application()

django_asgi_app

import config.urls  # noqa: F401

from apps.social.application.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": WebSocketCORSMiddleware(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
application = BoundedApplication(application, settings.ASGI_HTTP_CONCURRENCY, settings.ASGI_WEBSOCKET_CONNECTIONS, settings.ASGI_WEBSOCKET_HANDSHAKES)
application = OperationalTelemetry(application, enabled=settings.OPERATIONAL_METRICS_ENABLED,
    token=settings.OPERATIONAL_METRICS_TOKEN, sample_rate=settings.OPERATIONAL_TRACE_SAMPLE_RATE)
