---
id: F0020
title: Ограничения GC файлов чата
status: active
date: '2026-10-11'
tags:
- data-integrity
- media
kind: environmental
governed-by: D0004
---

gc_chat_files по умолчанию dry-run: возраст 24 ч, limit 100; требует возраст >=24 ч и limit 1..1000. Apply/restore требуют --writers-stopped, который сам не останавливает писателей. Реализация переносит файлы в карантин с проверкой ссылок/путей и поддерживает restore.

Источники: `backend/apps/social/management/commands/gc_chat_files.py`, `backend/apps/social/application/chat_file_gc.py`, `backend/apps/social/application/test_chat_file_gc.py`, `docs/CHAT_SYSTEM_REBUILD_STATUS.md` → «Обслуживание файлов».
