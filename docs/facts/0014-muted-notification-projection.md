---
id: F0014
title: Разделение unread и mute в уведомлениях
status: active
date: '2026-10-11'
tags:
- chats
- notifications
kind: decision
governed-by: D0013
---

Рабочее дерево содержит chat_notification_preferences и клиентскую одноимённую библиотеку/тесты; отчёт описывает исключение muted чатов из уведомлений/бейджа при сохранении непрочитанных в истории и изоляцию ответов аккаунтов.

Источники: `backend/apps/social/application/chat_notification_preferences.py`, `frontend/src/lib/chatNotificationPreferences.ts`, `frontend/src/lib/chatNotificationPreferences.test.ts`, `frontend/src/composables/useTabBadge.test.ts`, `docs/CHAT_UI_FIXES_2026-10-11.md`.
