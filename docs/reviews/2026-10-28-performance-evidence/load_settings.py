from performance_settings import *
from config.settings import REST_FRAMEWORK as production_rest
from datetime import timedelta

REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': production_rest['DEFAULT_THROTTLE_CLASSES']}
SIMPLE_JWT = {**SIMPLE_JWT, 'ACCESS_TOKEN_LIFETIME': timedelta(hours=12)}
DOWNLOAD_ROOT = Path('/audit-downloads')
CELERY_BROKER_URL = 'redis://audit-redis:6379/2'
CELERY_RESULT_BACKEND = 'redis://audit-redis:6379/3'
CHANNEL_LAYERS = {'default': {'BACKEND': 'core.channel_layer.BoundedRedisChannelLayer', 'CONFIG': {'hosts': [{
    'address': 'redis://audit-redis:6379/0', 'socket_connect_timeout': 1, 'socket_timeout': 1,
}]}}}
