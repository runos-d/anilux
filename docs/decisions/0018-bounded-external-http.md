---
id: D0018
title: Внешние HTTP-запросы имеют явные таймауты
status: draft
date: '2026-10-11'
tags:
- integrations
- verification
track: process
---

Мотивация: Ограничивать ожидание SMS и Google OAuth, чтобы внешние сервисы не удерживали серверный запрос без предела.

Источники: git `e8e0853` (2026-10-07): external HTTP timeouts; `backend/apps/users/presentation/views/users_views.py`.

<!-- looks like a decision, could be a behavioral rule -classify before finalizing -->
