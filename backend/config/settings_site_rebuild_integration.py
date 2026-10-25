from .settings_chat_integration import *  # noqa: F403

DATABASES['default']['TEST']['NAME'] = 'test_site_rebuild'
if os.environ.get('CHAT_TEST_USE_TEST_DB') == '1':
    DATABASES['default']['NAME'] = 'test_site_rebuild'
MEDIA_ROOT = '/tmp/site-rebuild-media'
CHAT_PRIVATE_MEDIA_ROOT = '/tmp/site-rebuild-chats'
POST_PRIVATE_MEDIA_ROOT = '/tmp/site-rebuild-posts'
