from .settings_chat_test import *  # noqa: F403
from pathlib import Path

DATABASES['default']['NAME'] = 'playlist_browser_v1'
DATABASES['default']['TEST']['NAME'] = 'test_playlist_discovery_v1'
SECRET_KEY = 'disposable-playlist-acceptance-key'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
SITE_URL = 'http://localhost:5196'
CORS_ALLOWED_ORIGINS = [SITE_URL, 'http://127.0.0.1:5196']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
CELERY_TASK_ALWAYS_EAGER = True
MEDIA_ROOT = Path('/tmp/playlists-browser/media')
CHAT_PRIVATE_MEDIA_ROOT = Path('/tmp/playlists-browser/chats')
POST_PRIVATE_MEDIA_ROOT = Path('/tmp/playlists-browser/posts')
DATA_DIR = Path('/tmp/playlists-browser')
