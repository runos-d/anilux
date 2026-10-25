import os
import logging
import subprocess
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)


class PosterEnhancementService:
    def __init__(self):
        self.enabled = getattr(settings, 'POSTER_ENHANCEMENT_ENABLED', False)
        self.binary_path = getattr(settings, 'REALESRGAN_BINARY_PATH', '')
        self.model_path = getattr(settings, 'REALESRGAN_MODEL_PATH', '')
        self.model_name = getattr(settings, 'REALESRGAN_MODEL_NAME', 'realesr-animevideov3')
        self.scale = getattr(settings, 'REALESRGAN_SCALE', 2)
        self.tile_size = getattr(settings, 'REALESRGAN_TILE_SIZE', 0)
        self.tta = getattr(settings, 'REALESRGAN_TTA', False)

    def enhance(self, input_path: str) -> str | None:
        if not self.enabled:
            return None

        if not os.path.exists(input_path):
            logger.warning('Poster enhancement skipped: input file not found: %s', input_path)
            return None

        if not self.binary_path or not os.path.exists(self.binary_path):
            logger.warning('Poster enhancement skipped: binary not found at %s', self.binary_path)
            return None

        if not self.model_path or not os.path.isdir(self.model_path):
            logger.warning('Poster enhancement skipped: model path invalid: %s', self.model_path)
            return None

        try:
            input_path = os.path.abspath(input_path)
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_enhanced{ext if ext else '.png'}"

            cmd = [
                self.binary_path,
                '-i', input_path,
                '-o', output_path,
                '-n', self.model_name,
                '-s', str(self.scale),
                '-m', self.model_path,
            ]

            if self.tile_size:
                cmd.extend(['-t', str(self.tile_size)])

            if self.tta:
                cmd.append('-x')

            logger.info('Real-ESRGAN starting: %s', ' '.join(cmd))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )

            logger.info('Real-ESRGAN finished for %s: rc=%s stdout=%s stderr=%s', input_path, result.returncode, result.stdout[:500], result.stderr[:500])

            if result.returncode != 0:
                logger.warning('Real-ESRGAN failed for %s: %s', input_path, result.stderr[:500])
                return None

            if not os.path.exists(output_path):
                logger.warning('Real-ESRGAN output missing for %s', input_path)
                return None

            logger.info('Poster enhanced: %s -> %s', input_path, output_path)
            return output_path

        except subprocess.TimeoutExpired:
            logger.warning('Real-ESRGAN timeout for %s', input_path)
            return None
        except Exception as e:
            logger.exception('Poster enhancement error for %s', input_path)
            return None
