import os
import tempfile
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile
import logging



logger = logging.getLogger(__name__)
def convert_to_webm(
    video_file,
    max_width=1280,
    max_height=720,
    crf=35,
    fps=24
):
    try:
        import ffmpeg
        
        if hasattr(video_file, 'path'):
            input_path = video_file.path
        elif hasattr(video_file, 'name'):
            input_path = video_file.name
        else:
            input_path = str(video_file)
        
        if not os.path.exists(input_path):
            logger.info(f"❌ Файл не найден: {input_path}")
            return None
        
        temp_output = tempfile.NamedTemporaryFile(suffix='.webm', delete=False)
        temp_output.close()
        output_path = temp_output.name
        
        try:
            (
                ffmpeg
                .input(input_path)
                .filter('scale', f'min({max_width},iw*{max_height}/ih)', f'min({max_height},ih*{max_width}/iw)')
                .filter('fps', fps=fps)
                .output(
                    output_path,
                    **{
                        'c:v': 'libvpx-vp9',
                        'crf': crf,
                        'b:v': '0',
                        'c:a': 'libopus',
                        'b:a': '96k',  
                        'cpu-used': '4',  
                        'row-mt': '1',  
                        'tile-columns': '4',
                        'frame-parallel': '1',
                        'auto-alt-ref': '0',  
                        'lag-in-frames': '0',  
                    }
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, quiet=True)
            )
        except ffmpeg.Error as e:
            logger.info(f"❌ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            return None
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.info("❌ Пустой или несуществующий выходной файл")
            if os.path.exists(output_path):
                os.unlink(output_path)
            return None
        
        with open(output_path, 'rb') as f:
            webm_data = f.read()
        
        os.unlink(output_path)
        
        import uuid
        unique_name = f"{uuid.uuid4().hex}.webm"
        
        webm_file = ContentFile(webm_data, name=unique_name)
        
        logger.info(f"✅ Конвертировано в WebM: {unique_name} ({len(webm_data) // 1024} KB)")
        return webm_file
        
    except ImportError:
        logger.info("❌ ffmpeg-python не установлен. Запуск: pip install ffmpeg-python")
        return None
    except Exception as e:
        logger.info(f"❌ Ошибка конвертации видео: {e}")
        return None


def get_video_duration(video_file):
    try:
        import ffmpeg
        
        if hasattr(video_file, 'path'):
            input_path = video_file.path
        elif hasattr(video_file, 'name'):
            input_path = video_file.name
        else:
            return 0
        
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
        return duration
        
    except Exception:
        return 0


def get_video_metadata(video_file):
    try:
        import ffmpeg
        
        if hasattr(video_file, 'path'):
            input_path = video_file.path
        elif hasattr(video_file, 'name'):
            input_path = video_file.name
        else:
            return None
        
        probe = ffmpeg.probe(input_path)
        
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        format_data = probe.get('format', {})
        
        fps_str = video_stream.get('r_frame_rate', '30/1')
        try:
            num, den = map(int, fps_str.split('/'))
            fps = num / den if den else 30
        except Exception:
            fps = 30
        
        return {
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'duration': float(format_data.get('duration', 0)),
            'fps': fps
        }
        
    except Exception:
        return None