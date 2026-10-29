"""Isolated worker fixture: local source only, no provider traffic."""
from config.celery import app
app.loader.import_default_modules()
from apps.anime.application.anime_service import anime_service
import requests

def disabled_http(*args, **kwargs):
    raise RuntimeError('External HTTP disabled in isolated audit worker')
requests.sessions.Session.request = disabled_http
anime_service.get_anime_m3u8 = lambda **kwargs: '/audit-downloads/source.mp4'
