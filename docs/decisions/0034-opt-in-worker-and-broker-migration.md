---
id: D0034
title: Разделение workers и смена брокера включаются независимо с дренированием
status: active
date: '2026-10-29'
tags: [realtime, release, data-integrity, verification]
track: platform
---

Legacy Celery routing остаётся default. Isolated profile требует готовых consumers до переключения producers; RabbitMQ quorum — отдельный opt-in с provisioned queues, confirms, publish deadlines, bounded overflow и DLQ policy. Late ACK разрешён только проверенным идемпотентным задачам. Откат не очищает брокер: старые/новые consumers сохраняются до дренирования. Centrifugo не получает защищённые события до доказательства D0031 и replay. Одноузловой lab не подтверждает broker HA.
