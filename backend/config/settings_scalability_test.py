from .settings_scalability_lab import *  # noqa: F403

DATABASES['default']['TEST'] = {'NAME': 'test_scalability_lab'}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
ROOT_URLCONF = 'config.urls'
OPERATIONAL_METRICS_ENABLED = False
