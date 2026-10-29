---
id: F0058
title: Адресные события чата объединяются по текущим пользовательским группам Redis
status: active
date: '2026-10-29'
tags: [realtime, performance, access-control, verification]
kind: implementation
governed-by: D0031
---

`send_to_users`/`BoundedRedisChannelLayer.user_groups_send` читают текущие group entries пакетами до 256 пользователей и публикуют один frame на process queue. Штатный Channels receiver/dispatch, expiry/capacity и свежие session/ACL/projection checks сохранены; решения доступа не кешируются. Ограничения: 256 каналов на пользовательскую группу, 8192 в union; превышение/Redis error оставляет outbox retryable. Generic layers сохраняют прежние адресные sends. Совместимость зависит от закреплённого channels-redis 4.3; при обновлении повторять реальные transport/security tests.

На 120 users/4 API/10 HTTP+1 send в секунду/60с локальный instrumented baseline: chat p95/p99 3190/3880мс; union: 681/895мс, 7200/7200 доставок без дублей/утечек. Это короткое последовательное сравнение на общем host, не capacity certificate; цель p95 500мс ещё не пройдена. Evidence: `docs/reviews/2026-10-29-scalability-continuation-evidence/`.
