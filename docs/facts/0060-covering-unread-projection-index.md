---
id: F0060
title: Plain chat projection читает viewer IDs и использует покрывающий unread индекс
status: active
date: '2026-10-29'
tags: [chats, performance, data-integrity, verification]
kind: implementation
governed-by: D0031
---

`project_records` не загружает profile/preferences JSON зрителей обычного сообщения; rich reader получает полные текущие accounts. Миграция social.0039 добавляет индекс `(conversation,is_deleted,seq,sender,created_at)`: MySQL EXPLAIN unread подзапроса сменился с table scan/range checked на ref/Using index. Текущие права/clear/prejoin/receipts сохранены, unread остаётся точным и зависит от длины истории — асинхронная счётчиковая проекция ещё открыта.

75 privacy/session/history/delivery/projection/real Redis regressions PASS (29,775с), model drift отсутствует, миграция применена только к lab. Повтор 120/4 API/60с: chat 598/791мс, 7200/7200; p95 500мс ещё не пройден. Evidence: `docs/reviews/2026-10-29-scalability-continuation-evidence/indexed-projection/`.
