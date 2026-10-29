"""Isolated diagnostic settings. Never connects to the application database."""
from config.settings_chat_test import *
from pathlib import Path
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CELERY_TASK_ALWAYS_EAGER = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 1
REDIS_SOCKET_TIMEOUT = 0.05
MEDIA_ROOT = Path(MEDIA_ROOT)
from django.db.backends.signals import connection_created
def sqlite_collation(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_collation('utf8mb4_unicode_ci', lambda a,b: (a.casefold()>b.casefold())-(a.casefold()<b.casefold()))
connection_created.connect(sqlite_collation, weak=False)

# Every destructive lifecycle test must use an isolated export root as well.
import tempfile
DATA_EXPORT_ROOT = Path(tempfile.mkdtemp(prefix="review-exports-"))

DOWNLOAD_ROOT = Path(tempfile.mkdtemp(prefix="review-downloads-"))
