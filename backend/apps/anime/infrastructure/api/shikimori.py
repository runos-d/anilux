import os
import requests
import logging
import threading
import time
from typing import Any, Dict, List, Optional
from django.core.cache import cache
from redis.exceptions import ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)

SHIKIMORI_BASE_URL = os.environ.get('SHIKIMORI_BASE_URL', 'https://shikimori.one/api')
SHIKIMORI_USER_AGENT = os.environ.get('SHIKIMORI_USER_AGENT', 'Project/1.0')
SHIKIMORI_API_TIMEOUT = int(os.environ.get('SHIKIMORI_API_TIMEOUT', '15'))
SHIKIMORI_CLIENT_ID = os.environ.get('SHIKIMORI_CLIENT_ID')
SHIKIMORI_CLIENT_SECRET = os.environ.get('SHIKIMORI_CLIENT_SECRET')
SHIKIMORI_TOKEN_URL = f"{(SHIKIMORI_BASE_URL or 'https://shikimori.io/api').rstrip('/')}/oauth/token"


def safe_cache_get(key: str, default=None):
    try:
        return cache.get(key, default)
    except RedisConnectionError:
        logger.debug("Redis connection failed for cache get: %s", key)
        return default
    except Exception as e:
        logger.debug("Cache get failed for %s: %s", key, e)
        return default


def safe_cache_set(key: str, value: Any, timeout: int = 3600) -> bool:
    try:
        cache.set(key, value, timeout)
        return True
    except RedisConnectionError:
        logger.debug("Redis connection failed for cache set: %s", key)
        return False
    except Exception as e:
        logger.debug("Cache set failed for %s: %s", key, e)
        return False


class ShikimoriAPI:
    def __init__(
        self,
        base_url: str = SHIKIMORI_BASE_URL,
        user_agent: str = SHIKIMORI_USER_AGENT,
        client_id: Optional[str] = SHIKIMORI_CLIENT_ID,
        client_secret: Optional[str] = SHIKIMORI_CLIENT_SECRET,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.user_agent = user_agent
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_lock = threading.Lock()
        self._refreshing = False
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        })

    @property
    def _authenticated(self) -> bool:
        return bool(self.client_id and self.client_secret)

    def _get_auth_header(self) -> Dict[str, str]:
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}

    def _fetch_token(self, grant_type: str = "client_credentials", **extra_params: Any) -> bool:
        if not self._authenticated:
            return False
        data = {
            "grant_type": grant_type,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        data.update(extra_params)
        if self._refresh_token and grant_type == "refresh_token":
            data["refresh_token"] = self._refresh_token
        try:
            resp = requests.post(SHIKIMORI_TOKEN_URL, data=data, timeout=SHIKIMORI_API_TIMEOUT)
            resp.raise_for_status()
            token_data = resp.json()
            self._access_token = token_data.get("access_token")
            new_refresh = token_data.get("refresh_token")
            if new_refresh:
                self._refresh_token = new_refresh
            logger.info("Shikimori token refreshed successfully")
            return bool(self._access_token)
        except requests.RequestException as e:
            logger.error("Shikimori token fetch failed: %s", e)
            return False

    def _ensure_token(self) -> bool:
        if self._access_token:
            return True
        if not self._authenticated:
            return False
        with self._token_lock:
            if self._access_token:
                return True
            if self._refreshing:
                while self._refreshing:
                    time.sleep(0.1)
                return bool(self._access_token)
            self._refreshing = True
        try:
            result = self._fetch_token()
            return result
        finally:
            with self._token_lock:
                self._refreshing = False

    def _request(self, method: str, url: str, **kwargs: Any) -> Optional[requests.Response]:
        headers = kwargs.pop("headers", {})
        headers.update(self._get_auth_header())
        kwargs["headers"] = headers
        kwargs.setdefault("timeout", SHIKIMORI_API_TIMEOUT)

        resp = self.session.request(method, url, **kwargs)

        if resp.status_code == 401 and self._authenticated:
            logger.warning("Shikimori 401 received, attempting token refresh")
            if self._ensure_token():
                headers.update(self._get_auth_header())
                kwargs["headers"] = headers
                resp = self.session.request(method, url, **kwargs)

        return resp

    def _handle_response(self, resp: requests.Response) -> Any:
        if resp.status_code == 429:
            logger.warning("Shikimori rate limit hit, retrying after delay")
            time.sleep(2)
            resp = self.session.request(resp.request.method, resp.request.url, timeout=SHIKIMORI_API_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def get_anime(self, anime_id: int) -> Optional[Dict[str, Any]]:
        cache_key = f"shikimori:anime:{anime_id}"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/animes/{anime_id}"
        try:
            resp = self._request("GET", url)
            if resp is None:
                return None
            data = self._handle_response(resp)
            safe_cache_set(cache_key, data, timeout=3600)
            return data
        except requests.RequestException as e:
            logger.warning("Shikimori anime fetch failed for %s: %s", anime_id, e)
            return None
        except Exception as e:
            logger.warning("Shikimori anime parse failed for %s: %s", anime_id, e)
            return None

    def list_animes(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/animes"
        try:
            resp = self._request("GET", url, params=params)
            if resp is None:
                return []
            data = self._handle_response(resp)
            if isinstance(data, list):
                return data
            return []
        except requests.RequestException as e:
            logger.warning("Shikimori animes list fetch failed: %s", e)
            return []
        except Exception as e:
            logger.warning("Shikimori animes list parse failed: %s", e)
            return []

    def get_franchise(self, anime_id: int) -> Optional[Dict[str, Any]]:
        cache_key = f"shikimori:franchise:{anime_id}"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/animes/{anime_id}/franchise"
        try:
            resp = self._request("GET", url)
            if resp is None:
                return None
            if resp.status_code == 404:
                data = {"nodes": [], "links": []}
                safe_cache_set(cache_key, data, timeout=3600)
                return data
            data = self._handle_response(resp)
            safe_cache_set(cache_key, data, timeout=3600)
            return data
        except requests.RequestException as e:
            logger.warning("Shikimori franchise fetch failed for %s: %s", anime_id, e)
            return None
        except Exception as e:
            logger.warning("Shikimori franchise parse failed for %s: %s", anime_id, e)
            return None

    def get_calendar(self, censored: bool = True) -> List[Dict[str, Any]]:
        cache_key = "shikimori:calendar"
        if censored:
            cache_key += ":censored"
        else:
            cache_key += ":all"

        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/calendar"
        params = {}
        if not censored:
            params["censored"] = "false"

        try:
            resp = self._request("GET", url, params=params)
            if resp is None:
                return []
            data = self._handle_response(resp)
            safe_cache_set(cache_key, data, timeout=3600)
            return data
        except requests.RequestException as e:
            logger.warning("Shikimori calendar fetch failed: %s", e)
            return []
        except Exception as e:
            logger.warning("Shikimori calendar parse failed: %s", e)
            return []

    def get_genres(self) -> List[Dict[str, Any]]:
        cache_key = "shikimori:genres"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/genres"
        try:
            resp = self._request("GET", url)
            if resp is None:
                return []
            data = self._handle_response(resp)
            safe_cache_set(cache_key, data, timeout=3600)
            return data if isinstance(data, list) else []
        except requests.RequestException as e:
            logger.warning("Shikimori genres fetch failed: %s", e)
            return []
        except Exception as e:
            logger.warning("Shikimori genres parse failed: %s", e)
            return []


shikimori_api = ShikimoriAPI()
