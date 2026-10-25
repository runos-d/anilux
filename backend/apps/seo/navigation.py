import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings


@lru_cache(maxsize=4)
def _read(path, mtime):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def site_navigation():
    candidates = [Path(settings.SEO_FRONTEND_INDEX).parent / 'site-navigation.json',
                  settings.BASE_DIR / 'site-navigation.json',
                  settings.BASE_DIR.parent / 'frontend' / 'public' / 'site-navigation.json']
    for path in candidates:
        if path.is_file():
            return _read(str(path), path.stat().st_mtime_ns)
    return {'email': '', 'groups': [], 'documents': []}
