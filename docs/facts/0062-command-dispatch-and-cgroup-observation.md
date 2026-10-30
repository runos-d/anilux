---
id: F0062
title: Command telemetry разделяет dispatch и транзакцию с внешними cgroup counters
status: active
date: '2026-10-30'
tags: [realtime, performance, verification]
kind: implementation
governed-by: D0033
---

ASGI timestamp измеряет incoming dispatch wait без изменения native Channels dispatch. Command intervals: current authorization, executor, sync work, transaction/commit, broker publication и ACK send; SQL/connection вложены. Один loop callback наблюдает scheduling lag. Host helper читает local Docker Engine cgroup counters только lab containers, без исполнения probes в API; generator сохраняет до 1800 command timeline aggregates без payload/credentials. Это измерения, не доказанная причина latency или capacity. Границы/повторение: `deploy/scalability/README.md`.
