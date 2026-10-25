---
id: F0025
title: Фотографии постов обрабатываются отдельно от очереди конвертации видео
status: active
date: '2026-10-12'
tags: [posts, media, performance]
kind: environmental
governed-by: TBD
---

queue_media направляет изображения в celery, а видео в post_media. Локальный выпуск имеет обычный worker с concurrency=2 и отдельный worker post_media с concurrency=1. Поэтому фотографии не обязаны ждать завершения конвертации видео в post_media.

Источники: backend/apps/social/application/post_media.py, post_commands.py, test_oct12_fixes.py; docker-compose.yml; docker-compose.production.yml.
