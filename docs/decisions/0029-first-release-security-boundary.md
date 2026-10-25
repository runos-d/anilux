---
id: D0029
title: Первая версия закрывает необязательные модули и использует email-only auth
status: active
date: '2026-10-19'
tags:
- release
- access-control
- api-contracts
track: product
---

Первая версия по умолчанию не публикует dubs, Reactor, 2FA, studio sync и реакции обсуждений студий. Вход, регистрация, подтверждение и восстановление используют email; телефонные поля остаются только для совместимости сохранённых данных. Серверная граница обязательна: клиентские флаги не считаются контролем доступа.

Источники: `FIRST_RELEASE_HARDENING_PLAN.md`; `backend/config/feature_flags.py`; `backend/config/urls.py`; `backend/apps/users/presentation/urls.py`; `frontend/src/config/features.ts`; `frontend/src/router/index.ts`.
