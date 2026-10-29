"""Disposable production-mode lab. Never import settings from a real env file."""
import os

os.environ['ENV_FILE'] = '/dev/null'
if os.environ.get('DB_HOST') != 'lab-mysql' or os.environ.get('DB_NAME') != 'scalability_lab':
    raise RuntimeError('Scalability lab requires lab-mysql/scalability_lab')
if os.environ.get('REDIS_HOST') != 'lab-realtime':
    raise RuntimeError('Scalability lab requires its own realtime Redis')

from .settings import *  # noqa: F403, E402

DEBUG = False
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend', 'api', 'frontend']
STATICFILES_DIRS = []
NATIVE_AUTO_BUILD_ON_START = False
ROOT_URLCONF = 'config.urls_scalability_lab'
MEDIA_ROOT = '/lab-data/media'
CHAT_PRIVATE_MEDIA_ROOT = '/lab-data/private_chat_media'
POST_PRIVATE_MEDIA_ROOT = '/lab-data/private_post_media'
DOWNLOAD_ROOT = '/lab-data/private_downloads'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CORS_ALLOWED_ORIGINS = [*CORS_ALLOWED_ORIGINS, 'http://127.0.0.1:4480', 'http://localhost:4480']
CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, 'http://127.0.0.1:4480', 'http://localhost:4480']
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
# External adapters cannot be exercised accidentally with copied credentials.
BREVO_API_KEY = ''
WEB_PUSH_PRIVATE_KEY = ''
