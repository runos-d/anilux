from .settings_calendar_browser import *  # noqa: F403
from pathlib import Path

DATABASES['default']['NAME'] = 'episode_browser_v1'
MEDIA_ROOT = Path(MEDIA_ROOT)
CHANNEL_LAYERS = {'default': {'BACKEND': 'channels_redis.core.RedisChannelLayer', 'CONFIG': {
    'hosts': [('anilux-chat-redis-tests', 6379)], 'prefix': 'episode-browser-v1',
}}}
