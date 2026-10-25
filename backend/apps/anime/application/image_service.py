import os
import requests
from urllib.parse import urlparse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging
from PIL import Image
from io import BytesIO

from apps.anime.application.poster_enhancement_service import PosterEnhancementService

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self.media_root = settings.MEDIA_ROOT
        self.poster_dir = 'posters'
        self.max_size = (800, 1200)
        self.quality = 95
        self.webp_quality = 93
        self.enhancement_service = PosterEnhancementService()  
        
    def download_poster(self, image_url: str, anime_id: int, title: str) -> str:
        if not image_url:
            logger.warning(f"Пустой URL изображения для аниме {title}")
            return None
            
        try:
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                logger.warning(f"Неизвестный тип контента: {content_type} для {image_url}")
                return None
            
            image_content = response.content
            filename = self._generate_filename(anime_id, title, response.headers.get('content-type'))
            file_path = os.path.join(self.poster_dir, filename)
            
            ext = '.jpg'
            if 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            
            temp_filename = f"temp_enhance_{anime_id}{ext}"
            temp_path = os.path.join(self.poster_dir, temp_filename)
            temp_abs = default_storage.path(temp_path)
            
            default_storage.save(temp_path, ContentFile(image_content))
            enhanced_abs = self.enhancement_service.enhance(temp_abs)
            default_storage.delete(temp_path)
            
            if enhanced_abs and os.path.exists(enhanced_abs):
                with open(enhanced_abs, 'rb') as f:
                    enhanced_content = f.read()
                os.remove(enhanced_abs)
                
                processed_image = self._process_image(enhanced_content)
                if processed_image:
                    default_storage.save(file_path, ContentFile(processed_image))
                    logger.info(f"Постер загружен и улучшен для {title}: {file_path}")
                    return file_path
                else:
                    logger.warning(f"Не удалось обработать улучшенное изображение для {title}")
            
            processed_image = self._process_image(image_content)
            if processed_image:
                default_storage.save(file_path, ContentFile(processed_image))
                logger.info(f"Постер загружен для {title}: {file_path}")
                return file_path
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Ошибка загрузки изображения {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Общая ошибка загрузки изображения для {title}: {e}")
            return None
    
    def _process_image(self, image_content: bytes) -> bytes:
        try:
            image = Image.open(BytesIO(image_content))
            
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            output = BytesIO()
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            image.save(output, format='WEBP', quality=self.webp_quality, optimize=True, method=6)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            return None
    
    def _generate_filename(self, anime_id: int, title: str, content_type: str) -> str:
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  
        
        return f"anime_{anime_id}_{safe_title}.webp"
    
    def download_poster_safe(self, image_url: str, anime_id: int, title: str) -> str:
        try:
            if not image_url:
                return None
            
            if image_url.startswith('/media/') or image_url.startswith('/static/'):
                return None
            
            return self.download_poster(image_url, anime_id, title)
            
        except Exception as e:
            logger.error(f"Ошибка безопасной загрузки постера для {title}: {e}")
            return None
    
    def cleanup_old_poster(self, old_poster_path: str):
        if old_poster_path:
            try:
                if default_storage.exists(old_poster_path):
                    default_storage.delete(old_poster_path)
                    logger.info(f"Удален старый постер: {old_poster_path}")
            except Exception as e:
                logger.error(f"Ошибка удаления постера {old_poster_path}: {e}")
    
    def get_poster_url(self, poster_path: str) -> str:
        if poster_path:
            if poster_path.startswith('/'):
                return poster_path
            return f"/media/{poster_path}"
        return None