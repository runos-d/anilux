from .settings_chat_integration import *  # noqa: F403
from pathlib import Path

DATABASES['default']['NAME'] = 'chat_e2e_20261010'
DATABASES['default']['TEST']['NAME'] = 'test_chat_e2e_20261010'
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
CORS_ALLOW_ALL_ORIGINS = True
MEDIA_ROOT = Path('/app/data/chat_e2e/media')
CHAT_PRIVATE_MEDIA_ROOT = Path('/app/data/chat_e2e/private')
CHANNEL_LAYERS['default']['CONFIG']['prefix'] = 'anilux-chat-e2e'
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:6379/11'
CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:6379/10'
