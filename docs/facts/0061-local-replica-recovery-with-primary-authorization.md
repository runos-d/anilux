---
id: F0061
title: Локальная реплика MySQL проверена без переключения API
status: active
date: '2026-10-29'
tags: [data-integrity, environment, access-control, verification]
kind: implementation
governed-by: D0004
---

`compose.replica.yml`/`replica_probe.py` создают новую пустую копию lab по согласованному binlog checkpoint; существующие schema/volumes не очищаются. Counts/checksums шести таблиц совпали, paused applier/catch-up/restart и отказ записи в persisted super-read-only прошли. Повторный bootstrap непустой schema отклонён. Backup SQL остаётся ignored; API/WS/session/ACL читают primary по D0031. Это одна локальная replica, без writer promotion/host HA/production CA identity. Процедура/границы: `deploy/scalability/REPLICATION.md`; evidence — `docs/reviews/2026-10-29-scalability-continuation-evidence/replication/`.
