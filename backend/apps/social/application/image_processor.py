import os
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
from django.core.files.base import ContentFile
import logging



logger = logging.getLogger(__name__)
def convert_to_webp(image_file, max_size=(1920, 1920), quality=85):
    try:
        img = Image.open(image_file)
        
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        output = BytesIO()
        img.save(output, format='WEBP', quality=quality, optimize=True)
        output.seek(0)
        
        if hasattr(image_file, 'name'):
            original_name = os.path.basename(image_file.name)
            name, _ = os.path.splitext(original_name)
            new_name = f"{name}.webp"
        else:
            new_name = "image.webp"
        
        webp_file = ContentFile(output.read(), name=new_name)
        
        return webp_file
        
    except Exception as e:
        logger.info(f"Error converting to WebP: {e}")
        return None


def process_image_field(instance, field_name, max_size=(1920, 1920), quality=85):
    try:
        image_file = getattr(instance, field_name)
        
        if not image_file:
            return False
        
        webp_file = convert_to_webp(image_file, max_size, quality)
        
        if webp_file:
            setattr(instance, field_name, webp_file)
            return True
        
        return False
        
    except Exception as e:
        logger.info(f"Error processing image field: {e}")
        return False


def get_webp_url(url):
    if not url:
        return url
    
    if url.endswith('.webp'):
        return url
    
    if url.endswith('.png'):
        return url[:-4] + '.webp'
    elif url.endswith('.jpg') or url.endswith('.jpeg'):
        return url[:-4] + '.webp'
    
    return url
