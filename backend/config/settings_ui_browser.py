from .settings_episode_browser import *  # noqa: F403
from datetime import timedelta

DATABASES['default']['NAME'] = 'ui_browser_20261012'
SECRET_KEY = 'isolated-interface-browser-key-20261012'
SIMPLE_JWT = {**SIMPLE_JWT, 'SIGNING_KEY': SECRET_KEY, 'ACCESS_TOKEN_LIFETIME': timedelta(hours=6)}
SITE_URL = 'http://localhost:5186'
CORS_ALLOWED_ORIGINS = [SITE_URL, 'http://127.0.0.1:5186', 'http://localhost:5187']
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS
MEDIA_ROOT = Path('/tmp/ui-browser/media')
CHAT_PRIVATE_MEDIA_ROOT = Path('/tmp/ui-browser/chats')
POST_PRIVATE_MEDIA_ROOT = Path('/tmp/ui-browser/posts')
CHANNEL_LAYERS['default']['CONFIG']['prefix'] = 'ui-browser-20261012'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

import json
_ui_push_file = BASE_DIR / "data/local_release/ui-review/push-keys.json"
if _ui_push_file.exists():
    globals().update(json.loads(_ui_push_file.read_text()))
