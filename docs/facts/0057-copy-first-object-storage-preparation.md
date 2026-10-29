---
id: F0057
title: Миграция в S3 подготавливает проверенную копию без переключения live paths
status: active
date: '2026-10-29'
tags: [media, data-integrity, verification, release]
kind: implementation
governed-by: D0004
---

`mirror_media_file` по умолчанию только хеширует локальный файл. `--apply` требует private manifest вне checkout, копирует content-addressed объект и проверяет реальные удалённые байты; источник сохраняется. Optional SDK установлен только отдельным migration image/lock. Mock tests и build не подтверждают совместимость провайдера, CDN или live S3 cutover. Процедура/границы: `deploy/scalability/OBJECT_STORAGE.md`.
