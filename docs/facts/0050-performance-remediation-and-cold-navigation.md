---
id: F0050
title: Исправлены узкие места повторного ревью и первая навигация Vite
status: active
date: '2026-10-29'
tags: [performance, frontend, realtime, verification, release]
kind: implementation
governed-by: TBD
---

N01–N20 закрыты ограниченными фоновыми download/import, адресными WS и presence, пакетными SQL/privacy, виртуальной лентой и keyset, устранением повторов/HTTP provider calls, отменой устаревших загрузок, readiness и cache circuit breaker. Первичная навигация localhost:5173 облегчена server.warmup, прогревом кода и отложенной загрузкой разделов/закрытых окон. Локальный API проходит через Vite на IPv4 backend, сохраняя same-origin cookies и media/WS; это убрало измеренный fallback localhost примерно на 2 с.

Проверки: 114 тестов MySQL и 269 frontend, сборка/type/lint/budget; 72 fixture-маршрута без JS ошибок/overflow; реальный локальный FFmpeg/Celery и Range/X-Accel; 100 WS и адресная доставка 30 событий; Redis pause/recovery. Четыре HTTP-реплики приняли 2000/2000 запросов при подаче 100/с, p95 около 1,5 с. Это короткая локальная проба, не гарантия production SLO или произвольной нагрузки.

Локальные миграции применены после backup и репетиции на восстановленной копии. Backend/worker/beat обновлены, выделенные очереди запущены, readiness ok. Полный журнал, ограничения и доставка: `docs/reviews/2026-10-28-performance-remediation.md`; результаты — `docs/reviews/2026-10-28-performance-evidence/`.
