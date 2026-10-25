---
id: D0015
title: 'Напоминания: UTC в БД и локальное время в интерфейсе'
status: draft
date: '2026-10-11'
tags:
- notifications
- environment
track: process
expires: После проверки расписания напоминаний и сопоставления с текущим TIME_ZONE/USE_TZ
---

Мотивация: Согласовывать хранение и отображение расписания, проверяя реальную работу Celery beat с USE_TZ.

Источники: `NOTIF_REPORT_FINAL.md` → «Не проверено», п. о часовом поясе.

<!-- looks like a decision, could be a behavioral rule -classify before finalizing -->
