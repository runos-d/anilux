from __future__ import annotations

from typing import Any, Dict, List, Optional

from apps.anime.infrastructure.api.kodik import KodikAPI, kodik_api
from apps.anime.infrastructure.api.shikimori import ShikimoriAPI, shikimori_api


class ExternalAnimeAPI:
    def __init__(
        self,
        kodik: Optional[KodikAPI] = None,
        shikimori: Optional[ShikimoriAPI] = None,
    ):
        self.kodik = kodik or kodik_api
        self.shikimori = shikimori or shikimori_api

    def search_by_shikimori_id(self, shikimori_id: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        params = {
            "shikimori_id": shikimori_id,
            "with_material_data": True,
            "limit": limit,
        }
        data = self.kodik.search(**params)
        results = data.get("results", [])
        return results[0] if results else None

    def search_by_kodik_id(self, kodik_id: str) -> Optional[Dict[str, Any]]:
        params = {
            "id": kodik_id,
            "with_material_data": True,
            "limit": 1,
        }
        data = self.kodik.search(**params)
        results = data.get("results", [])
        return results[0] if results else None

    def get_translations(self, shikimori_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        params = {
            "shikimori_id": shikimori_id,
            "with_episodes_data": False,
            "limit": limit,
        }
        data = self.kodik.search(**params)
        results = data.get("results", [])
        translations_map = {}
        for result in results:
            translation = result.get("translation", {})
            if not translation:
                continue
            translation_id = translation.get("id")
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
                    "logo": None,
                }
            t = translations_map[translation_id]
            episodes = result.get("episodes_count") or 0
            if episodes > t["episodes_done"]:
                t["episodes_done"] = episodes
        translations = list(translations_map.values())
        translations.sort(key=lambda x: x["episodes_done"], reverse=True)
        return translations

    def get_episode_url(self, shikimori_id: str, episode: int, season: str, translation_id: Optional[str] = None) -> Optional[str]:
        params = {
            "with_material_data": False,
            "with_seasons": True,
            "with_episodes": True,
            "limit": 100,
        }
        if shikimori_id:
            params["shikimori_id"] = shikimori_id
        if translation_id:
            params["translation_id"] = translation_id

        data = self.kodik.search(**params)
        season_key = str(season)
        ep_key = str(episode)
        for res in data.get("results", []):
            if translation_id:
                tid = (res.get("translation") or {}).get("id")
                if str(tid) != str(translation_id):
                    continue
            s_data = ((res.get("seasons") or {}).get(season_key)) or {}
            ep_data = s_data.get("episodes") or {}
            ep_url = ep_data.get(ep_key) or ep_data.get(
                int(ep_key) if ep_key.isdigit() else ep_key
            )
            if ep_url:
                return ep_url.strip()
        return None

    def get_filters(self) -> Dict[str, Any]:
        genres = self.kodik.get_genres(
            types="anime-serial,anime",
            genres_type="shikimori",
            sort="title",
        ).get("results", [])
        years = self.kodik.get_years(
            types="anime-serial,anime",
            sort="year",
            order="desc",
        ).get("results", [])
        studios = self.kodik.get_genres(
            types="anime-serial,anime",
            sort="title",
        ).get("results", [])
        translations = self.kodik.get_translations(
            types="anime-serial,anime",
            sort="title",
        ).get("results", [])
        return {
            "genres": genres,
            "years": years,
            "studios": studios,
            "translations": translations,
        }

    def get_kodik_filters(self) -> Dict[str, Any]:
        return self.kodik.get_filters()

    def get_franchise(self, anime_id: int) -> Optional[Dict[str, Any]]:
        return self.shikimori.get_franchise(anime_id)

    def get_franchise_nodes(self, anime_id: int) -> List[Dict[str, Any]]:
        data = self.shikimori.get_franchise(anime_id)
        if not data:
            return []
        return data.get("nodes", []) or []

    def get_franchise_links(self, anime_id: int) -> List[Dict[str, Any]]:
        data = self.shikimori.get_franchise(anime_id)
        if not data:
            return []
        return data.get("links", []) or []

    def get_anime_details(self, anime_id: int) -> Optional[Dict[str, Any]]:
        return self.shikimori.get_anime(anime_id)

    def get_calendar(self, censored: bool = True) -> List[Dict[str, Any]]:
        return self.shikimori.get_calendar(censored=censored)

    def get_years(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_years(**kwargs)

    def get_genres(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_genres(**kwargs)

    def get_countries(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_countries(**kwargs)

    def get_qualities(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_qualities(**kwargs)

    def get_translations_list(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_translations(**kwargs)

    def get_translations_v1(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.get_translations_v1(**kwargs)

    def list_materials(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.list_materials(**kwargs)

    def kodik_request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.kodik._get(path, params)

    def search(self, **kwargs: Any) -> Dict[str, Any]:
        return self.kodik.search(**kwargs)

    def get_animes(self, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        return self.shikimori.list_animes(params)

    def get_anime_by_id(self, anime_id: int) -> Optional[Dict[str, Any]]:
        return self.shikimori.get_anime(anime_id)

    def get_genres_shikimori(self) -> List[Dict[str, Any]]:
        return self.shikimori.get_genres()

external_anime_api = ExternalAnimeAPI()
