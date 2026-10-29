---
id: F0053
title: Холодные рекомендации не пересчитывают персональную библиотеку в HTTP
status: active
date: '2026-10-29'
tags: [performance, catalog, data-integrity, verification]
kind: implementation
governed-by: D0021
---

`recommendations.read` возвращает общий fallback до подготовки персонального snapshot; dirty personal data не используется. Проверки библиотеки и текущей видимости ограничены кандидатами. Catalog invalidation увеличивает revision, чтобы старый worker не погасил dirty. `manage.py rebuild_recommendations --limit 100 --after-id N` по умолчанию dry-run; `--apply` помечает максимум 500 записей для перестроения существующим worker. Алгоритм и публичные ID сохранены. Регрессии: `test_scalability_reads.py`; результаты в scalability progress.
