from __future__ import annotations
import hashlib
import html
import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from html.parser import HTMLParser
from urllib.parse import quote, urlparse

import requests
from django.core.cache import cache


ANIMEGO_BASE = "https://animego.org"
CVH_API_BASE = "https://plapi.cdnvideohub.com/api/v1/player/sv"
REQUEST_TIMEOUT = (5, 15)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
    "Gecko/20100101 Firefox/127.0"
)


class AlternativeStreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class AlternativeStream:
    id: str
    label: str
    url: str
    referer: str


@dataclass(frozen=True)
class AlternativePlayback:
    id: str
    label: str
    translations: tuple[AlternativeStream, ...]
    episodes: tuple[int, ...]
    selected_episode: int


class _PlayerParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.voices: list[dict[str, str]] = []
        self.episodes: dict[int, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "button" and values.get("data-player"):
            self.voices.append(values)
        episode_number = values.get("data-episode-number")
        episode_id = values.get("data-episode")
        if episode_number and episode_id:
            try:
                self.episodes[int(episode_number)] = episode_id
            except ValueError:
                pass


class _VideoParametersParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parameters = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "video":
            return
        values = {key: value or "" for key, value in attrs}
        if values.get("id") == "video":
            self.parameters = values.get("data-parameters", "")


def _absolute_url(value: str) -> str:
    if value.startswith("//"):
        return f"https:{value}"
    return value


def _json_source(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("src") or "")
    if not isinstance(value, str) or not value:
        return ""
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return ""
    return str(parsed.get("src") or "") if isinstance(parsed, dict) else ""


class AnimeGoStreamResolver:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.session = session or requests.Session()

    def _get(self, url: str, *, headers: dict[str, str] | None = None) -> requests.Response:
        response = self.session.get(
            url,
            headers=headers or {"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response

    def find_anime_id(self, *, title: str, slug: str = "", title_en: str = "") -> str:
        cache_key = "animego:id:" + hashlib.sha256(
            f"{title}|{slug}|{title_en}".encode("utf-8")
        ).hexdigest()
        cached = cache.get(cache_key)
        if isinstance(cached, str) and cached:
            return cached

        response = self._get(f"{ANIMEGO_BASE}/search/anime?q={quote(title)}")
        candidates: list[tuple[str, str]] = []
        seen: set[str] = set()
        pattern = re.compile(
            r'''href=["'](?:https?://[^/"']+)?/anime/(?P<slug>[^?"']+?)-(?P<id>\d+)(?:[/?#"'])''',
            re.IGNORECASE,
        )
        for match in pattern.finditer(response.text):
            anime_id = match.group("id")
            if anime_id in seen:
                continue
            seen.add(anime_id)
            candidates.append((match.group("slug").strip("/"), anime_id))

        if not candidates:
            raise AlternativeStreamError("AnimeGO не нашёл подходящее аниме")

        desired = [value.casefold().strip("-/ ") for value in (slug, title_en) if value]
        best_slug, best_id = max(
            candidates,
            key=lambda item: max(
                [SequenceMatcher(None, item[0].casefold(), value).ratio() for value in desired]
                or [0.0]
            ),
        )
        score = max(
            [SequenceMatcher(None, best_slug.casefold(), value).ratio() for value in desired]
            or [1.0]
        )
        if desired and score < 0.55:
            raise AlternativeStreamError("AnimeGO вернул неоднозначный результат поиска")

        cache.set(cache_key, best_id, timeout=24 * 60 * 60)
        return best_id

    def _player_payload(self, anime_id: str, episode: int) -> tuple[str, tuple[int, ...], int]:
        headers = {
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{ANIMEGO_BASE}/",
        }
        root_url = f"{ANIMEGO_BASE}/player/{anime_id}"
        root = self._get(root_url, headers=headers).json()
        content = html.unescape(str((root.get("data") or {}).get("content") or ""))
        parser = _PlayerParser()
        parser.feed(content)
        episodes = tuple(sorted(parser.episodes)) or (1,)
        selected_episode = episode if episode in episodes else episodes[0]
        episode_id = parser.episodes.get(selected_episode)
        if selected_episode == episodes[0]:
            return content, episodes, selected_episode
        if not episode_id:
            raise AlternativeStreamError(f"AnimeGO: серия {selected_episode} не найдена")
        payload = self._get(
            f"{ANIMEGO_BASE}/player/videos/{episode_id}", headers=headers
        ).json()
        return (
            html.unescape(str((payload.get("data") or {}).get("content") or "")),
            episodes,
            selected_episode,
        )

    def _aniboom_stream(self, embed_url: str) -> str:
        response = self._get(
            embed_url,
            headers={
                "User-Agent": USER_AGENT,
                "Referer": f"{ANIMEGO_BASE}/",
                "Accept-Language": "ru-RU,ru;q=0.9",
            },
        )
        parser = _VideoParametersParser()
        parser.feed(response.text)
        if not parser.parameters:
            raise AlternativeStreamError("AniBoom не вернул параметры видео")
        try:
            data = json.loads(html.unescape(parser.parameters))
        except (TypeError, ValueError) as exc:
            raise AlternativeStreamError("AniBoom вернул повреждённые параметры") from exc
        hls_url = _json_source(data.get("hls")) or _json_source(data.get("fallbackHls"))
        if not hls_url:
            raise AlternativeStreamError("AniBoom не вернул HLS-поток")
        return _absolute_url(hls_url)

    def _cvh_streams(
        self,
        *,
        cvh_id: str,
        season: int,
        episode: int,
        label: str,
    ) -> list[str]:
        headers = {
            "User-Agent": USER_AGENT,
            "Referer": f"{ANIMEGO_BASE}/",
            "Accept": "application/json",
        }
        playlist = self._get(
            f"{CVH_API_BASE}/playlist?pub=747&aggr=mali&id={quote(cvh_id)}",
            headers=headers,
        ).json().get("items") or []
        seasons = {int(item.get("season") or 0) for item in playlist}
        selected_season = next(iter(seasons)) if len(seasons) == 1 else season
        matching = [
            item
            for item in playlist
            if int(item.get("season") or 0) == selected_season
            and int(item.get("episode") or 0) == episode
        ]
        if not matching:
            return []

        exact = [
            item for item in matching
            if str(item.get("voiceStudio") or "").casefold() == label.casefold()
        ]
        items = exact or matching[:1]
        urls: list[str] = []
        for item in items:
            video_id = item.get("vkId")
            if not video_id:
                continue
            sources = self._get(
                f"{CVH_API_BASE}/video/{quote(str(video_id))}", headers=headers
            ).json().get("sources") or {}
            hls_url = sources.get("hlsUrl")
            if isinstance(hls_url, str) and hls_url.startswith("http"):
                urls.append(hls_url)
        return urls

    def resolve(
        self,
        *,
        title: str,
        slug: str,
        title_en: str,
        season: int,
        episode: int,
    ) -> AlternativePlayback:
        anime_id = self.find_anime_id(title=title, slug=slug, title_en=title_en)
        player_html, episodes, selected_episode = self._player_payload(anime_id, episode)
        parser = _PlayerParser()
        parser.feed(player_html)

        streams: list[AlternativeStream] = []
        seen_urls: set[str] = set()
        for voice in parser.voices:
            provider = voice.get("data-provider-title", "").strip()
            if provider.casefold() == "kodik":
                continue
            label = voice.get("data-translation-title", "").replace(" (ошибка)", "").strip()
            embed_url = _absolute_url(voice.get("data-player", ""))
            urls: list[str] = []
            referer = f"{ANIMEGO_BASE}/"
            try:
                if provider.casefold() == "aniboom" and embed_url:
                    urls = [self._aniboom_stream(embed_url)]
                    referer = "https://aniboom.one/"
                elif provider.casefold() == "cvh" and embed_url:
                    path = urlparse(embed_url).path
                    match = re.search(r"/cdn-iframe/([^/]+)", path)
                    if match:
                        urls = self._cvh_streams(
                            cvh_id=match.group(1),
                            season=season,
                            episode=episode,
                            label=label,
                        )
            except (requests.RequestException, ValueError, AlternativeStreamError):
                continue

            for url in urls:
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                stream_id = hashlib.sha256(
                    (
                        f"{provider}|{voice.get('data-provider', '')}|"
                        f"{voice.get('data-translation-id', '')}|"
                        f"{voice.get('data-ptranslation', '')}|{label}"
                    ).encode("utf-8")
                ).hexdigest()[:16]
                streams.append(
                    AlternativeStream(
                        id=stream_id,
                        label=label or "Дополнительный поток",
                        url=url,
                        referer=referer,
                    )
                )
        return AlternativePlayback(
            id="reserve",
            label="Резервный",
            translations=tuple(streams),
            episodes=episodes,
            selected_episode=selected_episode,
        )
