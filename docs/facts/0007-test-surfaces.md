---
id: F0007
title: Существующие уровни проверки
status: active
date: '2026-10-11'
tags:
- verification
- build
kind: environmental
governed-by: D0009
---

Есть Django unit/regression/migration/transport-наборы users/social/anime, Vitest-тесты клиента, компонентов и библиотек, browser-сценарии frontend/tests и scripts/profile_local_chats.mjs. Unit-настройки чатов задают отдельную MySQL и in-memory broker/cache; transport-настройки предназначены для настоящих Redis/Celery/Channels. CI задан в .github/workflows/release-hardening.yml: frontend проверки/тесты, backend проверки/тесты с MySQL/Redis и сборка контейнеров.

Источники: `backend/apps/*/`, `backend/config/settings_chat_test.py`, `backend/config/settings_chat_integration.py`, `frontend/src/**/*.test.ts`, `frontend/tests/`, `scripts/profile_local_chats.mjs`.
