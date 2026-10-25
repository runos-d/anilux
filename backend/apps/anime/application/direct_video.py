import asyncio
import aiohttp
from typing import Any
import logging



logger = logging.getLogger(__name__)
class DirectVideoService:
    @staticmethod
    async def get_anime_episode_url(
        anime_id: int,
        episode: int,
        season: int = 1,
        translation_id: str | None = None,
        quality: str = "720"
    ) -> dict[str, Any] | None:
        try:
            from anicli_api.player.kodik import Kodik
            from anicli_api.player.aniboom import AniBoom
            
            
            
            from apps.anime.application.anime_service import anime_service

            user_ip = "1.1.1.1"  
            m3u8_url = await asyncio.to_thread(
                anime_service.get_anime_m3u8,
                anime_id=anime_id,
                episode=episode,
                season=season,
                translation_id=translation_id,
                user_ip=user_ip,
                quality=quality
            )
            
            if not m3u8_url:
                return None
            
            direct_url = await DirectVideoService._extract_direct_url(m3u8_url)
            
            if direct_url:
                return {
                    "url": direct_url,
                    "quality": quality,
                    "source": "kodik"
                }
            
            return {
                "url": m3u8_url,
                "quality": quality,
                "source": "kodik",
                "is_m3u8": True
            }
            
        except Exception as e:
            logger.info(f"[DirectVideoService] Error: {e}")
            return None
    
    @staticmethod
    async def _extract_direct_url(m3u8_url: str) -> str | None:
        try:
            if m3u8_url.endswith('.mp4'):
                return m3u8_url
            
            from anicli_api.player.kodik import Kodik
            
            if "kodik.cc" in m3u8_url or "kodikapi" in m3u8_url:
                direct_url = m3u8_url.replace('.m3u8', '.mp4')
                
                async with aiohttp.ClientSession() as session:
                    async with session.head(direct_url, allow_redirects=True) as resp:
                        if resp.status == 200:
                            return direct_url
                
                try:
                    parser = Kodik()
                except Exception:
                    pass
            
            return None
            
        except Exception as e:
            logger.info(f"[ExtractDirectURL] Error: {e}")
            return None
    




