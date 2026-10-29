"""Compatibility helpers for per-account storage.

Export generation and account deletion intentionally live in data_management so
there is only one privacy-reviewed lifecycle. The former broad chat/contact
export is deliberately unavailable.
"""

from pathlib import Path
import shutil

from django.conf import settings
from django.db.models import Sum

from apps.social.infrastructure.models.social import UploadedFile
from apps.users.application.data_management import delete_user_account


class StorageService:
    def __init__(self, user):
        self.user = user

    def get_storage_usage(self) -> dict:
        from apps.social.models import Attachment, Message, PostComment
        from apps.playlists.models import Playlist
        from apps.users.models import UserLibrary
        from django.db.models.functions import Length
        uploads = UploadedFile.objects.filter(user=self.user).aggregate(total=Sum("file_size"))["total"] or 0
        attachments = Attachment.objects.filter(message__sender=self.user)
        sizes = {kind: attachments.filter(type=kind).aggregate(total=Sum("file_size"))["total"] or 0 for kind in ("file", "image", "video", "audio")}
        messages = Message.objects.filter(sender=self.user).aggregate(total=Sum(Length("text")))["total"] or 0
        cache = self._cache_size()
        total = uploads + sum(sizes.values()) + messages + cache
        limit = getattr(settings, 'USER_STORAGE_LIMIT', 2 * 1024 ** 3)
        percent = min(100, total / limit * 100) if limit else 0
        return {
            "messages": messages, "media": uploads + sizes['image'] + sizes['video'],
            "documents": sizes['file'], "audio": sizes['audio'], "cache": cache,
            "total": total, "used": total, "limit": limit, "percentage": percent, "usage_percent": percent,
            "breakdown": {"messages_count": Message.objects.filter(sender=self.user).count(),
                "comments_count": PostComment.objects.filter(author=self.user).count(),
                "playlists_count": Playlist.objects.filter(user=self.user).count(),
                "library_count": UserLibrary.objects.filter(user=self.user).count()},
        }

    def _cache_path(self) -> Path:
        root = (Path(settings.MEDIA_ROOT) / "cache").resolve()
        path = (root / f"user_{self.user.pk}").resolve()
        path.relative_to(root)
        return path

    def _cache_size(self) -> int:
        path = self._cache_path()
        if not path.is_dir():
            return 0
        return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())

    def clear_cache(self) -> bool:
        path = self._cache_path()
        if path.is_dir():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return True

    def export_data(self, *_args, **_kwargs):
        raise RuntimeError("Use the authenticated DataExport lifecycle; direct exports are disabled")

    def delete_account_data(self) -> dict:
        return {"deleted": delete_user_account(self.user.pk)}
