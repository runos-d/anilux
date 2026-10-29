import csv
import html
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models.deletion import Collector
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from apps.users.infrastructure.models.users import DataExport, User


EXPORT_CATEGORIES = frozenset({
    "profile", "playlists", "shorts", "comments", "reviews", "messages",
    "history", "favorites", "settings", "activity",
})
EXPORT_FORMATS = frozenset({"json", "csv", "html"})


def export_root() -> Path:
    return Path(settings.DATA_EXPORT_ROOT).resolve()


def safe_export_path(value: str) -> Path | None:
    if not value:
        return None
    candidate = Path(value).resolve()
    try:
        candidate.relative_to(export_root())
    except ValueError:
        return None
    return candidate


def delete_export_file(record: DataExport) -> None:
    path = safe_export_path(record.file_path)
    if path and path.is_file():
        path.unlink(missing_ok=True)


def _profile(user: User):
    return [{
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number,
        "display_name": user.display_name,
        "nickname": user.nickname,
        "bio": user.bio,
        "favorite_genres": user.favorite_genres,
        "created_at": user.created_at,
        "email_verified": user.email_verified,
        "phone_verified": user.phone_verified,
    }]


def _playlists(user: User):
    from apps.playlists.infrastructure.models.playlists import Playlist

    result = []
    for playlist in Playlist.objects.filter(user=user).prefetch_related("items"):
        result.append({
            "id": playlist.pk,
            "title": playlist.title,
            "description": playlist.description,
            "visibility": playlist.visibility,
            "created_at": playlist.created_at,
            "updated_at": playlist.updated_at,
            "items": [{
                "anime_id": item.anime_id,
                "nested_playlist_id": item.nested_playlist_id,
                "position": item.position,
                "notes": item.notes,
                "added_at": item.added_at,
            } for item in playlist.items.all()],
        })
    return result


def _messages(user: User):
    from apps.social.infrastructure.models.social import Message

    return list(Message.objects.filter(sender=user).order_by("created_at").values(
        "id", "text", "message_type", "media_type", "created_at", "updated_at", "is_edited", "is_deleted"
    ))


def _comments(user: User):
    from apps.social.infrastructure.models.social import PostComment

    return list(PostComment.objects.filter(author=user).order_by("created_at").values(
        "id", "post_id", "content", "created_at", "updated_at", "is_deleted"
    ))


def _history(user: User):
    from apps.anime.infrastructure.models.anime import UserEpisodeProgress, WatchProgress
    from apps.users.infrastructure.models.users import UserLibrary

    return {
        "library": list(UserLibrary.objects.filter(user=user).values(
            "anime_id", "status", "current_season", "current_episode", "episodes_watched",
            "rating", "notes", "is_favorite", "added_at", "updated_at"
        )),
        "watch_progress": list(WatchProgress.objects.filter(user=user).values(
            "anime_id", "episode_id", "current_time", "duration", "is_completed", "watch_count", "last_watched"
        )),
        "episode_progress": list(UserEpisodeProgress.objects.filter(user=user).values(
            "anime_id", "season_number", "episode_number", "status", "last_position", "duration", "watched_at"
        )),
    }


def _favorites(user: User):
    from apps.playlists.infrastructure.models.playlists import FavoriteAnime, FavoritePlaylist
    from apps.users.infrastructure.models.users import FavoriteEpisode, FavoriteTheme, UserFavorite

    return {
        "anime": list(UserFavorite.objects.filter(user=user).values("anime_id", "added_at")),
        "playlist_anime": list(FavoriteAnime.objects.filter(user=user).values("anime_id", "created_at")),
        "playlists": list(FavoritePlaylist.objects.filter(user=user).values("playlist_id", "created_at")),
        "episodes": list(FavoriteEpisode.objects.filter(user=user).values("anime_id", "season", "episode", "note", "added_at")),
        "themes": list(FavoriteTheme.objects.filter(user=user).values("anime_id", "theme_type", "season", "episode", "title", "added_at")),
    }


def _settings(user: User):
    result = {}
    for relation, fields in {
        "settings": ("theme", "ui_style", "text_size", "show_in_search", "show_online_status", "show_stats", "personalized_recommendations"),
        "profile_settings": ("theme", "accent_color", "language", "timezone", "date_format", "time_format", "show_online_status", "show_last_seen", "show_typing_status", "allow_calls", "allow_group_invites"),
        "notification_settings": ("push_enabled", "email_enabled", "email_frequency"),
        "privacy_settings": ("who_can_see_phone", "who_can_see_email", "who_can_see_last_seen", "who_can_see_profile_photo", "allow_message_forwarding", "who_can_call", "who_can_add_to_groups", "analytics_consent_state", "analytics_consent_version"),
    }.items():
        instance = getattr(user, relation, None)
        if instance is not None:
            result[relation] = {field: getattr(instance, field) for field in fields if hasattr(instance, field)}
    return result


def _activity(user: User):
    from apps.social.infrastructure.models.social import Message, Post, PostComment
    from apps.playlists.infrastructure.models.playlists import Playlist

    return [{
        "messages_sent": Message.objects.filter(sender=user).count(),
        "posts_created": Post.objects.filter(author=user).count(),
        "comments_created": PostComment.objects.filter(author=user).count(),
        "playlists_created": Playlist.objects.filter(user=user).count(),
    }]


def _own_model_rows(app_label: str, model_name: str, user: User):
    from django.apps import apps

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return []
    user_field = next((name for name in ("user", "author", "owner") if any(f.name == name for f in model._meta.fields)), None)
    if not user_field:
        return []
    safe_fields = [
        field.name for field in model._meta.fields
        if field.name not in {"user", "author", "owner"} and not field.many_to_one
        and field.get_internal_type() not in {"FileField", "ImageField", "BinaryField"}
    ]
    return list(model.objects.filter(**{user_field: user}).values(*safe_fields))


def collect_export_data(user: User, categories: list[str]) -> dict:
    loaders = {
        "profile": _profile,
        "playlists": _playlists,
        "shorts": lambda value: _own_model_rows("reactor", "ReactorPost", value),
        "comments": _comments,
        "reviews": lambda value: _own_model_rows("dubs", "DubReview", value),
        "messages": _messages,
        "history": _history,
        "favorites": _favorites,
        "settings": _settings,
        "activity": _activity,
    }
    return {category: loaders[category](user) for category in categories}


def _write_category(archive: zipfile.ZipFile, category: str, value, output_format: str) -> None:
    if output_format == "json":
        archive.writestr(f"{category}.json", json.dumps(value, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder))
        return
    rows = value if isinstance(value, list) else [{"section": key, "data": json.dumps(item, ensure_ascii=False, cls=DjangoJSONEncoder)} for key, item in value.items()]
    flattened = [{key: json.dumps(item, ensure_ascii=False, cls=DjangoJSONEncoder) if isinstance(item, (dict, list)) else item for key, item in row.items()} for row in rows]
    headers = sorted({key for row in flattened for key in row})
    if output_format == "csv":
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=headers)
        writer.writeheader()
        writer.writerows(flattened)
        archive.writestr(f"{category}.csv", buffer.getvalue())
        return
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in headers) + "</tr>" for row in flattened)
    head = "".join(f"<th>{html.escape(key)}</th>" for key in headers)
    archive.writestr(f"{category}.html", f"<!doctype html><meta charset='utf-8'><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")


def build_user_export(export_id: int) -> None:
    with transaction.atomic():
        record = DataExport.objects.select_for_update().select_related("user").get(pk=export_id)
        if record.status != "queued":
            return
        record.status = "processing"
        record.error_code = ""
        record.save(update_fields=["status", "error_code"])
    temp_path = None
    target = None
    try:
        data = collect_export_data(record.user, record.items)
        target_dir = export_root() / str(record.user_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"export-{record.pk}.zip"
        handle, temp_name = tempfile.mkstemp(prefix="export-", suffix=".tmp", dir=target_dir)
        os.close(handle)
        temp_path = Path(temp_name)
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps({
                "created_at": timezone.now(), "categories": record.items, "format": record.format,
                "privacy": "Only data belonging to the requesting account is included.",
            }, ensure_ascii=False, indent=2, cls=DjangoJSONEncoder))
            for category, value in data.items():
                _write_category(archive, category, value, record.format)
        os.replace(temp_path, target)
        with transaction.atomic():
            current = DataExport.objects.select_for_update().get(pk=record.pk)
            if current.status == "canceled":
                target.unlink(missing_ok=True)
                return
            current.status = "ready"
            current.file_path = str(target)
            current.size = str(target.stat().st_size)
            current.save(update_fields=["status", "file_path", "size"])
    except Exception:
        if temp_path:
            temp_path.unlink(missing_ok=True)
        if target:
            target.unlink(missing_ok=True)
        DataExport.objects.filter(pk=export_id).exclude(status="canceled").update(status="failed", error_code="export_failed")


def expire_exports(now=None) -> int:
    now = now or timezone.now()
    records = list(DataExport.objects.filter(expires_at__lte=now).exclude(status="expired"))
    for record in records:
        delete_export_file(record)
    if records:
        DataExport.objects.filter(pk__in=[record.pk for record in records]).update(status="expired", file_path="", download_url="")
    return len(records)


def _session_keys_for_user(user_id: int) -> list[str]:
    keys = []
    for session in Session.objects.filter(expire_date__gte=timezone.now()).iterator():
        try:
            if str(session.get_decoded().get("_auth_user_id")) == str(user_id):
                keys.append(session.session_key)
        except Exception:
            continue
    return keys


def _collect_user_files(user: User) -> list[tuple[object, str]]:
    collector = Collector(using="default")
    collector.collect([user])
    files: list[tuple[object, str]] = []
    objects = [item for values in collector.data.values() for item in values]
    for queryset in collector.fast_deletes:
        objects.extend(list(queryset))
    for instance in objects:
        for field in instance._meta.fields:
            if field.get_internal_type() not in {"FileField", "ImageField"}:
                continue
            value = getattr(instance, field.name, None)
            if value and getattr(value, "name", ""):
                files.append((value.storage, value.name))
    for record in DataExport.objects.filter(user=user):
        path = safe_export_path(record.file_path)
        if path:
            files.append((None, str(path)))
    return files


def delete_user_account(user_id: int) -> bool:
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=user_id).first()
        if user is None:
            return False
        from apps.anime.models import BackgroundJob
        BackgroundJob.objects.filter(payload__actor=str(user.pk)).delete()
        file_refs = _collect_user_files(user)
        session_keys = _session_keys_for_user(user.pk)
        outstanding = list(OutstandingToken.objects.filter(user=user))
        for token in outstanding:
            BlacklistedToken.objects.get_or_create(token=token)
        Session.objects.filter(session_key__in=session_keys).delete()
        user.delete()

    # Forwarded media can have multiple database owners. Query each field once
    # for the entire batch instead of issuing model queries for every file.
    from django.apps import apps
    groups = {}
    for storage, name in file_refs:
        if storage is not None:
            root = Path(storage.location).resolve()
            groups.setdefault(root, {})[name] = storage
        else:
            path = safe_export_path(name)
            if path:
                path.unlink(missing_ok=True)
    for root, files in groups.items():
        referenced = set()
        for model in apps.get_models():
            for field in model._meta.fields:
                if field.get_internal_type() in {"FileField", "ImageField"} and Path(field.storage.location).resolve() == root:
                    referenced.update(model.objects.filter(**{field.name + "__in": list(files)}).values_list(field.name, flat=True))
        for name, storage in files.items():
            if name not in referenced:
                try:
                    storage.delete(name)
                except OSError:
                    continue
    account_dir = export_root() / str(user_id)
    if account_dir.is_dir():
        shutil.rmtree(account_dir, ignore_errors=True)
    return True
