from .settings_chat_test import *  # noqa: F403

DATABASES['default']['HOST'] = 'anilux-seo-mysql'
DATABASES['default']['NAME'] = 'seo_acceptance'
DATABASES['default']['TEST']['NAME'] = 'test_seo_acceptance'
SECRET_KEY = 'isolated-seo-tests-key'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY}
ALLOWED_HOSTS = ['*']
SITE_URL = 'http://localhost:8096'
SEO_SITE_NAME = 'Тестовый каталог'
SEO_PUBLIC_ORIGIN = ''
SEO_INDEXING_ENABLED = False
SEO_FRONTEND_INDEX = '/app/frontend_dist/index.html'
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CELERY_TASK_ALWAYS_EAGER = False
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}
