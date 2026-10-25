---
id: F0009
title: Реализация постов опережает план
status: active
date: '2026-10-11'
tags:
- posts
- realtime
- documentation
kind: environmental
governed-by: D0005
---

Рабочее дерево содержит post_commands с транзакциями/Conflict 409, PostCommand/PostEvent/PostUpload, post_access, защищённые media services и test_post_transport/test_site_rebuild. POST_SYSTEM_REBUILD_PLAN всё ещё относит эти области к предстоящей работе; наличие кода не доказывает полную приёмку.

Источники: `backend/apps/social/application/post_commands.py`, `backend/apps/social/infrastructure/models/post_lifecycle.py`, `backend/apps/social/application/post_access.py`, `backend/apps/social/application/test_post_transport.py`, `backend/apps/social/application/test_site_rebuild.py`, `docs/POST_SYSTEM_REBUILD_PLAN.md`.
