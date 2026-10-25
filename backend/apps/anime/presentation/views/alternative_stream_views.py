from __future__ import annotations

import logging
import re
from urllib.parse import urlencode, urljoin, urlparse

import requests
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.anime.infrastructure.clients.animego_streams import (
    AnimeGoStreamResolver,
    AlternativeStreamError,
)
from apps.anime.infrastructure.models.anime import Anime


logger = logging.getLogger(__name__)
TOKEN_SALT = "anime.alternative-stream.v1"
TOKEN_MAX_AGE = 6 * 60 * 60
UPSTREAM_TIMEOUT = (5, 30)
URI_ATTRIBUTE_RE = re.compile(r'URI=(?P<quote>["\'])(?P<url>.*?)(?P=quote)')


def _validate_upstream_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Unsupported upstream URL")


def _stream_token(url: str, referer: str) -> str:
    _validate_upstream_url(url)
    return signing.dumps(
        {"url": url, "referer": referer},
        salt=TOKEN_SALT,
        compress=True,
    )


def _proxy_path(url: str, referer: str) -> str:
    token = _stream_token(url, referer)
    return f"{reverse('anime-alternative-stream-content')}?{urlencode({'token': token})}"


def _rewrite_playlist(content: str, base_url: str, referer: str) -> str:
    def rewrite_attribute(match: re.Match[str]) -> str:
        absolute = urljoin(base_url, match.group("url"))
        return f'URI={match.group("quote")}{_proxy_path(absolute, referer)}{match.group("quote")}'

    lines: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append(raw_line)
        elif line.startswith("#"):
            lines.append(URI_ATTRIBUTE_RE.sub(rewrite_attribute, raw_line))
        else:
            lines.append(_proxy_path(urljoin(base_url, line), referer))
    return "\n".join(lines) + "\n"


class AnimeAlternativeStreamsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk: int):
        try:
            anime = Anime.objects.get(pk=pk)
        except Anime.DoesNotExist:
            return Response({"error": "Аниме не найдено"}, status=status.HTTP_404_NOT_FOUND)

        try:
            episode = max(1, int(request.query_params.get("episode", 1)))
            season = max(1, int(request.query_params.get("season", 1)))
        except (TypeError, ValueError):
            return Response({"error": "Некорректный номер серии"}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"anime:alternative-streams:v2:{anime.pk}:{season}:{episode}"
        resolved = cache.get(cache_key)
        if not isinstance(resolved, dict):
            try:
                playback = AnimeGoStreamResolver().resolve(
                    title=anime.title_ru,
                    slug=anime.slug or "",
                    title_en=anime.title_en or "",
                    season=season,
                    episode=episode,
                )
                resolved = {
                    "id": playback.id,
                    "label": playback.label,
                    "episodes": list(playback.episodes),
                    "selected_episode": playback.selected_episode,
                    "translations": [
                        {
                            "id": translation.id,
                            "name": translation.label,
                            "url": translation.url,
                            "referer": translation.referer,
                        }
                        for translation in playback.translations
                    ],
                }
                cache.set(cache_key, resolved, timeout=10 * 60)
            except (requests.RequestException, AlternativeStreamError, ValueError) as exc:
                logger.info("Alternative stream lookup failed for anime %s: %s", anime.pk, exc)
                resolved = {}

        translations = []
        for translation in resolved.get("translations", []):
            try:
                source_url = _proxy_path(translation["url"], translation["referer"])
            except (KeyError, TypeError, ValueError):
                continue
            translations.append(
                {
                    "id": translation["id"],
                    "name": translation["name"],
                    "type": "voice",
                    "sources": [{"quality": "auto", "url": source_url}],
                }
            )

        streams = []
        if translations:
            default_translation = translations[0]
            episodes = [
                value
                for value in resolved.get("episodes", [])
                if isinstance(value, int) and value > 0
            ]
            streams.append(
                {
                    "id": resolved.get("id", "reserve"),
                    "label": resolved.get("label", "Резервный"),
                    "sources": default_translation["sources"],
                    "translation_id": default_translation["id"],
                    "translations": translations,
                    "episode_groups": [
                        {"season": 1, "label": "Серии", "episodes": episodes or [1]}
                    ],
                    "resolved_episode": resolved.get("selected_episode", episode),
                }
            )

        return Response(
            {"streams": streams, "episode": episode, "season": season},
            headers={"Cache-Control": "private, no-store"},
        )


class AlternativeStreamContentView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        token = request.query_params.get("token", "")
        try:
            data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
            upstream_url = str(data["url"])
            referer = str(data.get("referer") or "https://animego.org/")
            _validate_upstream_url(upstream_url)
        except (signing.BadSignature, signing.SignatureExpired, KeyError, TypeError, ValueError):
            return Response({"error": "Ссылка на поток недействительна"}, status=status.HTTP_403_FORBIDDEN)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
            "Referer": referer,
            "Origin": f"{urlparse(referer).scheme}://{urlparse(referer).netloc}",
        }
        range_header = request.headers.get("Range")
        if range_header:
            headers["Range"] = range_header

        try:
            upstream = requests.get(
                upstream_url,
                headers=headers,
                stream=True,
                timeout=UPSTREAM_TIMEOUT,
                allow_redirects=True,
            )
            upstream.raise_for_status()
            _validate_upstream_url(upstream.url)
        except (requests.RequestException, ValueError) as exc:
            logger.info("Alternative stream proxy failed for %s: %s", upstream_url, exc)
            return Response({"error": "Резервный поток временно недоступен"}, status=status.HTTP_502_BAD_GATEWAY)

        content_type = upstream.headers.get("Content-Type", "application/octet-stream")
        is_playlist = (
            ".m3u8" in urlparse(upstream.url).path
            or "mpegurl" in content_type.casefold()
        )
        if is_playlist:
            try:
                rewritten = _rewrite_playlist(upstream.text, upstream.url, referer)
            finally:
                upstream.close()
            response = HttpResponse(rewritten, content_type="application/vnd.apple.mpegurl")
            response["Cache-Control"] = "private, no-store"
            return response

        def chunks():
            try:
                yield from upstream.iter_content(chunk_size=128 * 1024)
            finally:
                upstream.close()

        response = StreamingHttpResponse(
            chunks(),
            status=upstream.status_code,
            content_type=content_type,
        )
        for header in ("Content-Length", "Content-Range", "Accept-Ranges"):
            if upstream.headers.get(header):
                response[header] = upstream.headers[header]
        response["Cache-Control"] = "private, no-store"
        return response
