---
id: F0008
title: Текущее ядро чатов
status: active
date: '2026-10-11'
tags:
- chats
- realtime
- api-contracts
kind: environmental
governed-by: D0005
---

В рабочем дереве существуют Conversation, ChatEvent, общий conversations service и conversation consumer; backend тестирует версии, повторы, replay и различие публичных/внутренних ID. Документ CHAT_SYSTEM_REBUILD_STATUS описывает локальную приёмку; bootstrap проверил наличие реализации, но не запускал эти сценарии.

Источники: `backend/apps/social/infrastructure/models/conversation.py`, `backend/apps/social/application/conversations.py`, `backend/apps/social/application/conversation_consumer.py`, `backend/apps/social/application/test_conversations.py`, `docs/CHAT_SYSTEM_REBUILD_STATUS.md`.
