import json
import logging
import os
import tempfile
import uuid
from datetime import date, datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, NamedTuple, Optional, Tuple

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from .release_year import release_year, valid_year, premiere_date

logger = logging.getLogger(__name__)

DUMPS_BASE = os.environ.get("KODIK_DUMPS_BASE", "https://dumps.kodikres.com").rstrip("/")
DUMPS = {
    "serials": "/serials/anime-serial.json",
    "films": "/films/anime.json",
    "calendar": "/calendar.json",
}
CATALOG_DUMPS = ("serials", "films")
ANIME_TYPES = frozenset({"anime", "anime-serial"})

CALENDAR_CACHE_KEY = "kodik:calendar:entries:v1"
CALENDAR_CACHE_TTL = 6 * 3600
LOCK_KEY = "kodik:dump_import:lock"
LOCK_TTL = 2 * 3600


class DumpError(RuntimeError):
    """Error..."""

def _token() -> str:
    token = os.environ.get("KODIK_API_TOKEN")
    if not token:
        from apps.anime.infrastructure.clients import kodik_config
        token = kodik_config.KODIK_API_TOKEN
    if not token:
        raise DumpError("KODIK_API_TOKEN не задан")
    return token


def _mask(text: str) -> str:
    try:
        token = _token()
    except DumpError:
        return text
    return text.replace(token, "***")


def _dump_dir() -> Path:
    custom = getattr(settings, "KODIK_DUMP_DIR", None) or os.environ.get("KODIK_DUMP_DIR")
    path = Path(custom) if custom else Path(tempfile.gettempdir()) / "anilux_kodik_dumps"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path(name: str) -> Path:
    return _dump_dir() / f"{name}.state.json"


def _load_state(name: str) -> Dict[str, Any]:
    try:
        with open(_state_path(name), encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(name: str, state: Dict[str, Any]) -> None:
    path = _state_path(name)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh)
    os.replace(tmp, path)


def _version(state: Dict[str, Any]) -> str:
    return state.get("etag") or state.get("last_modified") or state.get("downloaded_at") or ""


def _needs_import(name: str) -> bool:
    state = _load_state(name)
    return bool(_version(state)) and state.get("imported_version") != _version(state)


def _mark_imported(name: str) -> None:
    state = _load_state(name)
    state["imported_version"] = _version(state)
    state["imported_at"] = timezone.now().isoformat()
    _save_state(name, state)


def _assert_json_array(path: Path) -> None:
    with open(path, "rb") as fh:
        head = fh.read(64).lstrip(b"\xef\xbb\xbf \t\r\n")
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        fh.seek(max(0, size - 64))
        tail = fh.read().rstrip(b" \t\r\n")
    if not head.startswith(b"[") or not tail.endswith(b"]"):
        raise DumpError(f"{path.name}: файл не похож на JSON-массив (повреждён или неполный)")

def download_dump(name: str, force: bool = False) -> Tuple[Path, bool]:
    if name not in DUMPS:
        raise ValueError(f"Неизвестный дамп: {name}")
    path = _dump_dir() / f"{name}.json"
    state = _load_state(name)
    headers: Dict[str, str] = {}
    if not force and path.exists():
        if state.get("etag"):
            headers["If-None-Match"] = state["etag"]
        elif state.get("last_modified"):
            headers["If-Modified-Since"] = state["last_modified"]

    url = f"{DUMPS_BASE}{DUMPS[name]}"
    part = path.with_suffix(".json.part")
    try:
        with requests.get(url, params={"token": _token()}, headers=headers, stream=True, timeout=(15, 120)) as resp:
            if resp.status_code == 304 and path.exists():
                return path, False
            resp.raise_for_status()
            expected = int(resp.headers.get("Content-Length") or 0)
            compressed = bool(resp.headers.get("Content-Encoding"))
            written = 0
            with open(part, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    if chunk:
                        fh.write(chunk)
                        written += len(chunk)
            if expected and not compressed and written != expected:
                raise DumpError(f"{name}: получено {written} байт из {expected}")
            _assert_json_array(part)
            os.replace(part, path)
            state.update(
                etag=resp.headers.get("ETag", ""),
                last_modified=resp.headers.get("Last-Modified", ""),
                downloaded_at=timezone.now().isoformat(),
            )
            _save_state(name, state)
    except requests.RequestException as exc:
        raise DumpError(_mask(f"{name}: ошибка загрузки: {exc}")) from None
    except Exception:
        try:
            part.unlink()
        except OSError:
            pass
        raise
    return path, True


def iter_json_array(path: Path, chunk_size: int = 1 << 20) -> Iterator[Any]:
    decoder = json.JSONDecoder()
    with open(path, encoding="utf-8-sig") as fh:
        state = {"buf": "", "pos": 0}

        def more() -> bool:
            chunk = fh.read(chunk_size)
            if not chunk:
                return False
            state["buf"] = state["buf"][state["pos"]:] + chunk
            state["pos"] = 0
            return True

        def skip(chars: str) -> bool:
            while True:
                buf, pos = state["buf"], state["pos"]
                while pos < len(buf) and buf[pos] in chars:
                    pos += 1
                state["pos"] = pos
                if pos < len(buf):
                    return True
                if not more():
                    return False

        if not skip(" \t\r\n"):
            return
        if state["buf"][state["pos"]] != "[":
            raise DumpError(f"{path.name}: ожидался JSON-массив")
        state["pos"] += 1
        while True:
            if not skip(" \t\r\n,"):
                return
            if state["buf"][state["pos"]] == "]":
                return
            while True:
                try:
                    obj, end = decoder.raw_decode(state["buf"], state["pos"])
                    break
                except json.JSONDecodeError:
                    if not more():
                        raise DumpError(f"{path.name}: оборванный или некорректный JSON")
            state["pos"] = end
            yield obj

def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _episodes_total(item: Dict[str, Any]) -> Optional[int]:
    md = item.get("material_data") or {}
    total = _to_int(md.get("episodes_total"))
    if total and total > 0:
        return total
    candidates = [
        _to_int(md.get("episodes_aired")),
        _to_int(item.get("last_episode")),
        _to_int(item.get("episodes_count")),
    ]
    candidates = [c for c in candidates if c and c > 0]
    return max(candidates) if candidates else None


def _light(item: Dict[str, Any]) -> Dict[str, Any]:
    from .episode_availability import provider_episodes
    md = item.get("material_data") or {}
    score = _to_float(md.get("shikimori_rating")) or _to_float(md.get("kinopoisk_rating")) or 0.0
    return {
        "id": item.get("id") or "",
        "link": item.get("link") or "",
        "updated_at": item.get("updated_at") or "",
        "status": md.get("anime_status") or None,
        "episodes": _episodes_total(item),
        "score": score if score > 0 else None,
        "year": release_year(item),
        "release_date": premiere_date(item),
        "legacy_year": valid_year(md.get('year')),
        "available_episodes": provider_episodes(item),
    }


class _Cur(NamedTuple):
    pk: int
    kodik_id: str
    status: str
    episodes: Optional[int]
    score: Optional[float]
    kodik_link: str
    episode_duration: Optional[int]
    year: Optional[int] = None
    release_date: Optional[date] = None


def _new_group() -> Dict[str, Any]:
    return {"latest": None, "current": None, "episodes": None,
            "status": None, "status_ts": "", "score": None, "score_ts": "",
            "year": None, "legacy_year": None, "year_ts": "", "release_date": None,
            "release_date_ts": "", "available_episodes": None,
            "availability_complete": True}


def _collect(group: Dict[str, Any], light: Dict[str, Any], cur: _Cur) -> None:
    if light.get('available_episodes') is None:
        group['availability_complete'] = False
    if light.get('available_episodes') is not None:
        if group['available_episodes'] is None:
            group['available_episodes'] = set()
        group['available_episodes'].update(light['available_episodes'])
    ts = light["updated_at"]
    is_current = (cur.kodik_id and light["id"] == cur.kodik_id) or (
        not cur.kodik_id and cur.kodik_link and light["link"] == cur.kodik_link
    )
    if is_current:
        group["current"] = light
    if group["latest"] is None or ts >= group["latest"]["updated_at"]:
        group["latest"] = light
    if light["episodes"] and (group["episodes"] is None or light["episodes"] > group["episodes"]):
        group["episodes"] = light["episodes"]
    if light["status"] and ts >= group["status_ts"]:
        group["status"], group["status_ts"] = light["status"], ts
    if light["score"] and ts >= group["score_ts"]:
        group["score"], group["score_ts"] = light["score"], ts
    if light.get('year') and ts >= group['year_ts']:
        group['year'], group['legacy_year'], group['year_ts'] = light['year'], light.get('legacy_year'), ts
    if light.get('release_date') and ts >= group['release_date_ts']:
        group['release_date'], group['release_date_ts'] = light['release_date'], ts


def plan_update(cur: _Cur, group: Dict[str, Any], map_status, full_scan: bool = True) -> Dict[str, Any]:
    changes: Dict[str, Any] = {}
    if group.get('year') and cur.year != group['year'] and (cur.year is None or cur.year == group.get('legacy_year')):
        changes['year'] = group['year']
    if group.get('release_date') and cur.release_date is None:
        changes['release_date'] = group['release_date']
        changes['release_date_string'] = group['release_date'].isoformat()
    if group["status"]:
        status = map_status(group["status"])
        if status and status != cur.status:
            changes["status"] = status
    episodes = group["episodes"]
    if episodes and episodes != cur.episodes:
        changes["episodes"] = episodes
        if cur.episode_duration:
            changes["total_duration"] = episodes * cur.episode_duration
    score = group["score"]
    if score and abs(score - (cur.score or 0.0)) > 0.004:
        changes["score"] = score

    chosen = group["current"] or (group["latest"] if full_scan else None)
    if chosen and chosen["link"]:
        if chosen["link"] != cur.kodik_link:
            changes["kodik_link"] = chosen["link"]
        if chosen["id"] and chosen["id"] != cur.kodik_id:
            changes["kodik_id"] = chosen["id"]
    return changes

def _acquire_lock() -> Optional[str]:
    owner = uuid.uuid4().hex
    return owner if cache.add(LOCK_KEY, owner, LOCK_TTL) else None


def _release_lock(owner: str) -> None:
    if cache.get(LOCK_KEY) == owner:
        cache.delete(LOCK_KEY)


def _load_existing() -> Dict[int, _Cur]:
    from apps.anime.infrastructure.models.anime import Anime

    existing: Dict[int, _Cur] = {}
    rows = Anime.objects.exclude(shikimori_id__isnull=True).values_list(
        "id", "shikimori_id", "kodik_id", "status", "episodes", "score", "kodik_link", "episode_duration", "year", "release_date"
    )
    for pk, sid, kodik_id, status, episodes, score, link, duration, year, exact_date in rows.iterator(chunk_size=5000):
        existing[sid] = _Cur(pk, kodik_id or "", status or "", episodes, score, link or "", duration, year, exact_date)
    return existing


def sync_catalog(force: bool = False, max_new: int = 3000, download_posters: bool = False,
                 dry_run: bool = False) -> Dict[str, Any]:
    owner = _acquire_lock()
    if not owner:
        return {"skipped": "уже выполняется другой импорт"}
    try:
        return _sync_catalog(force, max_new, download_posters, dry_run)
    finally:
        _release_lock(owner)


def _sync_catalog(force: bool, max_new: int, download_posters: bool, dry_run: bool) -> Dict[str, Any]:
    from apps.anime.application.anime_service import anime_service
    from apps.anime.infrastructure.models.anime import Anime

    stats: Dict[str, Any] = {
        "downloaded": [], "unchanged": [], "errors": [], "records": 0, "no_shikimori_id": 0,
        "other_type": 0, "titles_in_db": 0, "updated": 0, "update_fields": {},
        "created": 0, "deferred_new": 0, "failed_new": 0, "dry_run": dry_run, "availability_changed": 0,
    }

    files: Dict[str, Path] = {}
    need = force
    for name in CATALOG_DUMPS:
        try:
            path, changed = download_dump(name, force=force)
        except DumpError as exc:
            stats["errors"].append(str(exc))
            local = _dump_dir() / f"{name}.json"
            if local.exists():
                files[name] = local
            continue
        files[name] = path
        (stats["downloaded"] if changed else stats["unchanged"]).append(name)
        need = need or changed or _needs_import(name)

    if not files or not need:
        stats["note"] = "дампы не менялись, импорт не требуется"
        return stats

    full_scan = len(files) == len(CATALOG_DUMPS)
    existing = _load_existing()
    stats["titles_in_db"] = len(existing)

    groups: Dict[int, Dict[str, Any]] = {}
    new_groups: Dict[int, List[Dict[str, Any]]] = {}
    for name, path in files.items():
        for item in iter_json_array(path):
            if not isinstance(item, dict):
                continue
            stats["records"] += 1
            if item.get("type") not in ANIME_TYPES:
                stats["other_type"] += 1
                continue
            sid = _to_int(item.get("shikimori_id"))
            if not sid:
                stats["no_shikimori_id"] += 1
                continue
            cur = existing.get(sid)
            if cur is not None:
                _collect(groups.setdefault(sid, _new_group()), _light(item), cur)
            elif sid in new_groups:
                new_groups[sid].append(item)
            elif len(new_groups) < max_new:
                new_groups[sid] = [item]
            else:
                stats["deferred_new"] += 1

    pending: List[Tuple[int, Dict[str, Any]]] = []
    for sid, group in groups.items():
        changes = plan_update(existing[sid], group, anime_service._map_status, full_scan)
        if changes:
            pending.append((sid, changes))
            for field in changes:
                stats["update_fields"][field] = stats["update_fields"].get(field, 0) + 1
    stats["updated"] = len(pending)

    if not dry_run and pending:
        fields = [
            "status", "episodes", "progress_total", "total_duration", "score", "kodik_link", "kodik_id",
            "year", "release_date", "release_date_string", "updated_at",
        ]
        now = timezone.now()
        objs: List[Any] = []
        full_rows = {
            r[0]: r for r in Anime.objects.filter(pk__in=[existing[s].pk for s, _ in pending]).values_list(
                "id", "status", "episodes", "progress_total", "total_duration", "score", "kodik_link", "kodik_id",
                "year", "release_date", "release_date_string")
        }
        for sid, changes in pending:
            pk = existing[sid].pk
            row = full_rows.get(pk)
            if row is None:
                continue
            obj = Anime(pk=pk, status=row[1], episodes=row[2], progress_total=row[3],
                        total_duration=row[4], score=row[5], kodik_link=row[6],
                        kodik_id=row[7], year=row[8], release_date=row[9],
                        release_date_string=row[10], updated_at=now)
            for key, value in changes.items():
                setattr(obj, key, value)
            if (changes.get("episodes") or 0) > (row[3] or 0):
                obj.progress_total = changes["episodes"]
            objs.append(obj)
        for i in range(0, len(objs), 500):
            Anime.objects.bulk_update(objs[i:i + 500], fields)
        from apps.anime.models import Franchise
        changed_year_ids = [existing[sid].pk for sid, changes in pending if 'year' in changes]
        franchise_ids = Anime.objects.filter(pk__in=changed_year_ids, franchise__isnull=False).values_list('franchise_id', flat=True).distinct()
        for franchise in Franchise.objects.filter(pk__in=franchise_ids):
            franchise.update_aggregated_data()
        from .recommendations import invalidate_catalog
        invalidate_catalog()

    if dry_run:
        stats["created"] = len(new_groups)
    else:
        for sid, records in new_groups.items():
            records.sort(key=lambda r: (bool(r.get("material_data")), r.get("updated_at") or ""))
            try:
                anime = None
                for record in records:
                    anime, _ = anime_service.import_anime(
                        record, update_existing=True, download_posters=download_posters, skip_shikimori=True,
                        track_availability=False)
                titles = sorted({(r.get("translation") or {}).get("title") for r in records} - {None, ""})
                if anime is not None and titles:
                    Anime.objects.filter(pk=anime.pk).update(translations=titles)
                stats["created"] += 1
            except Exception as exc:
                stats["failed_new"] += 1
                logger.exception("Kodik dump: не удалось создать тайтл shikimori_id=%s: %s", sid, exc)

    if not dry_run and not stats['errors']:
        from .episode_availability import apply_availability, provider_episodes
        observed = {existing[sid].pk: group['available_episodes'] for sid, group in groups.items()
                    if group['available_episodes'] is not None}
        new_ids = dict(Anime.objects.filter(shikimori_id__in=new_groups).values_list('shikimori_id', 'pk'))
        for sid, records in new_groups.items():
            episodes = [provider_episodes(record) for record in records]
            known = [value for value in episodes if value is not None]
            if sid in new_ids and known:
                observed[new_ids[sid]] = set().union(*known)
        complete_ids = {existing[sid].pk for sid, group in groups.items() if group['availability_complete']}
        complete_ids.update(new_ids[sid] for sid, records in new_groups.items() if sid in new_ids
            and all(provider_episodes(record) is not None for record in records))
        if full_scan and not stats['errors']:
            from apps.anime.models import KodikAvailability
            missing_ids = KodikAvailability.objects.exclude(anime__shikimori_id__isnull=True).exclude(
                anime__shikimori_id__in=set(groups) | set(new_groups)).values_list('anime_id', flat=True)
            for pk in missing_ids:
                observed[pk] = set()
                complete_ids.add(pk)
        complete = {pk: value for pk, value in observed.items() if pk in complete_ids}
        partial = {pk: value for pk, value in observed.items() if pk not in complete_ids}
        stats['availability_changed'] = apply_availability(complete, replace=full_scan and not stats['errors'])
        stats['availability_changed'] += apply_availability(partial)

    if not dry_run and not stats["errors"] and not stats["deferred_new"] and not stats["failed_new"]:
        for name in files:
            _mark_imported(name)
    logger.info("Kodik dump import: %s", stats)
    return stats

def normalize_calendar(raw: Any) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    if not isinstance(raw, list):
        raise DumpError('Календарь должен быть JSON-массивом')
    now = datetime.now(dt_timezone.utc)
    for item in raw:
        if not isinstance(item, dict):
            raise DumpError('Некорректная запись календаря')
        anime = item.get("anime") or {}
        sid = _to_int(anime.get("id"))
        aired_at = item.get("next_episode_at")
        if not sid or not aired_at:
            raise DumpError('В записи календаря отсутствует ID или дата')
        try:
            release_date = datetime.fromisoformat(str(aired_at).replace("Z", "+00:00"))
            if not release_date.tzinfo:
                release_date = release_date.replace(tzinfo=dt_timezone.utc)
            upcoming = release_date > now
        except ValueError as exc:
            raise DumpError('Некорректная дата календаря') from exc
        image = anime.get("image") or {}
        entries.append({
            "id": sid,
            "name": anime.get("name") or "",
            "russian": anime.get("russian") or "",
            "english": anime.get("name") or "",
            "japanese": "",
            "image": image,
            "poster_url": image.get("original") or "",
            "kind": item.get("kind") or "",
            "status": item.get("status"),
            "score": _to_float(item.get("score")),
            "episodes": _to_int(item.get("episodes")),
            "episodes_aired": _to_int(item.get("episodes_aired")),
            "episode": _to_int(item.get("next_episode")),
            "aired_at": aired_at,
            "is_upcoming": upcoming,
            "duration": _to_int(item.get("duration")),
        })
    return entries


def _calendar_file() -> Path:
    return _dump_dir() / "calendar.normalized.json"


def sync_calendar(force: bool = False) -> Dict[str, Any]:
    stats: Dict[str, Any] = {"downloaded": False, "entries": 0}
    path, changed = download_dump("calendar", force=force)
    with open(path, encoding="utf-8-sig") as fh:
        entries = normalize_calendar(json.load(fh))
    from .calendar_history import merge_calendar
    merge_calendar(entries)
    tmp = _calendar_file().with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False)
    os.replace(tmp, _calendar_file())
    try:
        cache.set(CALENDAR_CACHE_KEY, entries, CALENDAR_CACHE_TTL)
    except Exception:
        logger.warning('Calendar cache unavailable; history saved in DB', exc_info=True)
    stats.update(downloaded=changed, entries=len(entries))
    return stats


def get_calendar_entries() -> Optional[List[Dict[str, Any]]]:
    try:
        entries = cache.get(CALENDAR_CACHE_KEY)
    except Exception:
        entries = None
    if entries is not None:
        return entries
    try:
        with open(_calendar_file(), encoding="utf-8") as fh:
            entries = json.load(fh)
    except (OSError, ValueError):
        return None
    try:
        cache.set(CALENDAR_CACHE_KEY, entries, CALENDAR_CACHE_TTL)
    except Exception:
        pass
    return entries
