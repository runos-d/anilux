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

`npm run build` параллельно выполняет type-check и build-only. type-check — vue-tsc --build; build-only — Vite; test:unit:run — Vitest без visual tests. lint выполняет проверку без исправлений; lint:fix явно включает --fix. Dockerfile запускает npm ci и build.

Источники: `frontend/package.json`, `frontend/Dockerfile`.
