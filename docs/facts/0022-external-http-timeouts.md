---
id: F0022
title: Явные таймауты SMS и Google OAuth
status: active
date: '2026-10-11'
tags:
- integrations
- verification
kind: environmental
governed-by: D0018
---

users_views задаёт requests timeout 10 с для SMS, 15 с для Google token и 10 с для userinfo. Изменение отражено в коммите e8e0853; это значения кода, не гарантия общей длительности запроса.

Источники: `backend/apps/users/presentation/views/users_views.py`, git `e8e0853`.
