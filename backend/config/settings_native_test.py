from .settings_chat_test import *  # noqa: F403

SECRET_KEY = 'native-packaging-isolated-tests'
SITE_URL = 'https://example.org'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': []}
ROOT_URLCONF = 'apps.native_apps.urls'
