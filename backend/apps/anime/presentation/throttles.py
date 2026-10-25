from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from redis.exceptions import ConnectionError as RedisConnectionError


class SafeCacheWrapper:
    def __init__(self, cache_backend):
        self._cache = cache_backend

    def get(self, key, default=None):
        try:
            return self._cache.get(key, default)
        except RedisConnectionError:
            return default
        except Exception:
            return default

    def set(self, key, value, timeout=None):
        try:
            self._cache.set(key, value, timeout)
            return True
        except RedisConnectionError:
            return False
        except Exception:
            return False

    def delete(self, key):
        try:
            self._cache.delete(key)
        except RedisConnectionError:
            pass
        except Exception:
            pass


class StaffExemptRateThrottle(UserRateThrottle):
    @property
    def cache(self):
        return SafeCacheWrapper(super().cache)

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return True
        return super().allow_request(request, view)


class StaffExemptAnonRateThrottle(AnonRateThrottle):
    @property
    def cache(self):
        return SafeCacheWrapper(super().cache)

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return True
        return super().allow_request(request, view)


class SearchRateThrottle(AnonRateThrottle):
    scope = 'search'

    @property
    def cache(self):
        return SafeCacheWrapper(super().cache)


class ImportRateThrottle(AnonRateThrottle):
    scope = 'import'

    @property
    def cache(self):
        return SafeCacheWrapper(super().cache)

    def allow_request(self, request, view):
        if request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            return True
        return super().allow_request(request, view)