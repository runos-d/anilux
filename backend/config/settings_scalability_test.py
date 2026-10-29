from .settings_scalability_lab import *  # noqa: F403
import tempfile
from pathlib import Path

DATABASES['default']['TEST'] = {'NAME': 'test_scalability_lab'}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
ROOT_URLCONF = 'config.urls'
OPERATIONAL_METRICS_ENABLED = False
DATA_DIR = Path(tempfile.mkdtemp(prefix='scalability-tests-'))
MEDIA_ROOT = str(DATA_DIR / 'media')
CHAT_PRIVATE_MEDIA_ROOT = str(DATA_DIR / 'private_chat_media')
POST_PRIVATE_MEDIA_ROOT = str(DATA_DIR / 'private_post_media')
DOWNLOAD_ROOT = str(DATA_DIR / 'downloads')
