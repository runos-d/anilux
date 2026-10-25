from .settings_chat_test import *  # noqa: F403
import os

CHAT_INTEGRATION_TESTS = True
if os.environ.get('CHAT_TEST_USE_TEST_DB') == '1':
    DATABASES['default']['NAME'] = DATABASES['default']['TEST']['NAME']
MEDIA_ROOT = '/tmp/chat-integration-media'
CHAT_PRIVATE_MEDIA_ROOT = '/tmp/chat-integration-private-media'
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels_redis.core.RedisChannelLayer', 'CONFIG': {
    'hosts': [(REDIS_HOST, 6379)], 'prefix': 'anilux-chat-integration', 'expiry': 60,
}}}
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:6379/13'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:6379/12'
CELERY_TASK_ALWAYS_EAGER = False
