---
id: D0033
title: Ограниченные технические метрики включаются отдельно от продуктовой аналитики
status: active
date: '2026-10-29'
tags: [performance, verification, access-control]
track: platform
---

Transport telemetry включается env-флагом, process-local histogram имеет конечные domain/status labels, private scrape требует bearer token. Семплированные логи содержат trace ID, время и размер, без URL/параметров, пользователя, сессии или payload. Флаг удалённого sampling не увеличивает сбор. Каждый процесс scrape-ится отдельно. Это техническая наблюдаемость; согласие на продуктовую аналитику и D0031 не меняются. Корреляция transport ещё не является полной OTel-трассой команды/SQL/outbox/доставки.
