---
id: F0012
title: Реализованный срок приглашений - 24 часа
status: active
date: '2026-10-11'
tags:
- chats
- access-control
kind: decision
governed-by: D0011
---

ChatInviteLink задаёт 24 часа и effective_expires_at ограничивает старые сроки created_at + 24h; views_chat создаёт новые ссылки с этим сроком и не позволяет продление. Повторное членство и вход без заявки описаны в текущем отчёте.

Источники: `backend/apps/social/infrastructure/models/social_chat.py`, `backend/apps/social/presentation/views/views_chat.py`, `docs/CHAT_UI_FIXES_2026-10-11.md`.
