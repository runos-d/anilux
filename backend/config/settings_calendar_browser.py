from .settings_calendar_test import *  # noqa: F403

DATABASES['default']['NAME'] = 'calendar_browser_v1'
SECRET_KEY = 'disposable-calendar-browser-test-key'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
SITE_URL = 'http://localhost:5179'
CORS_ALLOWED_ORIGINS = [SITE_URL, 'http://127.0.0.1:5179']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
DEBUG = False
