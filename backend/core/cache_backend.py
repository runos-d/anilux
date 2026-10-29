"""Fail quickly during an outage; never silently bypass security counters."""
import threading
import time
from django_redis.cache import RedisCache
from redis.exceptions import RedisError


class CacheUnavailable(RuntimeError):
    pass


class CircuitRedisCache(RedisCache):
    # Django creates cache backends per thread. Keep outage state per Redis URL
    # across those instances so ASGI requests share the same recovery probe.
    _circuits = {}
    _circuits_lock = threading.Lock()

    def __init__(self, server, params):
        super().__init__(server, params)
        with self._circuits_lock:
            self._state = self._circuits.setdefault(repr(server), {'until': 0, 'probe': threading.Lock()})

    def _call(self, name, *args, **kwargs):
        now = time.monotonic()
        if now < self._state['until']:
            raise CacheUnavailable('Cache dependency is unavailable')
        probing = bool(self._state['until'])
        if probing and not self._state['probe'].acquire(blocking=False):
            raise CacheUnavailable('Cache dependency recovery in progress')
        try:
            value = getattr(super(), name)(*args, **kwargs)
            self._state['until'] = 0
            return value
        except (RedisError, OSError) as error:
            self._state['until'] = time.monotonic() + 5
            raise CacheUnavailable('Cache dependency is unavailable') from error
        finally:
            if probing:
                self._state['probe'].release()

    def get(self, *args, **kwargs): return self._call('get', *args, **kwargs)
    def set(self, *args, **kwargs): return self._call('set', *args, **kwargs)
    def add(self, *args, **kwargs): return self._call('add', *args, **kwargs)
    def delete(self, *args, **kwargs): return self._call('delete', *args, **kwargs)
    def get_many(self, *args, **kwargs): return self._call('get_many', *args, **kwargs)
    def set_many(self, *args, **kwargs): return self._call('set_many', *args, **kwargs)
    def incr(self, *args, **kwargs): return self._call('incr', *args, **kwargs)


def api_exception_handler(error, context):
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    if isinstance(error, (CacheUnavailable, RedisError)):
        return Response({'detail': 'Сервис временно перегружен. Повторите позже.'}, status=503,
                        headers={'Retry-After': '5', 'Cache-Control': 'private, no-store'})
    return exception_handler(error, context)
