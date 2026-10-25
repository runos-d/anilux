import os
import shutil
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from django.conf import settings
from django.core.files.base import ContentFile
import logging


logger = logging.getLogger(__name__)
FFMPEG_PATH = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FFPROBE_PATH = shutil.which("ffprobe") or "/usr/bin/ffprobe"


def check_requirements() -> Tuple[bool, bool]:
    yt_dlp_ok = False
    ffmpeg_ok = False
    
    try:
        result = subprocess.run(
            ['/usr/local/bin/yt-dlp', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        yt_dlp_ok = result.returncode == 0
    except Exception:
        pass
    
    try:
        result = subprocess.run(
            ['/usr/bin/ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        ffmpeg_ok = result.returncode == 0
    except Exception:
        pass
    
    return yt_dlp_ok, ffmpeg_ok


def take_screenshot(
    video_url: str,
    timestamp: float,
    output_path: str,
    quality: int = 2
) -> Optional[str]:
    try:
        hours = int(timestamp // 3600)
        minutes = int((timestamp % 3600) // 60)
        seconds = timestamp % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
        
        cmd = [
            "/usr/bin/ffmpeg",
            '-y',                      
            '-ss', time_str,           
            '-i', video_url,           
            '-frames:v', '1',          
            '-q:v', str(quality),      
            '-vf', 'scale=1280:-1',    
            '-an',                     
            '-f', 'image2',            
            output_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.info(f"[SCREENSHOT] ffmpeg error: {result.stderr}")
            return None
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.info(f"[SCREENSHOT] File not created or empty")
            return None
        
        return output_path
    
    except subprocess.TimeoutExpired:
        logger.info(f"[SCREENSHOT] Timeout")
        return None
    except Exception as e:
        logger.info(f"[SCREENSHOT] Error: {e}")
        return None


def download_clip(
    video_url: str,
    start_time: str,
    end_time: str,
    output_path: str,
    use_keyframes: bool = True
) -> Optional[str]:
    try:
        cmd = [
            '/usr/local/bin/yt-dlp',
            '--download-sections', f'*{start_time}-{end_time}',
            '--force-keyframes-at-cuts' if use_keyframes else None,
            '-o', output_path,
            '--no-playlist',
            '--no-warnings',
            video_url
        ]
        
        cmd = [x for x in cmd if x is not None]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  
        )
        
        if result.returncode != 0:
            logger.info(f"[CLIP] yt-dlp error: {result.stderr}")
            return None
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.info(f"[CLIP] File not created or empty")
            return None
        
        return output_path
    
    except subprocess.TimeoutExpired:
        logger.info(f"[CLIP] Timeout (300s)")
        return None
    except Exception as e:
        logger.info(f"[CLIP] Error: {e}")
        return None


def screenshot_to_base64(file_path: str) -> Optional[str]:
    import base64
    
    try:
        with open(file_path, 'rb') as f:
            image_data = f.read()
            base64_data = base64.b64encode(image_data).decode('utf-8')
            return f"data:image/jpeg;base64,{base64_data}"
    except Exception as e:
        logger.info(f"[BASE64] Error: {e}")
        return None


def get_clip_duration(file_path: str) -> Optional[float]:
    try:
        cmd = [
            "/usr/bin/ffprobe",
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            file_path
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        return None
    
    except Exception as e:
        logger.info(f"[DURATION] Error: {e}")
        return None



