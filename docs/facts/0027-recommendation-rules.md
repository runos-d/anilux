---
id: F0027
title: Односерийные фильмы проверяются во всех путях рекомендаций
status: active
date: '2026-10-12'
tags:
- catalog
- frontend
- api-contracts
kind: environmental
governed-by: D0020
---

Основной build и legacy _get_movies_high_rated требуют movie/episodes=1. read проверяет фильмы сохранённой подборки по актуальной Anime, сохраняя исключения коллекции. algorithm_version=2 и новый ключ кэша исключают старые снимки; первое чтение несовместимого снимка строит ограниченную подборку и ставит обновление в очередь. Клиент также изменяет версию query key и фильтрует movie/episodes=1.

Источники: `backend/apps/anime/application/recommendations.py`, `backend/apps/anime/migrations/0010_recommendation_algorithm_version.py`, `frontend/src/components/page/anime/RecommendationsView.vue`, `backend/apps/anime/presentation/views/anime_views.py`.
