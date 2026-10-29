---
id: D0033
title: Ограниченные технические метрики включаются отдельно от продуктовой аналитики
status: active
date: '2026-10-29'
tags: [performance, verification, access-control]
track: platform
---

Transport telemetry включается env-флагом, process-local histogram имеет конечные domain/status labels, private scrape требует bearer token. Семплированные логи содержат trace ID, время и размер, без URL/параметров, пользователя, сессии или payload. Флаг удалённого sampling не увеличивает сбор. Каждый процесс scrape-ится отдельно. Это техническая наблюдаемость; согласие на продуктовую аналитику и D0031 не меняются. Корреляция transport ещё не является полной OTel-трассой команды/SQL/outbox/доставки.

SQL wrapper сохраняет только count/duration/errors, без текста/params; один wrapper на переоткрываемый connection object. WS batch observation имеет конечные session/ACL/projection labels и не переиспользует решения между проверками. Outbox phase logs различают публикацию в transport и клиентскую доставку.

Post-publication histogram разделяет transport/consumer wait, batch wait, executor, connection setup, SQL, DTO preparation, serialization и ASGI send. Только фиксированные labels, без IDs/payload; внутренний timestamp не отправляется клиенту. Вложенные spans не суммируются; wall-clock между hosts требует синхронизации. Client latency остаётся отдельным критерием.

Command work включает execute, DB transaction и on-commit producer; SQL/connection имеют фиксированный command label. Generator публикует отдельный ACK histogram, чтобы не приписывать pre-publication хвост reader-у. Неуспешные end-to-end эксперименты сохраняются даже при улучшении SQL microprobe; неподтверждённые reader изменения откатываются.
