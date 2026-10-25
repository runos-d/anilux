import time
from contextlib import ExitStack

from django.core.cache import cache


WINDOW_SECONDS = 3600
LIMIT = 100


class KodikLimitExceeded(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = max(1, retry_after)


def _subject_keys(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",", 1)[0].strip()
    ip = forwarded or request.META.get("REMOTE_ADDR", "unknown")
    keys = [f"kodik-quota:ip:{ip}"]
    if request.user.is_authenticated:
        keys.append(f"kodik-quota:user:{request.user.pk}")
    return sorted(keys)


def reserve_unique_ids(request, identifiers):
    now = int(time.time())
    identifiers = {str(value) for value in identifiers}
    keys = _subject_keys(request)
    with ExitStack() as stack:
        for key in keys:
            lock_factory = getattr(cache, "lock", None)
            if lock_factory:
                stack.enter_context(lock_factory(f"{key}:lock", timeout=5, blocking_timeout=2))
        states = {}
        for key in keys:
            state = cache.get(key) or {}
            state = {value: int(timestamp) for value, timestamp in state.items() if now - int(timestamp) < WINDOW_SECONDS}
            new_ids = identifiers.difference(state)
            if len(state) + len(new_ids) > LIMIT:
                oldest = min(state.values(), default=now)
                raise KodikLimitExceeded(WINDOW_SECONDS - (now - oldest))
            states[key] = (state, new_ids)
        for key, (state, new_ids) in states.items():
            state.update({value: now for value in new_ids})
            cache.set(key, state, timeout=WINDOW_SECONDS)
