import hashlib
import hmac
import logging
import time
from datetime import datetime, timedelta, timezone as datetime_timezone
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache
from django.db import connection, transaction, models, IntegrityError
from django.utils import timezone
import requests

from apps.anime.infrastructure.models.anime import Anime, Genre, Studio, Episode, VideoSource, Translation, WatchProgress, AnimeUpdate, Franchise
from apps.anime.infrastructure.api.external_anime_api import external_anime_api
from apps.anime.application.image_service import ImageService
from apps.anime.application.cache_utils import safe_cache_get, safe_cache_set
from apps.anime.infrastructure.clients.kodik_config import (
    KODIK_PRIVATE_KEY,
    KODIK_PUBLIC_KEY,
    KODIK_VIDEO_BASE,
)
from apps.anime.infrastructure.clients.kodik_wrapper import KodikWrapper

logger = logging.getLogger(__name__)


class AnimeService:
    def __init__(self):
        self.cache_timeout = 3600
        self.image_service = ImageService()

    def search_anime(self, query: str, limit: int = 20) -> List[Dict]:
        cache_key = f"search_{query}_{limit}"
        cached = safe_cache_get(cache_key)
        if cached:
            return cached
        try:
            data = external_anime_api.search(title=query, limit=limit, with_material_data=True)
            results = data.get("results", [])
            safe_cache_set(cache_key, results, self.cache_timeout)
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_anime_by_id(self, external_id: int, source: str = "shikimori") -> Optional[Dict]:
        cache_key = f"anime_{source}_{external_id}"
        cached = safe_cache_get(cache_key)
        if cached:
            return cached
        try:
            if source == "shikimori":
                result = external_anime_api.get_anime_details(external_id)
            else:
                result = None
            if result:
                safe_cache_set(cache_key, result, self.cache_timeout)
            return result
        except Exception as e:
            logger.error(f"Get anime by id error: {e}")
            return None

    def get_all_anime(self, source: str = "kodik", page: int = 1, limit: int = 50) -> List[Dict]:
        cache_key = f"all_anime_{source}_{page}_{limit}"
        cached = safe_cache_get(cache_key)
        if cached:
            return cached
        try:
            if source == "kodik":
                data = external_anime_api.list_materials(limit=limit, page=page)
                results = data.get("results", [])
            else:
                params = {"page": page, "limit": limit, "order": "id"}
                data = external_anime_api.get_animes(params)
                results = data if isinstance(data, list) else []
            safe_cache_set(cache_key, results, self.cache_timeout)
            return results
        except Exception as e:
            logger.error(f"Get all anime error: {e}")
            return []

    def get_popular_anime(self, page: int = 1, limit: int = 50) -> List[Dict]:
        try:
            params = {"page": page, "limit": limit, "order": "popularity"}
            data = external_anime_api.get_animes(params)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Get popular anime error: {e}")
            return []

    def get_anime_by_genre(self, genre_id: int, page: int = 1, limit: int = 50) -> List[Dict]:
        try:
            params = {"genre": genre_id, "page": page, "limit": limit, "order": "popularity"}
            data = external_anime_api.get_animes(params)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Get anime by genre error: {e}")
            return []

    def get_anime_by_year(self, year: int, page: int = 1, limit: int = 50) -> List[Dict]:
        try:
            params = {"year": year, "page": page, "limit": limit, "order": "popularity"}
            data = external_anime_api.get_animes(params)
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Get anime by year error: {e}")
            return []

    def get_genres(self) -> List[Dict]:
        try:
            return external_anime_api.get_genres_shikimori()
        except Exception as e:
            logger.error(f"Get genres error: {e}")
            return []

    def get_filters(self) -> Dict[str, Any]:
        return external_anime_api.get_filters()

    def get_franchise(self, shikimori_id: int) -> Optional[Dict[str, Any]]:
        return external_anime_api.get_franchise(shikimori_id)

    def get_franchise_nodes(self, shikimori_id: int) -> List[Dict[str, Any]]:
        data = self.get_franchise(shikimori_id)
        return data.get("nodes", []) if data else []

    def get_franchise_links(self, shikimori_id: int) -> List[Dict[str, Any]]:
        data = self.get_franchise(shikimori_id)
        return data.get("links", []) if data else []

    def get_current_node(self, shikimori_id: int) -> Optional[Dict[str, Any]]:
        data = self.get_franchise(shikimori_id)
        if not data:
            return None
        current_id = data.get("current_id")
        if current_id is None:
            return None
        for node in data.get("nodes", []) or []:
            if node.get("id") == current_id:
                return node
        return None

    def build_franchise_graph(self, shikimori_id: int) -> Dict[str, Any]:
        data = self.get_franchise(shikimori_id)
        if not data:
            return {"nodes": [], "links": [], "current_id": shikimori_id}
        return {
            "nodes": data.get("nodes", []) or [],
            "links": data.get("links", []) or [],
            "current_id": data.get("current_id", shikimori_id),
        }

    def get_franchise_slug(self, shikimori_id: int) -> Optional[str]:
        cache_key = f"shikimori:franchise_slug:{shikimori_id}"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached
        anime = external_anime_api.get_anime_details(shikimori_id)
        if not anime:
            return None
        slug = anime.get("franchise")
        slug = slug.strip() if isinstance(slug, str) and slug.strip() else None
        safe_cache_set(cache_key, slug, timeout=3600)
        return slug

    def search_by_shikimori_id(self, shikimori_id: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        params = {"shikimori_id": shikimori_id, "with_material_data": True, "limit": limit}
        data = external_anime_api.search(**params)
        results = data.get("results", [])
        return results[0] if results else None

    def search_by_kodik_id(self, kodik_id: str) -> Optional[Dict[str, Any]]:
        params = {"id": kodik_id, "with_material_data": True, "limit": 1}
        data = external_anime_api.search(**params)
        results = data.get("results", [])
        return results[0] if results else None

    def get_translations(self, shikimori_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {
            "shikimori_id": shikimori_id,
            "with_episodes_data": False,
            "with_seasons": True,
            "limit": limit,
        }
        data = external_anime_api.search(**params)
        results = data.get("results", [])
        translations_map: Dict[str, Dict[str, Any]] = {}
        for result in results:
            translation = result.get("translation") or {}
            if not translation:
                continue
            translation_id = translation.get("id")
            if translation_id is None:
                continue
            translation_name = translation.get("title", "Неизвестно")
            translation_type = translation.get("type", "voice")
            if translation_id not in translations_map:
                translations_map[translation_id] = {
                    "id": translation_id,
                    "name": translation_name,
                    "type": translation_type,
                    "quality": result.get("quality", ""),
                    "episodes_done": 0,
                    "total_episodes": result.get("episodes_count") or 0,
                    "is_complete": False,
                    "kodik_link": result.get("link", ""),
                    "material_type": result.get("type"),
                    "logo": None,
                    "last_season": None,
                    "seasons": {},
                }
            t = translations_map[translation_id]
            episodes = result.get("episodes_count") or 0
            if episodes > t["episodes_done"]:
                t["episodes_done"] = episodes
            if episodes > t["total_episodes"]:
                t["total_episodes"] = episodes

            try:
                result_last_season = int(result.get("last_season"))
            except (TypeError, ValueError):
                result_last_season = None
            if result_last_season is not None:
                if t["last_season"] is None or result_last_season > t["last_season"]:
                    t["last_season"] = result_last_season

            for season_key, season_data in (result.get("seasons") or {}).items():
                try:
                    season_number = int(season_key)
                except (TypeError, ValueError):
                    continue
                if season_number < 0:
                    continue
                season_meta = t["seasons"].setdefault(
                    str(season_number),
                    {"title": None, "episodes": []},
                )
                title = (season_data or {}).get("title")
                if isinstance(title, str) and title.strip():
                    season_meta["title"] = title.strip()
                episode_keys = ((season_data or {}).get("episodes") or {}).keys()
                known_episodes = set(season_meta["episodes"])
                for episode_key in episode_keys:
                    try:
                        episode_number = int(episode_key)
                    except (TypeError, ValueError):
                        continue
                    if episode_number > 0:
                        known_episodes.add(episode_number)
                season_meta["episodes"] = sorted(known_episodes)

        translations = list(translations_map.values())
        for translation in translations:
            seasons = translation["seasons"]
            available_seasons = [
                int(season_key) for season_key in seasons.keys()
            ]
            if available_seasons:
                max_season = max(available_seasons)
                if translation["last_season"] is None or max_season > translation["last_season"]:
                    translation["last_season"] = max_season
        translations.sort(key=lambda x: x["episodes_done"], reverse=True)
        return translations

    def get_episode_info(
        self,
        shikimori_id: str,
        episode: int,
        season: str,
        translation_id: Optional[str] = None,
        with_screenshots: bool = True,
    ) -> Optional[Dict[str, Any]]:
        params = {
            "with_material_data": False,
            "with_seasons": True,
            "with_episodes": True,
            "with_episodes_data": with_screenshots,
            "limit": 100,
        }
        if shikimori_id:
            params["shikimori_id"] = shikimori_id
        if translation_id:
            params["translation_id"] = translation_id
        data = external_anime_api.search(**params)
        season_key = str(season)
        ep_key = str(episode)
        for res in data.get("results", []):
            if translation_id:
                tid = (res.get("translation") or {}).get("id")
                if str(tid) != str(translation_id):
                    continue
            s_data = ((res.get("seasons") or {}).get(season_key)) or {}
            ep_data = s_data.get("episodes") or {}
            ep_value = ep_data.get(ep_key) or ep_data.get(
                int(ep_key) if ep_key.isdigit() else ep_key
            )
            if isinstance(ep_value, dict):
                ep_url = ep_value.get("link") or ""
                screenshots = ep_value.get("screenshots") or []
            else:
                ep_url = ep_value or ""
                screenshots = []
            if not ep_url:
                continue
            if not screenshots:
                screenshots = res.get("screenshots") or []
            previews = [
                str(url.strip())
                for url in screenshots
                if isinstance(url, str) and url.strip()
            ]
            return {"url": ep_url.strip(), "screenshots": previews}
        return None

    def get_episode_url(self, shikimori_id: str, episode: int, season: str, translation_id: Optional[str] = None) -> Optional[str]:
        episode_info = self.get_episode_info(
            shikimori_id,
            episode,
            season,
            translation_id,
            with_screenshots=False,
        )
        return episode_info["url"] if episode_info else None


    def _get_video_links_via_wrapper(self, link: str) -> Dict[str, str]:
        try:
            quality_map = KodikWrapper().get_links(link)
        except Exception as exc:
            logger.warning("Kodik wrapper could not resolve %s: %s", link, exc)
            return {}

        sources: Dict[str, str] = {}
        for quality, items in quality_map.items():
            for item in items:
                src = item.get("src")
                if src:
                    sources[str(quality)] = src
                    break
        return sources

    def get_video_links(self, episode_url: str, user_ip: str = "1.1.1.1") -> Dict[str, str]:
        if not episode_url:
            raise RuntimeError("Kodik episode link is not provided")

        link = episode_url.strip()
        if link.startswith("https:"):
            link = link[6:]
        elif link.startswith("http:"):
            link = link[5:]

        deadline = (datetime.now(datetime_timezone.utc) + timedelta(hours=6)).strftime("%Y%m%d%H")
        cache_seed = f"{link}:{user_ip}:{deadline}"
        cache_key = f"kodik:direct:{hashlib.sha256(cache_seed.encode()).hexdigest()}"
        cached = safe_cache_get(cache_key)
        if isinstance(cached, dict):
            return cached

        sources = self._get_video_links_via_wrapper(link)
        if sources:
            safe_cache_set(cache_key, sources, timeout=1800)
            return sources

        if not KODIK_PRIVATE_KEY or not KODIK_PUBLIC_KEY or not KODIK_VIDEO_BASE:
            raise RuntimeError("Ошибка воспроизведение... Попробуйте перезагрузить страницу")

        signature = hmac.new(
            KODIK_PRIVATE_KEY.encode("utf-8"),
            f"{link}:{user_ip}:{deadline}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        response = requests.get(
            f"{KODIK_VIDEO_BASE.rstrip('/')}/api/video-links",
            params={
                "link": link,
                "p": KODIK_PUBLIC_KEY,
                "ip": user_ip,
                "d": deadline,
                "s": signature,
            },
            timeout=(5, 15),
        )
        response.raise_for_status()

        sources: Dict[str, str] = {}
        for quality, value in (response.json().get("links") or {}).items():
            items = value if isinstance(value, list) else [value]
            for item in items:
                if not isinstance(item, dict):
                    continue
                source = item.get("Src") or item.get("src") or item.get("File") or item.get("file")
                if source:
                    sources[str(quality)] = "https:" + source if source.startswith("//") else source
                    break

        if not sources:
            raise RuntimeError("Kodik video API returned no playable sources")
        safe_cache_set(cache_key, sources, timeout=1800)
        return sources

    def get_m3u8_url(self, episode_url: str, user_ip: str = "1.1.1.1", quality: str = "720") -> Optional[str]:
        sources = self.get_video_links(episode_url, user_ip)
        preferred = [quality, "1080", "720", "480", "360", "240"]
        return next((sources[item] for item in preferred if item in sources), None)

    def get_anime_m3u8(self, anime_id: int, episode: int = 1, season: int = 1, translation_id: Optional[str] = None, user_ip: str = "1.1.1.1", quality: str = "720") -> Optional[str]:
        try:
            anime = Anime.objects.get(pk=anime_id)
        except Anime.DoesNotExist:
            return None
        external_id = anime.shikimori_id or anime.kodik_id
        if not external_id:
            return None
        episode_url = self.get_episode_url(str(external_id), episode, str(season), translation_id)
        if not episode_url:
            return None
        return self.get_m3u8_url(episode_url, user_ip, quality)

    def get_video_segments(self, episode_url: str, user_ip: str = "1.1.1.1") -> Tuple[Optional[Dict], Optional[Dict]]:
        return None, None

    def get_video_sources(self, anime_id: str, episode_num: int = 1, translation_id: str = "0") -> Dict:
        cache_key = f"video_sources_{anime_id}_{episode_num}_{translation_id}"
        cached = safe_cache_get(cache_key)
        if cached:
            return cached
        try:
            anime = Anime.objects.get(id=anime_id)
            video_sources = {}
            sources = VideoSource.objects.filter(anime=anime, is_available=True).select_related("video_source").prefetch_related("qualities")
            for vs in sources:
                source_data = {"name": vs.source, "m3u8_url": None, "video_url": None, "qualities": []}
                for q in vs.qualities.filter(is_available=True):
                    source_data["qualities"].append({
                        "quality": q.quality,
                        "resolution": q.resolution,
                        "video_url": q.video_url,
                        "m3u8_url": q.m3u8_url,
                    })
                    if not source_data["m3u8_url"] and q.m3u8_url:
                        source_data["m3u8_url"] = q.m3u8_url
                    if not source_data["video_url"] and q.video_url:
                        source_data["video_url"] = q.video_url
                video_sources[vs.source] = source_data
            safe_cache_set(cache_key, video_sources, 1800)
            return video_sources
        except Exception as e:
            logger.error(f"Get video sources error: {e}")
            return {}

    def get_streaming_url(self, anime_id: str, episode_num: int = 1, translation_id: str = "0", quality: str = "720") -> Optional[str]:
        video_sources = self.get_video_sources(anime_id, episode_num, translation_id)
        for source_name, source_data in video_sources.items():
            if source_name == "kodik":
                if source_data.get("m3u8_url"):
                    return source_data["m3u8_url"]
                elif source_data.get("video_url"):
                    return source_data["video_url"]
        return None

    def get_video_qualities(self, anime_id: str, source: str = "kodik") -> List[Dict]:
        try:
            video_sources = VideoSource.objects.filter(anime_id=anime_id, source=source, is_available=True).select_related("video_source").prefetch_related("qualities")
            qualities = []
            for vs in video_sources:
                for q in vs.qualities.filter(is_available=True):
                    qualities.append({
                        "quality": q.quality,
                        "resolution": q.resolution,
                        "video_url": q.video_url,
                        "m3u8_url": q.m3u8_url,
                    })
            return qualities
        except Exception as e:
            logger.error(f"Get video qualities error: {e}")
            return []

    def save_watch_progress(self, user, anime_id: int, episode_id: int, current_time: int, duration: int = None):
        try:
            anime = Anime.objects.get(id=anime_id)
            episode = Episode.objects.get(id=episode_id)
            with transaction.atomic():
                progress, created = WatchProgress.objects.get_or_create(
                    user=user,
                    episode=episode,
                    defaults={
                        "current_time": current_time,
                        "duration": duration,
                        "is_completed": bool(duration and current_time >= duration * 0.9),
                    },
                )
                if not created:
                    progress.current_time = current_time
                    progress.duration = duration
                    progress.is_completed = bool(duration and current_time >= duration * 0.9)
                    progress.watch_count = (progress.watch_count or 0) + 1
                    progress.save(update_fields=["current_time", "duration", "is_completed", "watch_count", "updated_at"])
                logger.info(f"Saved watch progress for {user.username}: {current_time}s")
                return progress
        except (Anime.DoesNotExist, Episode.DoesNotExist) as e:
            logger.error(f"Save watch progress error: {e}")
            return None

    def get_watch_progress(self, user, anime_id: int) -> List[Dict]:
        try:
            progress_list = WatchProgress.objects.filter(user=user, anime_id=anime_id).select_related("episode", "translation").order_by("episode__number")
            return [
                {
                    "episode_id": p.episode.id,
                    "episode_number": p.episode.number,
                    "current_time": p.current_time,
                    "duration": p.duration,
                    "is_completed": p.is_completed,
                    "translation_name": p.translation.name if p.translation else None,
                    "last_watched": p.last_watched,
                }
                for p in progress_list
            ]
        except Exception as e:
            logger.error(f"Get watch progress error: {e}")
            return []

    def check_for_updates(self, anime: Anime) -> List[Dict]:
        updates = []
        try:
            if anime.shikimori_id:
                fresh_data = self.get_anime_by_id(anime.shikimori_id, "shikimori")
                if fresh_data:
                    if fresh_data.get("status") != anime.status:
                        updates.append({
                            "type": "status_change",
                            "description": f"Статус изменен с {anime.status} на {fresh_data['status']}",
                            "old_value": anime.status,
                            "new_value": fresh_data["status"],
                        })
                    if fresh_data.get("episodes") and fresh_data["episodes"] != anime.episodes:
                        updates.append({
                            "type": "new_episode",
                            "description": f"Количество эпизодов: {anime.episodes} → {fresh_data['episodes']}",
                            "old_value": anime.episodes,
                            "new_value": fresh_data["episodes"],
                        })
                    if fresh_data.get("score") and fresh_data["score"] != anime.score:
                        updates.append({
                            "type": "info_update",
                            "description": f"Рейтинг обновлен: {anime.score} → {fresh_data['score']}",
                            "old_value": anime.score,
                            "new_value": fresh_data["score"],
                        })
        except Exception as e:
            logger.error(f"Check for updates error: {e}")
        return updates

    def save_updates(self, anime: Anime, updates: List[Dict]):
        for update_data in updates:
            AnimeUpdate.objects.create(
                anime=anime,
                update_type=update_data["type"],
                description=update_data["description"],
            )
        if updates:
            logger.info(f"Saved {len(updates)} updates for {anime.title_ru}")

    def get_recent_updates(self, limit: int = 50) -> List[Dict]:
        recent_updates = AnimeUpdate.objects.select_related("anime").filter(anime__title_ru__regex=r"[а-яёА-ЯЁ]").order_by("-created_at")[:limit]
        return [
            {
                "id": update.id,
                "anime_title": update.anime.title_ru,
                "anime_id": update.anime.id,
                "update_type": update.get_update_type_display(),
                "description": update.description,
                "episode_number": update.episode_number,
                "created_at": update.created_at,
            }
            for update in recent_updates
        ]

    def import_anime_to_db(self, anime_data: Dict, source: str = "kodik") -> Anime:
        try:
            with transaction.atomic():
                title_en = anime_data.get("title_en") or ""
                anime, created = Anime.objects.update_or_create(
                    shikimori_id=anime_data.get("shikimori_id") or anime_data.get("id"),
                    defaults={
                        "title_ru": anime_data.get("title_ru", "") or "Без названия",
                        "title_en": title_en,
                        "title_jp": anime_data.get("title_jp", "") or "",
                        "description": anime_data.get("description", ""),
                        "year": anime_data.get("year"),
                        "status": anime_data.get("status", "finished"),
                        "kind": anime_data.get("kind", "tv"),
                        "episodes": anime_data.get("episodes"),
                        "episode_duration": anime_data.get("episode_duration"),
                        "total_duration": anime_data.get("total_duration"),
                        "score": anime_data.get("score"),
                        "poster_url": anime_data.get("poster_url", ""),
                        "movies": anime_data.get("movies", []),
                        "ovas": anime_data.get("ovas", []),
                        "movie_count": anime_data.get("movie_count", 0),
                        "ova_count": anime_data.get("ova_count", 0),
                        "total_items": anime_data.get("total_items", 1),
                        "data_source": source,
                    },
                )
                desired_total = (
                    anime_data.get("progress_total")
                    or anime_data.get("episodes")
                    or 0
                )
                if desired_total > (anime.progress_total or 0):
                    anime.progress_total = desired_total
                    anime.save(update_fields=["progress_total"])
                if anime_data.get("poster_url") and not anime.poster:
                    self._download_anime_poster(anime, anime_data["poster_url"])
                self._update_genres(anime, anime_data.get("genres", []))
                self._update_studios(anime, anime_data.get("studios", []))
                self._update_video_sources(anime, anime_data, source)
                logger.info(f"{'Создано' if created else 'Обновлено'} аниме: {anime.title_ru}")
                return anime
        except Exception as e:
            logger.error(f"Import anime error: {e}")
            raise

    def import_single_anime(self, shikimori_id: int) -> Optional[Anime]:
        try:
            raw_data = self.get_anime_by_id(shikimori_id, "shikimori")
            if not raw_data:
                return None
            normalized = self._normalize_shikimori_data(raw_data)
            return self._save_anime_to_db(normalized)
        except Exception as e:
            logger.error(f"Import single anime error: {e}")
            return None

    def import_by_known_ids(self, anime_ids: List[int]) -> List[Anime]:
        imported = []
        for idx, anime_id in enumerate(anime_ids):
            if Anime.objects.filter(shikimori_id=anime_id).exists():
                continue
            try:
                anime = self.import_single_anime(anime_id)
                if anime:
                    imported.append(anime)
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Import by known ids error ID {anime_id}: {e}")
                time.sleep(1)
        return imported

    def import_all_shikimori(self, target: int = 50000, method: str = "mixed", workers: int = 4) -> List[Anime]:
        logger.debug(f"Loading {target} anime by {method}...")
        if method == "bulk":
            return self._bulk_import(target)
        elif method == "id_range":
            return self._id_range_import(target, workers)
        elif method == "mixed":
            return self._mixed_import(target, workers)
        elif method == "complete":
            return self._complete_import(target, workers)
        return []

    def _bulk_import(self, target: int) -> List[Anime]:
        logger.debug("Bulk import via Shikimori API...")
        imported = []
        page = 1
        per_page = 50
        while len(imported) < target:
            try:
                params = {"page": page, "limit": per_page, "order": "id"}
                data = external_anime_api.get_animes(params)
                page_data = data if isinstance(data, list) else []
                if not page_data:
                    break
                for anime_data in page_data:
                    if len(imported) >= target:
                        break
                    try:
                        normalized = self._normalize_shikimori_data(anime_data)
                        anime = self._save_anime_to_db(normalized)
                        if anime:
                            imported.append(anime)
                    except Exception as e:
                        logger.error(f"Bulk import item error: {e}")
                        continue
                page += 1
                time.sleep(1)
            except Exception as e:
                logger.error(f"Bulk import page error: {e}")
                break
        return imported[:target]

    def _id_range_import(self, target: int, workers: int = 4) -> List[Anime]:
        max_id = 200000
        chunk_size = max(1, max_id // workers)
        futures = []
        imported = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for i in range(workers):
                start_id = i * chunk_size + 1
                end_id = min((i + 1) * chunk_size, max_id)
                future = executor.submit(self._process_id_range, start_id, end_id, target // workers)
                futures.append(future)
            for future in as_completed(futures):
                try:
                    imported.extend(future.result())
                except Exception as e:
                    logger.error(f"ID range import thread error: {e}")
        return imported[:target]

    def _mixed_import(self, target: int, workers: int = 4) -> List[Anime]:
        imported = []
        bulk_target = target // 3
        if bulk_target > 0:
            imported.extend(self._bulk_import(bulk_target))
        remaining = target - len(imported)
        if remaining > 0:
            imported.extend(self._id_range_import(remaining, workers))
        return imported[:target]

    def _complete_import(self, target: int, workers: int = 4) -> List[Anime]:
        imported = []
        current_id = 1
        batch_size = 1000
        max_id = 300000
        while len(imported) < target and current_id < max_id:
            end_id = min(current_id + batch_size - 1, max_id)
            with ThreadPoolExecutor(max_workers=workers) as executor:
                chunk_size = batch_size // workers
                futures = []
                for i in range(workers):
                    chunk_start = current_id + i * chunk_size
                    chunk_end = min(chunk_start + chunk_size - 1, end_id)
                    if chunk_start <= end_id:
                        future = executor.submit(self._process_id_range, chunk_start, chunk_end, batch_size // workers)
                        futures.append(future)
                for future in as_completed(futures):
                    try:
                        imported.extend(future.result())
                    except Exception as e:
                        logger.error(f"Complete import batch error: {e}")
            current_id = end_id + 1
            time.sleep(1)
            if len(imported) >= target:
                break
        return imported[:target]

    def _process_id_range(self, start_id: int, end_id: int, limit: int) -> List[Anime]:
        imported = []
        for current_id in range(start_id, start_id + limit):
            try:
                anime_data = self.get_anime_by_id(current_id, "shikimori")
                if anime_data:
                    normalized = self._normalize_shikimori_data(anime_data)
                    anime = self._save_anime_to_db(normalized)
                    if anime:
                        imported.append(anime)
            except Exception as e:
                if "404" not in str(e):
                    logger.error(f"Process id range error ID {current_id}: {e}")
            time.sleep(0.1)
        return imported

    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self.search_anime(query, limit)

    def get_by_shikimori_id(self, shikimori_id: int, with_episodes: bool = True) -> Optional[Dict[str, Any]]:
        cache_key = f"anime:shikimori:{shikimori_id}:episodes={with_episodes}"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached
        params = {"shikimori_id": str(shikimori_id), "with_material_data": True, "with_seasons": True, "limit": 1}
        if with_episodes:
            params["with_episodes"] = True
        data = external_anime_api.search(**params)
        results = data.get("results", [])
        result = results[0] if results else None
        if result:
            safe_cache_set(f"anime:shikimori:{shikimori_id}:episodes={with_episodes}", result, timeout=3600)
        return result

    def get_by_kodik_id(self, kodik_id: str, with_episodes: bool = True) -> Optional[Dict[str, Any]]:
        cache_key = f"anime:kodik:{kodik_id}:episodes={with_episodes}"
        cached = safe_cache_get(cache_key)
        if cached is not None:
            return cached
        params = {"id": kodik_id, "with_material_data": True, "with_seasons": True, "limit": 1}
        if with_episodes:
            params["with_episodes"] = True
        data = external_anime_api.search(**params)
        results = data.get("results", [])
        result = results[0] if results else None
        if result:
            safe_cache_set(f"anime:kodik:{kodik_id}:episodes={with_episodes}", result, timeout=3600)
        return result

    def import_anime(self, kodik_data: Dict[str, Any], update_existing: bool = False, download_posters: bool = False, skip_video_sync: bool = False, skip_shikimori: bool = False, track_availability: bool = True) -> Tuple[Anime, bool]:
        material_data = kodik_data.get("material_data") or {}
        title_ru = material_data.get("anime_title") or material_data.get("title") or kodik_data.get("title", "")
        title_en = material_data.get("title_en") or kodik_data.get("title_orig", "")
        title_jp = ""
        other_titles_jp = material_data.get("other_titles_jp", [])
        if other_titles_jp and isinstance(other_titles_jp, list):
            title_jp = other_titles_jp[0] if other_titles_jp else ""

        shikimori_id = kodik_data.get("shikimori_id")
        if shikimori_id is not None:
            try:
                shikimori_id = int(shikimori_id)
            except (ValueError, TypeError):
                shikimori_id = None

        episodes_count = self._get_episodes_count_correct(kodik_data, allow_shikimori=not skip_shikimori)
        
        episode_duration = None
        if shikimori_id and not skip_shikimori:
            episode_duration = self._get_episode_duration_from_shikimori(shikimori_id)
        elif skip_shikimori:
            try:
                episode_duration = int(material_data.get("duration") or 0) or None
            except (TypeError, ValueError):
                episode_duration = None
        
        kind = self._map_kind(material_data.get("anime_kind") or kodik_data.get("type"))
        
        if episode_duration is None:
            episode_duration = 100 if kind == "movie" else 25
        
        total_duration = episodes_count * episode_duration if episodes_count and episode_duration else None
        
        from .release_year import release_year, premiere_date
        year = release_year(kodik_data)
        exact_release_date = premiere_date(kodik_data)

        score = material_data.get("shikimori_rating") or material_data.get("kinopoisk_rating") or 0.0
        if score:
            try:
                score = float(score)
            except (ValueError, TypeError):
                score = 0.0

        status = self._map_status(material_data.get("anime_status"))

        genres: List[str] = []
        raw_genres = material_data.get("anime_genres") or material_data.get("genres") or []
        if isinstance(raw_genres, list):
            for g in raw_genres:
                if isinstance(g, dict) and "name" in g:
                    genres.append(g["name"])
                elif isinstance(g, str):
                    genres.append(g)
        elif isinstance(raw_genres, str):
            genres = [g.strip() for g in raw_genres.split(",") if g.strip()]

        studios: List[str] = []
        raw_studios = material_data.get("anime_studios") or []
        if isinstance(raw_studios, list):
            for s in raw_studios:
                if isinstance(s, dict) and "name" in s:
                    studios.append(s["name"])
                elif isinstance(s, str):
                    studios.append(s)
        elif isinstance(raw_studios, str):
            studios = [s.strip() for s in raw_studios.split(",") if s.strip()]

        poster_url = material_data.get("anime_poster_url") or material_data.get("poster_url") or ""
        description = material_data.get("anime_description") or material_data.get("description") or ""
        kodik_id = kodik_data.get("id", "")
        kodik_link = kodik_data.get("link", "")
        quality = kodik_data.get("quality", "")
        screenshots = kodik_data.get("screenshots") or []
        seasons = kodik_data.get("seasons") or {}
        last_season = kodik_data.get("last_season")
        last_episode = kodik_data.get("last_episode")
        translation = kodik_data.get("translation") or {}
        translations = [translation.get("title")] if translation.get("title") else []

        defaults = {
            "title_ru": title_ru[:255] if title_ru else "",
            "title_en": title_en[:255] if title_en else "",
            "title_jp": title_jp[:255] if title_jp else "",
            "description": description[:5000] if description else "",
            "year": year,
            "release_date": exact_release_date,
            "release_date_string": exact_release_date.isoformat() if exact_release_date else "",
            "status": status,
            "kind": kind,
            "episodes": episodes_count,
            "episode_duration": episode_duration,
            "total_duration": total_duration,
            "score": score,
            "poster_url": poster_url[:500] if poster_url else "",
            "genres": genres,
            "studios": studios,
            "kodik_link": kodik_link[:500] if kodik_link else "",
            "kodik_id": kodik_id[:255] if kodik_id else "",
            "quality": quality[:20] if quality else "",
            "screenshots": screenshots,
            "seasons": seasons,
            "last_season": last_season,
            "last_episode": last_episode,
            "translations": translations,
            "data_source": "kodik",
            "is_available": True,
            "movies": [],
            "ovas": [],
            "movie_count": 0,
            "ova_count": 0,
            "total_items": 1,
            "raw_kodik_data": kodik_data,
        }

        if shikimori_id is not None:
            try:
                with transaction.atomic():
                    anime, created = Anime.objects.select_for_update().update_or_create(
                        shikimori_id=shikimori_id,
                        defaults=defaults
                    )
            except IntegrityError:
                with transaction.atomic():
                    anime = Anime.objects.get(shikimori_id=shikimori_id)
                    created = False
                    for key, value in defaults.items():
                        setattr(anime, key, value)
                    anime.save()
        else:
            kodik_id_val = kodik_data.get("id", "")
            if kodik_id_val:
                with transaction.atomic():
                    anime, created = Anime.objects.select_for_update().update_or_create(
                        kodik_id=kodik_id_val,
                        defaults={**defaults, "shikimori_id": None}
                    )
            else:
                with transaction.atomic():
                    anime, created = Anime.objects.update_or_create(
                        shikimori_id=None,
                        defaults=defaults
                    )

        best_total = max(anime.progress_total or 0, episodes_count or 0)
        if best_total != (anime.progress_total or 0):
            anime.progress_total = best_total
            anime.save(update_fields=["progress_total"])

        if created or update_existing:
            if not skip_video_sync:
                self._sync_video_data(anime, kodik_data)

        if download_posters and poster_url and not anime.poster:
            try:
                saved_path = self.image_service.download_poster_safe(poster_url, anime.id, anime.title_ru or str(anime.id))
                if saved_path:
                    anime.poster.name = saved_path
                    anime.save(update_fields=["poster", "updated_at"])
            except Exception as e:
                logger.warning(f"Poster download failed for anime {anime.id}: {e}")

        if track_availability:
            from .episode_availability import record_availability
            record_availability(anime, kodik_data)
        return anime, created

    def bulk_import(self, limit: Optional[int] = None, update_existing: bool = False, batch_size: int = 100, download_posters: bool = False) -> Dict[str, int]:
        params = {"limit": 100, "types": "anime,anime-serial", "with_material_data": True, "with_seasons": True, "with_episodes": True}
        imported = 0
        created_count = 0
        updated_count = 0
        skipped = 0
        errors = 0

        existing_shikimori = set(Anime.objects.filter(shikimori_id__isnull=False).values_list("shikimori_id", flat=True))
        existing_kodik = set(Anime.objects.filter(kodik_id__isnull=False).values_list("kodik_id", flat=True))

        next_page = None
        while imported < (limit or 999999999):
            try:
                page_params = dict(params)
                if next_page:
                    page_params["next_page"] = next_page
                data = external_anime_api.list_materials(**page_params)
                results = data.get("results", [])
                if not results:
                    break
                for item in results:
                    if limit and imported >= limit:
                        break
                    try:
                        shikimori_id = item.get("shikimori_id")
                        if not shikimori_id:
                            skipped += 1
                            continue
                        try:
                            shikimori_id = int(shikimori_id)
                        except (ValueError, TypeError):
                            skipped += 1
                            continue
                        kodik_id = item.get("id", "")
                        is_existing = shikimori_id in existing_shikimori or (kodik_id and kodik_id in existing_kodik)
                        if is_existing and not update_existing:
                            skipped += 1
                            continue
                        _, created = self.import_anime(item, update_existing=update_existing, download_posters=download_posters)
                        if created:
                            created_count += 1
                            existing_shikimori.add(shikimori_id)
                        elif is_existing:
                            updated_count += 1
                        if kodik_id:
                            existing_kodik.add(kodik_id)
                        imported += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"Bulk import item error: {e}")
                        continue
                next_page = data.get("next_page")
                if not next_page:
                    break
            except Exception as e:
                logger.error(f"Bulk import page error: {e}")
                break
        return {"imported": imported, "created": created_count, "updated": updated_count, "skipped": skipped, "errors": errors}

    def get_calendar(self, censored: bool = True, start=None, end=None) -> List[Dict[str, Any]]:
        from apps.anime.application.calendar_history import read_calendar
        from apps.anime.infrastructure.models.read_models import CalendarRelease, CalendarSnapshot
        if CalendarRelease.objects.exists():
            return read_calendar(start, end)
        snapshot = CalendarSnapshot.objects.filter(key='kodik').first()
        return snapshot.entries if snapshot else []

    def get_random_anime_ids(self, count: int = 50) -> List[int]:
        try:
            params = {"page": 1, "limit": count, "order": "random"}
            data = external_anime_api.get_animes(params)
            anime_list = data if isinstance(data, list) else []
            return [a.get("id") for a in anime_list if a.get("id")]
        except Exception as e:
            logger.error(f"Get random anime ids error: {e}")
            return []

    def health_check(self) -> Dict[str, bool]:
        status = {}
        try:
            external_anime_api.get_animes({"page": 1, "limit": 1})
            status["shikimori"] = True
        except Exception:
            status["shikimori"] = False
        try:
            external_anime_api.list_materials(limit=1)
            status["kodik"] = True
        except Exception:
            status["kodik"] = False
        return status

    def _download_anime_poster(self, anime: Anime, poster_url: str):
        try:
            poster_path = self.image_service.download_poster_safe(poster_url, anime.id, anime.title_ru)
            if poster_path:
                if anime.poster:
                    self.image_service.cleanup_old_poster(anime.poster.name)
                anime.poster.name = poster_path
                anime.save(update_fields=["poster"])
                logger.info(f"Poster downloaded for {anime.title_ru}")
            else:
                logger.warning(f"Poster download failed for {anime.title_ru}")
        except Exception as e:
            logger.error(f"Poster download error for {anime.title_ru}: {e}")

    def _update_genres(self, anime: Anime, genres_data: List[Dict]):
        try:
            genre_names = []
            if isinstance(genres_data, list):
                for genre in genres_data:
                    if isinstance(genre, dict):
                        name = genre.get("name") or genre.get("title") or genre.get("russian")
                        if name:
                            genre_names.append(name)
                    elif isinstance(genre, str):
                        genre_names.append(genre)
            unique_genres = list(set(genre_names))
            anime.genres = unique_genres
            anime.save(update_fields=["genres"])
        except Exception as e:
            logger.warning(f"Update genres error for {anime.title_ru}: {e}")

    def _update_studios(self, anime: Anime, studios_data: List[Dict]):
        try:
            studio_names = []
            if isinstance(studios_data, list):
                for studio in studios_data:
                    if isinstance(studio, dict):
                        name = studio.get("name") or studio.get("title") or studio.get("russian")
                        if name:
                            studio_names.append(name)
                    elif isinstance(studio, str):
                        studio_names.append(studio)
            unique_studios = list(set(studio_names))
            anime.studios = unique_studios
            anime.save(update_fields=["studios"])
        except Exception as e:
            logger.warning(f"Update studios error for {anime.title_ru}: {e}")

    def _update_video_sources(self, anime: Anime, anime_data: Dict, source: str):
        try:
            shikimori_id = anime_data.get("shikimori_id")
            if shikimori_id and source != "kodik":
                self._update_episodes(anime, shikimori_id, source)
            if anime_data.get("video_sources"):
                self._save_video_sources(anime, anime_data["video_sources"])
        except Exception as e:
            logger.warning(f"Update video sources error for {anime.title_ru}: {e}")

    def _update_episodes(self, anime: Anime, shikimori_id: str, source: str):
        try:
            if source == "kodik":
                return
            episodes_data = self.get_episodes_info(str(shikimori_id), source)
            for ep_data in episodes_data:
                Episode.objects.update_or_create(
                    anime=anime,
                    number=int(ep_data["num"]),
                    defaults={"title": ep_data.get("title", ""), "air_date": self._parse_date(ep_data.get("date"))},
                )
        except Exception as e:
            logger.debug(f"Update episodes error for {anime.title_ru}: {e}")

    def _parse_date(self, date_str: str) -> Optional[object]:
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str.split()[0], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            return None

    def get_episodes_info(self, shikimori_id: str, source: str) -> List[Dict]:
        return []

    def _save_video_sources(self, anime: Anime, video_sources: List[Dict]):
        pass

    def _save_anime_to_db(self, anime_data: dict) -> Optional[Anime]:
        try:
            with transaction.atomic():
                anime, created = Anime.objects.update_or_create(
                    shikimori_id=anime_data["id"],
                    defaults={
                        "title_ru": anime_data.get("title_ru", ""),
                        "title_en": anime_data.get("title_en", ""),
                        "title_jp": anime_data.get("title_jp", ""),
                        "description": anime_data.get("description", ""),
                        "year": anime_data.get("year"),
                        "status": anime_data.get("status", "finished"),
                        "episodes": anime_data.get("episodes"),
                        "episode_duration": anime_data.get("episode_duration"),
                        "total_duration": anime_data.get("total_duration"),
                        "score": anime_data.get("score"),
                        "poster_url": anime_data.get("poster_url", ""),
                        "screenshots": anime_data.get("screenshots"),
                        "data_source": "shikimori",
                    },
                )
                desired_total = anime_data.get("episodes") or 0
                if desired_total > (anime.progress_total or 0):
                    anime.progress_total = desired_total
                    anime.save(update_fields=["progress_total"])
                if anime_data.get("genres"):
                    for genre_data in anime_data["genres"]:
                        genre_name = genre_data.get("name")
                        if genre_name:
                            genre, _ = Genre.objects.get_or_create(name=genre_name, defaults={"slug": genre_name.lower().replace(" ", "-")})
                            anime.genres.add(genre)
                if anime_data.get("studios"):
                    for studio_name in anime_data["studios"]:
                        if studio_name:
                            studio, _ = Studio.objects.get_or_create(name=studio_name, defaults={"slug": studio_name.lower().replace(" ", "-")})
                            anime.studios.add(studio)
                logger.debug(f"{'Создано' if created else 'Обновлено'}: {anime.title_ru}")
                return anime
        except Exception as e:
            logger.error(f"Save anime to db error: {e}")
            return None

    def _sync_video_data(self, anime: Anime, kodik_data: Dict[str, Any]) -> None:
        try:
            seasons = kodik_data.get("seasons") or {}
            translation = kodik_data.get("translation") or {}
            translation_name = translation.get("title", "")
            translation_type = translation.get("type", "voice")
            translation_id = translation.get("id")
            kodik_link = kodik_data.get("link", "")
            quality = kodik_data.get("quality", "720p")

            with transaction.atomic():
                source, _ = VideoSource.objects.update_or_create(
                    anime=anime,
                    source="kodik",
                    defaults={
                        "external_id": kodik_data.get("id", ""),
                        "title": kodik_data.get("title", ""),
                        "description": kodik_data.get("title_orig", ""),
                        "quality": (quality.replace("p", "") if quality else "720")[:10],
                        "video_format": "mp4",
                        "is_available": True,
                        "is_active": True,
                    },
                )

                if translation_name:
                    Translation.objects.update_or_create(
                        anime=anime,
                        name=translation_name,
                        defaults={
                            "video_source": source,
                            "translation_type": translation_type,
                            "studio_name": "",
                            "external_id": str(translation_id) if translation_id is not None else "",
                            "status": "active",
                            "is_complete": True,
                            "episodes_count": anime.episodes or 0,
                        },
                    )

                episode_numbers = set()
                for season_key, season_data in seasons.items():
                    episodes = ((season_data or {}).get("episodes") or {})
                    for ep_key in episodes.keys():
                        try:
                            episode_numbers.add(int(ep_key))
                        except (ValueError, TypeError):
                            continue

                if not episode_numbers:
                    episode_numbers = set(range(1, (anime.episodes or 1) + 1))

                existing_episodes = {e.number: e for e in Episode.objects.filter(anime=anime)}
                to_create = []
                for number in sorted(episode_numbers):
                    to_create.append(Episode(anime=anime, number=number, video_source=source, title="", title_en="", description=""))
                if to_create:
                    upsert_kwargs = {"update_conflicts": True, "update_fields": ["video_source", "title", "title_en", "description"]}
                    if connection.features.supports_update_conflicts_with_target:
                        upsert_kwargs["unique_fields"] = ["anime", "number"]
                    Episode.objects.bulk_create(to_create, **upsert_kwargs)

                if existing_episodes:
                    Episode.objects.filter(anime=anime, number__in=existing_episodes.keys()).exclude(number__in=episode_numbers).delete()
        except Exception as e:
            logger.warning(f"Sync video data error for anime {anime.id}: {e}")

    def _get_episodes_count_correct(self, item: Dict[str, Any], allow_shikimori: bool = True) -> Optional[int]:
        material_data = item.get("material_data") or {}
        episodes_total = material_data.get("episodes_total")
        if episodes_total:
            try:
                return int(episodes_total)
            except (TypeError, ValueError):
                pass

        shikimori_id = item.get("shikimori_id")
        if shikimori_id is not None:
            try:
                shikimori_id = int(shikimori_id)
            except (TypeError, ValueError):
                shikimori_id = None
        if shikimori_id and allow_shikimori:
            shikimori_episodes = self._get_episodes_from_shikimori(shikimori_id)
            if shikimori_episodes:
                return shikimori_episodes

        episodes_count = item.get("episodes_count")
        if episodes_count:
            try:
                return int(episodes_count)
            except (TypeError, ValueError):
                pass

        last_episode = item.get("last_episode")
        if last_episode:
            try:
                return int(last_episode)
            except (TypeError, ValueError):
                pass

        episodes_aired = material_data.get("episodes_aired")
        if episodes_aired:
            try:
                return int(episodes_aired)
            except (TypeError, ValueError):
                pass
        return None

    def _get_episodes_from_shikimori(self, shikimori_id: int) -> Optional[int]:
        try:
            anime = external_anime_api.get_anime_details(shikimori_id)
            if not anime:
                return None
            episodes = anime.get("episodes")
            if episodes is None or episodes == 0:
                episodes_aired = anime.get("episodes_aired")
                if episodes_aired:
                    return int(episodes_aired)
            if episodes:
                return int(episodes)
        except Exception:
            pass
        return None

    def _get_episode_duration_from_shikimori(self, shikimori_id: int) -> Optional[int]:
        try:
            anime = external_anime_api.get_anime_details(shikimori_id)
            if not anime:
                return None
            duration = anime.get("duration")
            if duration:
                return int(duration)
        except Exception:
            pass
        return None

    def _map_status(self, kodik_status: Optional[str]) -> str:
        mapping = {"ongoing": "ongoing", "released": "released", "anons": "announced", "canceled": "canceled", "on_hold": "on_hold"}
        return mapping.get(kodik_status, "finished") if kodik_status else "finished"

    def _map_kind(self, kodik_type: Optional[str]) -> str:
        mapping = {
            "anime": "tv", "anime-serial": "tv", "foreign-movie": "movie", "russian-movie": "movie",
            "soviet-cartoon": "movie", "foreign-cartoon": "movie", "russian-cartoon": "movie",
            "ova": "ova", "ona": "ona", "special": "special", "music": "music",
            "tv": "tv", "tv_13": "tv", "tv_24": "tv", "tv_48": "tv", "movie": "movie",
        }
        return mapping.get(kodik_type, "tv") if kodik_type else "tv"

    @staticmethod
    def _parse_year(aired_on: Any) -> Optional[int]:
        if not isinstance(aired_on, str):
            return None
        aired_on = aired_on.strip()
        if not aired_on:
            return None
        try:
            year = int(aired_on.split("-")[0])
        except (TypeError, ValueError):
            return None
        if year < 1900 or year > 2100:
            return None
        return year

    def _normalize_shikimori_data(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        episodes = raw.get("episodes")
        duration = raw.get("duration")
        episode_duration = int(duration) if duration else None
        total_duration = episodes * episode_duration if episodes and episode_duration else None
        
        return {
            "id": raw.get("id"),
            "title_ru": raw.get("russian") or raw.get("name"),
            "title_en": raw.get("english") or raw.get("name"),
            "title_jp": raw.get("japanese"),
            "description": raw.get("description", ""),
            "poster_url": raw.get("image", {}).get("original") or raw.get("poster_url", ""),
            "year": self._parse_year(raw.get("aired_on")),
            "status": self._map_status(raw.get("status")),
            "episodes": episodes,
            "episode_duration": episode_duration,
            "total_duration": total_duration,
            "score": raw.get("score"),
            "genres": [{"name": g.get("russian") or g.get("name")} for g in raw.get("genres", []) if isinstance(g, dict)],
            "studios": [s.get("name") for s in raw.get("studios", []) if isinstance(s, dict)],
            "screenshots": [{"url": s.get("original")} for s in raw.get("screenshots", []) if isinstance(s, dict)],
            "raw": raw,
        }


anime_service = AnimeService()
