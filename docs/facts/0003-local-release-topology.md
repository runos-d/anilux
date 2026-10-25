---
id: F0003
title: Порты и тома локального выпуска
status: active
date: '2026-10-11'
tags:
- release
- environment
kind: environmental
governed-by: D0008
---

С production override frontend опубликован на 127.0.0.1:8080, backend на 127.0.0.1:8000; базовый Compose публикует MySQL 3307 и Redis 6379 на loopback. Код поставляется образами, данные - backend/data; frontend получает read-only каталоги post media. Override добавляет отдельный post_media_worker.

Источники: `docker-compose.yml`, `docker-compose.production.yml`.
