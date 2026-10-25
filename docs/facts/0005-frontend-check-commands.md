---
id: F0005
title: Скрипты проверки фронтенда
status: active
date: '2026-10-11'
tags:
- build
- verification
kind: environmental
governed-by: TBD
---

`npm run build` параллельно запускает type-check и build-only; type-check - vue-tsc --build, build-only - vite build, test:unit - vitest, lint - eslint . --fix --cache. Frontend Dockerfile выполняет npm ci и npm run build. Команда lint изменяет файлы.

Источники: `frontend/package.json`, `frontend/Dockerfile`.
