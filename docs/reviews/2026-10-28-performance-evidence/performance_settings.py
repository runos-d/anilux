"""Disposable Docker audit only; no project database/media credentials."""
from config.settings_chat_test import *
from pathlib import Path

SECRET_KEY = 'disposable-performance-audit-only'
DEBUG = False
DATABASES['default'].update(HOST='audit-mysql', NAME='chat_test', USER='root', PASSWORD='', CONN_MAX_AGE=0)
REDIS_HOST = 'audit-redis'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = ''
CACHES = {'default': {
    'BACKEND': 'core.cache_backend.CircuitRedisCache',
    'LOCATION': 'redis://audit-redis:6379/1',
    'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient', 'SOCKET_CONNECT_TIMEOUT': 0.3, 'SOCKET_TIMEOUT': 0.5, 'RETRY_ON_TIMEOUT': False},
    'KEY_PREFIX': 'performance-audit',
}}
CHANNEL_LAYERS = {'default': {'BACKEND': 'core.channel_layer.BoundedRedisChannelLayer', 'CONFIG': {'hosts': ['redis://audit-redis:6379/0'], 'group_expiry': 300}}}
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1', 'audit-app']
DATA_DIR = Path('/tmp/animecore-performance')
DATA_EXPORT_ROOT = DATA_DIR / 'exports'
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
POST_MEDIA_AUTOSTART_WORKER = False
CELERY_TASK_ALWAYS_EAGER = False
