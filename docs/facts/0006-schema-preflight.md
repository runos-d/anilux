---
id: F0006
title: Миграции и schema preflight перед запуском
status: active
date: '2026-10-11'
tags:
- data-integrity
- release
kind: environmental
governed-by: D0004
---

Compose ставит успешное завершение migrate условием запуска backend/worker/beat. docker_entrypoint вызывает check_chat_schema и check_project_schema перед Daphne/Celery, затем execvp; не запускает сервер при неуспешной проверке.

Источники: `docker-compose.yml`, `backend/docker_entrypoint.py`, `backend/core/project_schema.py`, `backend/apps/social/application/test_chat_startup.py`.
