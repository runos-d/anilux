import os

KODIK_API_TOKEN = os.environ.get('KODIK_API_TOKEN')
KODIK_PUBLIC_KEY = os.environ.get('KODIK_PUBLIC_KEY') or KODIK_API_TOKEN
KODIK_PRIVATE_KEY = os.environ.get('KODIK_PRIVATE_KEY')

KODIK_API_BASE = os.environ.get('KODIK_API_BASE')
KODIK_PLAYER_BASE = os.environ.get('KODIK_PLAYER_BASE')
KODIK_DB_BASE = os.environ.get('KODIK_DB_BASE')
KODIK_SOCIAL_BASE = os.environ.get('KODIK_SOCIAL_BASE')
KODIK_VIDEO_BASE = os.environ.get('KODIK_VIDEO_BASE')
KODIK_SCREENSHOTS_BASE = os.environ.get('KODIK_SCREENSHOTS_BASE')

KODIK_OLD_DOMAINS = [
    'kodik.cc',
    'kodik.info',
    'kodik.biz',
    'kodikai.com',
]


def normalize_kodik_player_link(link: str) -> str:
    if not link:
        return link

    if link.startswith('//'):
        link = 'https:' + link
    elif not link.startswith('http'):
        link = 'https://' + link

    for old in KODIK_OLD_DOMAINS:
        if old in link:
            link = link.replace(old, 'kodikplayer.com')
            break

    return link


