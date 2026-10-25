---
id: F0011
title: README отстаёт от тестов и запуска
status: active
date: '2026-10-11'
tags:
- documentation
- verification
- release
kind: environmental
governed-by: TBD
---

README заявляет отсутствие backend/frontend тестов и ручные миграции. Дерево содержит тесты (F0007), отдельный migrate/preflight (F0006) и расширенный локальный Compose (F0003); список сервисов README также внутренне противоречив («4» при пяти строках).

Источники: `README.md` → «Запуск», «Команды фронтенда», «Проверка / линт»; F0003, F0006, F0007.
