from .settings_chat_test import *  # noqa: F403
from pathlib import Path

MEDIA_ROOT = Path(MEDIA_ROOT)

DATABASES['default']['NAME'] = 'excerpt_browser_v1'
DATABASES['default']['TEST']['NAME'] = 'test_excerpts_v1'
SECRET_KEY = 'disposable-excerpts-browser-v1'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
SITE_URL = 'http://localhost:5181'
CORS_ALLOWED_ORIGINS = [SITE_URL, 'http://127.0.0.1:5181']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
DEBUG = False
