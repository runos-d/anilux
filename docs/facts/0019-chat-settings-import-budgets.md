---
id: F0019
title: Бюджеты импорта настроек чата
status: active
date: '2026-10-11'
tags:
- chats
- media
kind: environmental
governed-by: TBD
---

settings_transfer использует default 32 MiB для JSON (может переопределяться CHAT_SETTINGS_IMPORT_MAX_BYTES), 5 MiB на изображение и 20 MiB на набор изображений; проверяет весь набор перед применением.

Источники: `backend/apps/social/application/settings_transfer.py`, `docs/CHAT_SYSTEM_REBUILD_STATUS.md` → «Реализовано».
