---
id: D0031
title: Пакетировать текущие WS-проверки без кеширования решений доступа
status: active
date: '2026-10-29'
tags: [realtime, access-control, performance, api-contracts]
track: platform
---

Concurrent WS authorization, read ACL и plain-message projections объединяются в bounded batches, после завершения результат не переиспользуется следующим batch. Session revocation, expiry, active account, membership/bans и bounds видимости проверяются по текущему состоянию БД. Viewer-free метаданные сериализатора можно переиспользовать; пользовательские payload и решения доступа в этот cache не входят. Rich-message reader сохраняет персональные проверки. Это уменьшает SQL fanout без stale-authorization TTL и поддерживает немедленный отзыв сессии при следующем действии/доставке. Реализация: `core/socket_auth.py`, `apps/social/application/live_projection.py`; privacy/equivalence/revocation regression tests обязательны при изменении reader.

Самостоятельные `authorize_chat`, `snapshot`, `execute` и отдельные global readers работают через `database_sync_to_async(thread_sensitive=False)` в ограниченном default executor. В callback передаются model instances/IDs, но не открытые DB connections/cursors. Каждая операция открывает connection в своём потоке и закрывает через Channels wrapper; транзакции не пересекают async boundary. Поэтому медленная история одной комнаты не блокирует остальные комнаты через глобальный single-thread executor. DB locks одной беседы и штатный Channels dispatch сохранены. `test_consumer_isolation.py` проверяет независимое завершение snapshot второй комнаты, пока reader первой специально заблокирован.

Членство transport groups не является авторизацией. Redis группы по умолчанию истекают через 300 с (`WS_GROUP_EXPIRY`, минимум 120 с), вместо суток; аутентифицированный heartbeat раз в примерно 90–100 с продлевает только текущие подписки через bounded pipelines. Он обрабатывается в той же очереди consumer, что subscribe/unsubscribe, чтобы renewal не возвращал уже удалённую подписку. Ошибка renewal требует reconnect. Пакетный fanout проверяет живые Redis group entries без TTL cache и пропускает пустые/истёкшие группы; непустые отправляет штатным `group_send` с его capacity/expiry правилами. История/outbox/replay остаются источником восстановления.
