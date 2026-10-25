import os

from django.core.exceptions import ImproperlyConfigured


_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off", ""}


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in _TRUE:
        return True
    if normalized in _FALSE:
        return False
    raise ImproperlyConfigured(
        f"{name} must be one of: 1/0, true/false, yes/no, on/off"
    )


FEATURE_DUBS_ENABLED = env_flag("FEATURE_DUBS_ENABLED")
FEATURE_REACTOR_ENABLED = env_flag("FEATURE_REACTOR_ENABLED")
FEATURE_TWO_FACTOR_ENABLED = env_flag("FEATURE_TWO_FACTOR_ENABLED")
FEATURE_STUDIO_REACTIONS_ENABLED = env_flag("FEATURE_STUDIO_REACTIONS_ENABLED")
FEATURE_STUDIO_SYNC_ENABLED = env_flag("FEATURE_STUDIO_SYNC_ENABLED")
