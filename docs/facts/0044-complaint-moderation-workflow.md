---
id: F0044
title: Жалоба сохраняет доказательства и применяет единое решение модерации
status: active
date: '2026-10-20'
tags:
- posts
- notifications
- data-integrity
- frontend
- verification
kind: implementation
governed-by: D0004
---

Пользовательские `Report` и административные `Complaint` связаны идентификатором; при отправке сохраняется снимок текста, автора, ссылки и метаданных вложений. Оба административных интерфейса показывают структурированные данные жалобщика и цели (автор, заголовок, полный текст, рабочая ссылка, доступность и медиа) и применяют один транзакционный сценарий: отклонение, предупреждение, удаление контента или восстанавливаемая деактивация аккаунта. Решение синхронизируется с `Report`; жалобщик и затронутый пользователь получают внутренние уведомления. Удалённый контент остаётся доступен администратору как снимок без неработающей публичной ссылки.

Проверка: `python manage.py test apps.notifications.application.test_complaints apps.social.application.test_site_rebuild.SiteRebuildTests.test_reports_deduplicate_and_cannot_retarget_private_content --keepdb`; `python manage.py makemigrations --check --dry-run`; `npm run type-check`.
