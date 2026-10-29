---
id: F0047
title: Аналитика работает только после согласия, а данные аккаунта имеют единый lifecycle
status: active
date: '2026-10-27'
tags: [frontend, integrations, api-contracts, access-control, data-integrity, verification, documentation]
kind: implementation
governed-by: D0030
---

Frontend использует единый типизированный analytics API с no-op по умолчанию, версионированным согласием, default-deny sanitizer, безопасными route templates и изолированными Yandex/Google adapters. Provider scripts не создаются до `granted`, а архитектурная CI-проверка запрещает прямые provider API вне adapters. Backend хранит consent через `/api/users/privacy-settings/me/`, формирует owner-only ZIP exports с TTL и выполняет удаление аккаунта одним идемпотентным cleanup, охватывающим БД, sessions, refresh tokens, push и physical files.

Проверка: `npm run type-check`; `npm run check:analytics-architecture`; `npx vitest run src/analytics`; `python manage.py check`; `python manage.py makemigrations --check --dry-run`; `python manage.py test apps.users.test_privacy_data_management --keepdb`.
