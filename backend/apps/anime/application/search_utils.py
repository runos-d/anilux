import re
import logging
from typing import List, Dict, Any
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def legacy_anime_slug(title: str) -> str:
    replacements = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e",
        "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k",
        "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
        "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
        "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
        "э": "e", "ю": "yu", "я": "ya",
    }
    slug = (title or "").lower()
    slug = "".join(replacements.get(char, char) for char in slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def normalize_search_string(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    text = re.sub(r"[-:\s]+", " ", text)
    text = re.sub(r"[^а-яa-z0-9\s]", "", text)
    text = " ".join(text.split())
    return text


def normalize_search_string_flexible(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("ё", "е")
    text = text.replace("-", "").replace(":", "")
    text = re.sub(r"[^а-яa-z0-9]", "", text)
    return text


def fuzzy_match(query: str, text: str, threshold: float = 0.6) -> float:
    if not query or not text:
        return 0.0
    query_norm = normalize_search_string(query)
    text_norm = normalize_search_string(text)
    if not query_norm or not text_norm:
        return 0.0
    if query_norm == text_norm:
        return 1.0
    if query_norm in text_norm or text_norm in query_norm:
        return 0.9
    return SequenceMatcher(None, query_norm, text_norm).ratio()


def flexible_title_match(query: str, *titles: str) -> bool:
    query_normalized = normalize_search_string(query)
    query_compact = normalize_search_string_flexible(query)
    if len(query_compact) < 2:
        return False

    query_words = query_normalized.split()
    similarity_threshold = 0.80 if len(query_compact) <= 5 else 0.72

    for title in titles:
        title_normalized = normalize_search_string(title)
        title_compact = normalize_search_string_flexible(title)
        if not title_compact:
            continue

        if query_compact in title_compact or title_compact in query_compact:
            return True

        if len(query_compact) < 4:
            continue

        title_words = title_normalized.split()
        candidates = [title_compact]
        if title_words:
            window_size = max(1, len(query_words))
            candidates.extend(
                "".join(title_words[index:index + window_size])
                for index in range(len(title_words) - window_size + 1)
            )

        if any(
            SequenceMatcher(None, query_compact, candidate).ratio() >= similarity_threshold
            for candidate in candidates
            if candidate
        ):
            return True

        
        if len(query_words) > 1 and all(
            any(SequenceMatcher(None, query_word, title_word).ratio() >= 0.76 for title_word in title_words)
            for query_word in query_words
        ):
            return True

    return False


def fuzzy_search_anime(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    if not query or len(query.strip()) < 2:
        return []
    try:
        from apps.anime.infrastructure.models.anime import Anime, Franchise
        query = query.strip()
        logger.debug("fuzzy_search_anime query=%r", query)
        query_compact = normalize_search_string_flexible(query)
        query_normalized = normalize_search_string(query)
        search_words = query_normalized.split()
        queryset = Anime.objects.filter(
            title_ru__regex=r"[а-яёА-ЯЁ]"
        ).order_by("-score")[:limit * 5]
        results = []
        seen_ids = set()
        matched_franchise_ids = set()
        for anime in queryset:
            if len(results) >= limit:
                break
            if anime.id in seen_ids:
                continue
            searchable_compact = [
                normalize_search_string_flexible(anime.title_ru or ""),
                normalize_search_string_flexible(anime.title_en or ""),
                normalize_search_string_flexible(anime.title_jp or ""),
                normalize_search_string_flexible(anime.slug or ""),
            ]
            searchable_split = [
                normalize_search_string(anime.title_ru or ""),
                normalize_search_string(anime.title_en or ""),
                normalize_search_string(anime.title_jp or ""),
                normalize_search_string(anime.slug or ""),
            ]
            found = False
            if len(query_compact) >= 2:
                for text in searchable_compact:
                    if query_compact in text:
                        found = True
                        break
            if not found and search_words:
                for text in searchable_split:
                    if all(word in text for word in search_words if len(word) >= 2):
                        found = True
                        break
            if found:
                seen_ids.add(anime.id)
                if anime.franchise_id:
                    matched_franchise_ids.add(anime.franchise_id)
                poster_url = (
                    anime.poster_image_url
                    if hasattr(anime, "poster_image_url")
                    else anime.poster_url
                )
                results.append({
                    "id": anime.id,
                    "title_ru": anime.title_ru or "",
                    "title_en": anime.title_en or "",
                    "title_jp": anime.title_jp or "",
                    "year": anime.year,
                    "status": anime.status,
                    "kind": anime.kind,
                    "episodes": anime.episodes,
                    "score": anime.score,
                    "poster_url": poster_url,
                    "description": anime.description,
                    "match_score": 1.0,
                    "source": "database",
                })
        if matched_franchise_ids:
            franchise_entries = Anime.objects.filter(
                franchise_id__in=matched_franchise_ids
            ).select_related("franchise").order_by("franchise__id", "franchise_order", "-score")
            for anime in franchise_entries:
                if anime.id in seen_ids:
                    continue
                if len(results) >= limit:
                    break
                seen_ids.add(anime.id)
                poster_url = (
                    anime.poster_image_url
                    if hasattr(anime, "poster_image_url")
                    else anime.poster_url
                )
                results.append({
                    "id": anime.id,
                    "slug": anime.slug,
                    "title_ru": anime.title_ru or "",
                    "title_en": anime.title_en or "",
                    "title_jp": anime.title_jp or "",
                    "year": anime.year,
                    "status": anime.status,
                    "kind": anime.kind,
                    "episodes": anime.episodes,
                    "score": anime.score,
                    "poster_url": poster_url,
                    "description": anime.description,
                    "match_score": 1.0,
                    "source": "database",
                })
        if len(results) < limit:
            franchise_qs = Franchise.objects.all()
            if search_words:
                franchise_qs = franchise_qs.filter(
                    name__icontains=query_normalized
                )
            elif len(query_compact) >= 2:
                franchise_qs = franchise_qs.filter(
                    name__icontains=query_compact
                )
            for franchise in franchise_qs[:10]:
                if franchise.id in matched_franchise_ids:
                    continue
                franchise_entries = Anime.objects.filter(
                    franchise=franchise
                ).order_by("franchise_order", "-score")
                added = 0
                for anime in franchise_entries:
                    if anime.id in seen_ids:
                        continue
                    if len(results) >= limit:
                        break
                    seen_ids.add(anime.id)
                    poster_url = (
                        anime.poster_image_url
                        if hasattr(anime, "poster_image_url")
                        else anime.poster_url
                    )
                    results.append({
                        "id": anime.id,
                        "slug": anime.slug,
                        "title_ru": anime.title_ru or "",
                        "title_en": anime.title_en or "",
                        "title_jp": anime.title_jp or "",
                        "year": anime.year,
                        "status": anime.status,
                        "kind": anime.kind,
                        "episodes": anime.episodes,
                        "score": anime.score,
                        "poster_url": poster_url,
                        "description": anime.description,
                        "match_score": 1.0,
                        "source": "database",
                    })
                    added += 1
                if added:
                    matched_franchise_ids.add(franchise.id)
        logger.debug("fuzzy_search_anime returned %d results", len(results))
        return results
    except Exception:
        logger.exception("Error in fuzzy_search_anime")
        return []


def split_param(value: str) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]
