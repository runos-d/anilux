from django.core.cache import cache
from redis.exceptions import ConnectionError as RedisConnectionError
import logging

logger = logging.getLogger(__name__)


def safe_cache_get(key: str, default=None):
    try:
        return cache.get(key, default)
    except RedisConnectionError:
        return default
    except Exception as e:
        return default


def safe_cache_set(key: str, value, timeout: int = 3600) -> bool:
    try:
        cache.set(key, value, timeout)
        return True
    except RedisConnectionError:
        return False
    except Exception:
        return False