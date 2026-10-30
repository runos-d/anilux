---
id: F0063
title: Физический storage inventory потоковый и сохраняет приватные имена вне checkout
status: active
date: '2026-10-30'
tags: [media, data-integrity, verification]
kind: implementation
governed-by: D0004
---

`inventory_storage_tree` обходит public/chat/post/downloads trees без SQL/сети и изменений источников. Private JSONL включает files без ORM-ссылок, явный partial footer, budgets entries/time/depth/hash; Linux directory descriptors не следуют symlink. Это наблюдаемый tree, не согласованный snapshot, классификация JSON/ACL или reconciliation. `complete_storage_inventory=false`; dual-write/live S3 migration остаются открыты. Процедура: `deploy/scalability/OBJECT_STORAGE.md`.
