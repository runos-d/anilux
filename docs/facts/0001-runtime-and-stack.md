---
id: F0001
title: Объявленный стек и ограничения runtime
status: active
date: '2026-10-11'
tags:
- environment
- build
kind: environmental
governed-by: TBD
---

Backend Docker использует Python 3.11; requirements объявляет Django >=5.2,<6.1, DRF, Channels, Daphne и Celery. Compose использует MySQL 8.0/Redis 7. Frontend - Vue 3/Vite/TypeScript; engines: Node `^20.19.0 || >=22.12.0`, build-образ Node 22. Это декларации файлов, не версии запущенных процессов.

Источники: `backend/Dockerfile`, `backend/requirements.txt`, `docker-compose.yml`, `frontend/package.json`, `frontend/Dockerfile`.
