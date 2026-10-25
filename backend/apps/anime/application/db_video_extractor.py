import json
import pymysql
from typing import Optional, Dict, Any
from django.conf import settings
import logging



logger = logging.getLogger(__name__)
ANILIBRIA_DB_CONFIG = getattr(settings, 'ANILIBRIA_DB_CONFIG', {
    'host': '85.121.4.196',
    'database': 'anisphere.org_db',
    'user': 'u333333',
    'password': 'iQ8zH0uM9k',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
})


def get_anime_video_links(anime_title: str, use_russian: bool = True) -> Optional[Dict[str, str]]:
    try:
        conn = pymysql.connect(**ANILIBRIA_DB_CONFIG)
        cursor = conn.cursor()
        
        if use_russian:
            cursor.execute("""
                SELECT download_links, title_ru, title_en 
                FROM anime_anime 
                WHERE title_ru = %s OR title_en = %s OR title_jp = %s
                LIMIT 1
            """, (anime_title, anime_title, anime_title))
        else:
            cursor.execute("""
                SELECT download_links, title_ru, title_en 
                FROM anime_anime 
                WHERE title_en = %s OR title_ru = %s
                LIMIT 1
            """, (anime_title, anime_title))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return None
        
        if not result.get('download_links'):
            return None
        
        links = json.loads(result['download_links'])
        
        return {
            '480': links.get('480'),
            '720': links.get('720'),
            '1080': links.get('1080'),
            'title_ru': result.get('title_ru'),
            'title_en': result.get('title_en'),
        }
    
    except Exception as e:
        logger.info(f"[DB_VIDEO_EXTRACTOR] Error: {e}")
        return None


def get_anime_video_links_by_id(anime_id: int) -> Optional[Dict[str, Any]]:
    from apps.anime.infrastructure.models.anime import Anime
    
    try:
        anime = Anime.objects.get(id=anime_id)
        
        if not anime.title_ru and not anime.title_en:
            return None
        
        if anime.title_ru:
            links = get_anime_video_links(anime.title_ru, use_russian=True)
            if links:
                return {
                    **links,
                    'anime_id': anime_id,
                    'shikimori_id': anime.shikimori_id,
                }
        
        if anime.title_en:
            links = get_anime_video_links(anime.title_en, use_russian=False)
            if links:
                return {
                    **links,
                    'anime_id': anime_id,
                    'shikimori_id': anime.shikimori_id,
                }
        
        return None
    
    except Anime.DoesNotExist:
        return None
    except Exception as e:
        logger.info(f"[DB_VIDEO_EXTRACTOR] Error by ID: {e}")
        return None


def get_best_quality_url(links: Dict[str, Optional[str]], preferred: str = '1080') -> Optional[str]:
    quality_order = ['1080', '720', '480']
    
    if preferred in quality_order:
        quality_order.remove(preferred)
        quality_order.insert(0, preferred)
    
    for quality in quality_order:
        url = links.get(quality)
        if url:
            return url
    
    return None
