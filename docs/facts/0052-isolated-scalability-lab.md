---
id: F0052
title: Добавлен изолированный production-build стенд и ограниченная telemetry
status: active
date: '2026-10-29'
tags: [performance, verification, environment]
kind: implementation
governed-by: D0033
---

`deploy/scalability/compose.yml` собирает production frontend и две Daphne-реплики, отдельные MySQL, cache/realtime/broker Redis и HTTP-генератор. Lab settings/seed проверяют точные host/schema; рабочие `.env` и volumes не монтируются. Генератор ограничивает concurrency/память, считает p95/p99 и scheduler delay, проверяет disposable identity. Его публичный HTTP smoke не измеряет active users/WS. Метрики и снимок outbox: `core/telemetry.py`, `manage.py scalability_snapshot`. Приёмка и ограничения: `docs/SCALABILITY_PROGRESS.md`, профили: `docs/SCALABILITY_WORKLOADS.md`.

Синтетические bound sessions/room IDs хранятся только в lab volume. Mixed probe проверяет unique deliveries/ACK и другую комнату; host collector сохраняет Git/source/image fingerprints, Docker resources, DB/outbox и broker ready/unacked без Config.Env. `restore_probe.py` восстанавливает dump только в новую lab schema; проверка counts/checksums не является RPO/RTO production.
