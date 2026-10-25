---
id: F0004
title: Объявленное расписание фоновых задач
status: active
date: '2026-10-11'
tags:
- integrations
- catalog
- realtime
kind: environmental
governed-by: D0017
---

В Celery beat каталог Kodik назначен на минуты 24,54, календарь - 12,42. Также объявлены синхронизация франшиз Shikimori (90 с), прогрев каталога (120 с), GC постов (3600 с), outbox постов/чатов (5 с), recovery post media/backups (60 с), рекомендации (15 с), scheduled chat messages (10 с) и cleanup bans/restrictions/invites (60 с).

Источники: `backend/config/celery.py`.
