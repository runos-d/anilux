---
id: F0028
title: Подсказки рекомендаций описывают конкретный тайтл и причину отбора
status: active
date: '2026-10-12'
tags: [catalog, frontend]
kind: environmental
governed-by: D0021
---

build формирует текст и reason_details по рейтингу, году, числу серий/частей или совпавшим жанрам, source_anime_id для персонализации. Снимки версии до algorithm_version=2 не выдаются. RecommendationCard показывает Teleport-подсказку по вопросу с hover/focus/tap и закрытием через Escape, blur, повторное или внешнее нажатие. Размер ограничен экраном, другие верхние бейджи сдвинуты; действия карточки сохранены.

Источники: `backend/apps/anime/application/recommendations.py`, `frontend/src/components/Cards/RecommendationCard.vue`, `RecommendationCard.test.ts`, `frontend/tests/calendar-recommendations-browser.js`.
