from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

KODIK_PLAYER_DOMAIN = "kodikplayer.com"
KODIK_VIDEO_INFO_ENDPOINT = "/ftor"
KODIK_REQUEST_TIMEOUT = (5, 20)
KODIK_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

_LINK_RE = re.compile(
    r"^(?P<protocol>http[s]?:|)//"
    r"(?P<host>[a-z0-9]+\.[a-z]+)/"
    r"(?P<type>[a-z]+)/"
    r"(?P<id>\d+)/"
    r"(?P<hash>[0-9a-z]+)/"
    r"(?P<quality>\d+p)(?:.*)$"
)
_URL_PARAMS_RE = re.compile(r"var\s+urlParams\s*=\s*'(?P<params>[^']+)';")
_TRANSLATION_RE = re.compile(
    r'var\s+translationId\s*=\s*(?P<id>\d+);\s*'
    r'var\s+translationTitle\s*=\s*"(?P<title>[^"]+)";',
    re.IGNORECASE | re.DOTALL,
)
_PLAYER_SINGLE_RE = re.compile(
    r'src="(?P<link>/assets/js/app\.player_single\.[a-z0-9]+\.js)"',
    re.IGNORECASE,
)
_ENDPOINT_RE = re.compile(
    r'type:"POST",url:atob\("(?P<endpoint>[^"]+)"\)',
    re.IGNORECASE,
)


class KodikWrapperError(RuntimeError):
    pass


def _normalize_link(link: str, player_domain: str = KODIK_PLAYER_DOMAIN) -> str:
    if not link:
        raise KodikWrapperError("Kodik link is not provided")
    if link.startswith("//"):
        return f"https:{link}"
    if link.startswith("http"):
        return link
    return f"https://{player_domain}/{link.lstrip('/')}"


def _decode_base64(value: str) -> str:
    padded = value + "=" * (-len(value) % 4)
    return base64.b64decode(padded.encode("utf-8")).decode("utf-8")


def _decode_video_source(source: str) -> str:
    decoded_chars: List[str] = []
    for char in source:
        if char.isascii() and char.isalpha():
            code = ord(char)
            shifted = code + 18
            if shifted > (90 if code <= 90 else 122):
                shifted -= 26
            decoded_chars.append(chr(shifted))
        else:
            decoded_chars.append(char)
    return _decode_base64("".join(decoded_chars))


class KodikWrapper:
    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(KODIK_HEADERS)

    def _get(self, url: str) -> requests.Response:
        response = self.session.get(url, timeout=KODIK_REQUEST_TIMEOUT)
        response.raise_for_status()
        return response

    @staticmethod
    def normalize_link(link: str) -> str:
        return _normalize_link(link)

    def parse_link(self, link: str, extended: bool = False) -> Dict[str, Any]:
        absolute = _normalize_link(link)
        match = _LINK_RE.match(link)
        if not match:
            raise KodikWrapperError(f"Kodik link is not valid: {link}")

        parsed: Dict[str, Any] = {
            key: value for key, value in match.groupdict().items() if key != "protocol"
        }
        if not extended:
            return parsed

        page = self._get(absolute).text
        params_match = _URL_PARAMS_RE.search(page)
        if not params_match:
            raise KodikWrapperError("Kodik player page has no urlParams")
        translation_match = _TRANSLATION_RE.search(page)
        if not translation_match:
            raise KodikWrapperError("Kodik player page has no translation info")

        player_single_match = _PLAYER_SINGLE_RE.search(page)
        parsed["ex"] = {
            "urlParams": json.loads(params_match.group("params")),
            "translation": {
                "id": int(translation_match.group("id")),
                "title": translation_match.group("title"),
            },
            "playerSingleUrl": (
                player_single_match.group("link") if player_single_match else None
            ),
        }
        return parsed

    def get_actual_video_info_endpoint(self, player_single_url: Optional[str]) -> str:
        if not player_single_url:
            return KODIK_VIDEO_INFO_ENDPOINT
        try:
            script = self._get(_normalize_link(player_single_url)).text
            match = _ENDPOINT_RE.search(script)
            if not match:
                return KODIK_VIDEO_INFO_ENDPOINT
            endpoint = _decode_base64(match.group("endpoint"))
            return endpoint or KODIK_VIDEO_INFO_ENDPOINT
        except (requests.RequestException, ValueError, UnicodeDecodeError) as exc:
            logger.warning("Could not resolve Kodik video endpoint: %s", exc)
            return KODIK_VIDEO_INFO_ENDPOINT

    def get_links(self, link: str) -> Dict[str, List[Dict[str, str]]]:
        try:
            parsed = self.parse_link(link, extended=True)
        except requests.RequestException as exc:
            raise KodikWrapperError(f"Kodik player request failed: {exc}") from exc

        endpoint = self.get_actual_video_info_endpoint(parsed["ex"].get("playerSingleUrl"))
        host = parsed["host"]
        request_url = f"https://{host}{endpoint}"
        params = {
            key: parsed[key] for key in ("id", "hash", "type") if parsed.get(key)
        }

        try:
            response = self._get(request_url) if not params else self.session.get(
                request_url, params=params, timeout=KODIK_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise KodikWrapperError(f"Kodik video API request failed: {exc}") from exc

        links = payload.get("links")
        if not isinstance(links, dict) or not links:
            raise KodikWrapperError("Kodik video API returned no playable sources")

        decoded: Dict[str, List[Dict[str, str]]] = {}
        for quality, items in links.items():
            entries: List[Dict[str, str]] = []
            for item in items if isinstance(items, list) else [items]:
                if not isinstance(item, dict):
                    continue
                source = item.get("src") or item.get("Src")
                if not source:
                    continue
                try:
                    url = _decode_video_source(source)
                except (ValueError, UnicodeDecodeError) as exc:
                    logger.warning("Could not decode Kodik source for %s: %s", quality, exc)
                    continue
                entries.append({
                    "src": f"https:{url}" if url.startswith("//") else url,
                    "type": item.get("type") or "application/x-mpegURL",
                })
            if entries:
                decoded[str(quality)] = entries

        if not decoded:
            raise KodikWrapperError("Kodik video API returned no playable sources")
        return decoded
