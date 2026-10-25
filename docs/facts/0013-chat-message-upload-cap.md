---
id: F0013
title: Реализованный бюджет файлов сообщения
status: active
date: '2026-10-11'
tags:
- chats
- media
kind: decision
governed-by: D0012
---

Frontend MAX_MESSAGE_FILE_BYTES и backend conversations используют 250 × 1024 × 1024 байт; сервер прибавляет существующие файлы. Отчёт интерфейса указывает nginx 260 МБ для тела запроса.

Источники: `frontend/src/lib/chatUploadLimits.ts`, `backend/apps/social/application/conversations.py`, `frontend/nginx.conf`, `docs/CHAT_UI_FIXES_2026-10-11.md`.
