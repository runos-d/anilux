from .settings import *  # noqa: F403
import os
import tempfile

DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'chat_test',
    'USER': 'root', 'PASSWORD': '',
    'HOST': os.environ.get('CHAT_TEST_DB_HOST', 'anilux-chat-tests'),
    'PORT': '3306',
    'OPTIONS': {'charset': 'utf8mb4'},
    'TEST': {'NAME': 'test_chat_test'},
}}
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
MEDIA_ROOT = tempfile.mkdtemp(prefix='chat-tests-')
REDIS_DB = 14
REDIS_HOST = os.environ.get('CHAT_TEST_REDIS_HOST', 'anilux-chat-redis-tests')
STATICFILES_DIRS = []

CHAT_PRIVATE_MEDIA_ROOT = tempfile.mkdtemp(prefix="chat-private-tests-")
POST_PRIVATE_MEDIA_ROOT = tempfile.mkdtemp(prefix='post-private-tests-')
