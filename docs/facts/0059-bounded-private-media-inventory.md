---
id: F0059
title: FileField inventory ограничен keyset страницей и приватным manifest
status: active
date: '2026-10-29'
tags: [media, data-integrity, verification]
kind: implementation
governed-by: D0004
---

`inventory_media_page` описывает FileFields без SQL или сохраняет до 500 строк по PK с upper watermark. Private manifest создаётся исключительно вне checkout; stdout без имён файлов. Hash I/O 0..64MiB/page, по умолчанию stat; missing/changed/invalid/unsupported явные. Ни загрузки в S3, ни изменения live paths нет; JSON/export/download/orphan paths ещё вне inventory. Четыре MySQL/temp-files regression tests PASS. Процедура: `deploy/scalability/OBJECT_STORAGE.md`.
