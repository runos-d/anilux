---
id: F0056
title: Добавлены отдельные task routes и изолированные прототипы RabbitMQ и Centrifugo
status: active
date: '2026-10-29'
tags: [realtime, performance, verification, release]
kind: implementation
governed-by: D0034
---

`core/task_topology.py`, `bounded_tasks.py` и worker override отделяют события от тяжёлых задач; legacy — default. RabbitMQ lab проверяет confirmations/countdown/outbox recovery/duplicate task; Centrifugo lab — только synthetic transport с официальным SDK. Защищённая доставка остаётся Channels. Настройка, ограничения и откат: `deploy/scalability/BROKERS.md`. Capacity/HA/security equivalence не подтверждены.
