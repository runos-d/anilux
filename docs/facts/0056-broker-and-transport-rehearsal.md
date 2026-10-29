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

`describe_scalability_surface` экспортирует текущие route templates/handlers и task queues без вызова БД/брокера, handlers/tasks или экспорта configuration values. Карта lab: 994 HTTP entries, 3 WS patterns, 88 application tasks, unregistered beat tasks нет. Проверка с `--network none`: legacy social notifications/FFmpeg/import/native jobs классифицированы в isolated routes; actual Celery router совпал со статической картой для всех 88 tasks, default остался только у debug/lab probe. Семь unit/config checks PASS. Это статическая карта с текущими feature flags, не функциональная/ACL приёмка всего corpus; explicit queue в caller имеет приоритет.
