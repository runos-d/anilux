import os
import sys
import django
import time
from datetime import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.anime.infrastructure.models.anime import Anime, Genre, Studio
from apps.anime.infrastructure.clients.kodik_config import normalize_kodik_player_link
from apps.anime.infrastructure.api.external_anime_api import external_anime_api


class Command(BaseCommand):
    help = 'Импорт новых аниме из Kodik API'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100, help='Количество аниме для проверки')
        parser.add_argument('--days', type=int, default=7, help='За сколько дней брать обновления')

    def handle(self, *args, **options):
        limit = options['limit']
        days = options['days']

        self.stdout.write(f'📥 Импорт новых аниме (лимит: {limit})...')

        page_size = 100
        pages_needed = (limit + page_size - 1) // page_size
        
        imported = 0
        updated = 0
        skipped = 0
        total_processed = 0

        try:
            params = {
                'types': 'anime-serial,anime',
                'with_material_data': True,
                'with_seasons': True,
                'with_episodes': True,
                'limit': page_size,
                'sort': 'updated_at',
                'order': 'desc'
            }

            data = external_anime_api.list_materials(**params)

            while data.get('results') and total_processed < limit:
                results = data.get('results', [])
                self.stdout.write(f'Страница {total_processed // page_size + 1}, результатов: {len(results)}')

                for item in results:
                    if total_processed >= limit:
                        break
                    
                    shikimori_id = item.get('shikimori_id')
                    if not shikimori_id:
                        skipped += 1
                        continue

                    existing = Anime.objects.filter(shikimori_id=shikimori_id).first()

                    if existing:
                        self._update_anime(existing, item)
                        updated += 1
                    else:
                        self._create_anime(item)
                        imported += 1

                    total_processed += 1
                    time.sleep(0.05)  

                next_page = data.get('next_page')
                if not next_page or total_processed >= limit:
                    break
                
                data = external_anime_api.list_materials(next_page)

            self.stdout.write(self.style.SUCCESS(
                f'✅ Готово! Создано: {imported}, Обновлено: {updated}, Пропущено: {skipped}'
            ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка: {e}'))

    def _map_status(self, status: str) -> str:
        status_map = {
            'anons': 'announced',
            'ongoing': 'ongoing',
            'released': 'finished',
            'discontinued': 'canceled'
        }
        return status_map.get(status, 'finished')

    def _map_kind(self, kind: str) -> str:
        kind_map = {
            'tv': 'tv', 'tv_13': 'tv', 'tv_24': 'tv', 'tv_48': 'tv',
            'movie': 'movie', 'ova': 'ova', 'ona': 'ona',
            'special': 'special', 'music': 'music'
        }
        return kind_map.get(kind, 'tv')

    def _get_episodes_count(self, result: dict) -> int:
        episodes_count = result.get('episodes_count') or 0
        last_episode = result.get('last_episode') or 0
        return max(episodes_count, last_episode) if last_episode else (episodes_count or 1)

    def _get_duration(self, result: dict) -> int:
        material_data = result.get('material_data', {})
        duration = material_data.get('duration')
        if duration:
            return int(duration)
        
        return 24

    def _create_anime(self, result: dict):
        material_data = result.get('material_data', {})

        genre_names = material_data.get('anime_genres') or material_data.get('genres') or []
        
        studio_names = material_data.get('anime_studios') or []

        poster_url = material_data.get('anime_poster_url') or material_data.get('poster_url') or ''

        screenshots = material_data.get('screenshots') or result.get('screenshots') or []

        score = material_data.get('shikimori_rating') or material_data.get('kinopoisk_rating') or 0.0

        description = material_data.get('anime_description') or material_data.get('description') or ''

        episodes_count = self._get_episodes_count(result)
        episode_duration = self._get_duration(result)

        raw_status = material_data.get('anime_status', '')
        status = self._map_status(raw_status) if raw_status else 'announced'  

        try:
            anime = Anime.objects.create(
                title_ru=result.get('title', ''),
                title_en=result.get('title_orig', ''),
                title_jp=result.get('other_title', ''),
                description=description,
                year=result.get('year'),
                status=status,
                kind=self._map_kind(material_data.get('anime_kind') or result.get('type', 'tv')),
                episodes=episodes_count,
                progress_total=episodes_count,
                episode_duration=episode_duration,
                score=score,
                poster_url=poster_url,
                genres=genre_names,
                studios=studio_names,
                data_source='kodik',
                shikimori_id=result.get('shikimori_id'),
                screenshots=screenshots,
                kodik_link=normalize_kodik_player_link(result.get('link', '')),
                kodik_id=result.get('id', ''),
                quality=result.get('quality', ''),
            )
            self.stdout.write(f'  ✅ Создано: {result.get("title")} [{status}]')
            from apps.anime.application.episode_availability import record_availability
            record_availability(anime, result)
        except Exception as e:
            self.stdout.write(f'  ❌ Ошибка создания {result.get("title")}: {e}')

    def _update_anime(self, anime: Anime, result: dict):
        from apps.anime.application.episode_availability import record_availability
        record_availability(anime, result)
        material_data = result.get('material_data', {})

        updated = False

        new_episodes = self._get_episodes_count(result)
        if anime.episodes != new_episodes and new_episodes > (anime.episodes or 0):
            anime.episodes = new_episodes
            updated = True
        if new_episodes > (anime.progress_total or 0):
            anime.progress_total = new_episodes
            updated = True

        new_duration = self._get_duration(result)
        if anime.episode_duration != new_duration:
            anime.episode_duration = new_duration
            updated = True

        raw_status = material_data.get('anime_status', '')
        new_status = self._map_status(raw_status) if raw_status else None
        
        if new_status and anime.status != new_status:
            if anime.status == 'announced' and new_status in ('finished', 'released'):
                self.stdout.write(f'  ⏭️ Пропущен статус (анонс): {anime.title_ru}')
            else:
                anime.status = new_status
                updated = True

        new_score = material_data.get('shikimori_rating') or material_data.get('kinopoisk_rating') or 0.0
        if anime.score != new_score and new_score > 0:
            anime.score = new_score
            updated = True

        if updated:
            anime.updated_at = timezone.now()
            anime.save()
            self.stdout.write(f'  🔄 Обновлено: {anime.title_ru}')
