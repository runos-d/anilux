---
id: F0010
title: Приватные ответы исключены из PWA-кэша
status: active
date: '2026-10-11'
tags:
- media
- access-control
kind: environmental
governed-by: D0007
---

privateMediaCache описывает исключения API/media/старых приватных URL; тесты проверяют также encoded paths и сохранение кэширования публичных аватарок. Service worker применяет эти правила; nginx содержит защищённые пути выдачи. Это статическая проверка реализации.

Источники: `frontend/src/lib/privateMediaCache.ts`, `frontend/src/lib/privateMediaCache.test.ts`, `frontend/src/sw.ts`, `frontend/nginx.conf`.
