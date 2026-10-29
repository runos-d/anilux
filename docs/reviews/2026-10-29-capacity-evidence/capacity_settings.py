from performance_settings import *
from config.settings import REST_FRAMEWORK as production_rest
from datetime import timedelta
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': production_rest['DEFAULT_THROTTLE_CLASSES']}
SIMPLE_JWT = {**SIMPLE_JWT, 'ACCESS_TOKEN_LIFETIME': timedelta(hours=12)}
CELERY_BROKER_URL = 'redis://audit-redis:6379/2'
CELERY_RESULT_BACKEND = 'redis://audit-redis:6379/3'
ASGI_WEBSOCKET_CONNECTIONS = 4096
ASGI_WEBSOCKET_HANDSHAKES = 64
ASGI_HTTP_CONCURRENCY = 32
NATIVE_AUTO_BUILD_ON_START = False
