---
id: D0005
title: Общие транзакционные команды и долговечные события
status: draft
date: '2026-10-11'
tags:
- chats
- posts
- realtime
- data-integrity
track: process
---

Мотивация: Согласовывать REST, WS и worker через общую policy/service, идемпотентные ключи, версии и outbox в одной транзакции.

Источники: `docs/CHAT_SYSTEM_REBUILD_PLAN.md` → «Целевая архитектура», этапы 3–6; `docs/POST_SYSTEM_REBUILD_PLAN.md` → «Правила новой реализации», пп. 4, 7.
