---
id: F0048
title: JWT отзывается вместе с серверной сессией
status: active
date: '2026-10-28'
tags: [access-control, realtime, verification]
kind: implementation
governed-by: D0029
---

Login, Google exchange и token endpoint выдают JWT с непрозрачным ActiveSession ID. HTTP, refresh и активные WebSocket проверяют серверную сессию; legacy JWT отзываются через User.token_version. Миграция users.0014 вводит token_version. Регрессии: apps.users.test_review_regressions.
