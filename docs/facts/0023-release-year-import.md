---
id: F0023
title: Год тайтла берётся из даты премьеры и сохраняется при обновлении дампа
status: active
date: '2026-10-12'
tags: [catalog, data-integrity, verification]
kind: environmental
governed-by: TBD
---

release_year предпочитает aired_at, затем год записи, anime_year и общий material_data.year. Массовое обновление включает year, сохраняет прежний год при обновлении других полей и обновляет агрегаты франшизы. repair_anime_years исправляет доказанные значения старого импортёра с отдельным журналом before/after. На локальном выпуске исправлены 987 записей, включая shikimori_id=61469: 2012 → 2026.

Источники: backend/apps/anime/application/release_year.py, kodik_dump_service.py, test_catalog_integrity.py; backend/apps/anime/management/commands/repair_anime_years.py; docs/CATALOG_FEED_FIXES_2026-10-12.md.
