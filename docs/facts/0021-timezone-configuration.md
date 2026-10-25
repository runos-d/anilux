---
id: F0021
title: Текущая конфигурация времени и непроверенный intent
status: active
date: '2026-10-11'
tags:
- notifications
- environment
kind: environmental
governed-by: D0015
---

settings объявляет TIME_ZONE="Europe/Moscow" и USE_TZ=True. NOTIF_REPORT_FINAL предлагает UTC для хранения напоминаний и явно оставляет проверку beat открытой; bootstrap не проверял хранение расписания в БД или фактический worker timezone.

Источники: `backend/config/settings.py`, `NOTIF_REPORT_FINAL.md`.

Календарь после доработки 12 октября хранит aware datetime в CalendarRelease и группирует API-выдачу в IANA-поясе устройства. Это проверено переходом 30 сентября/1 октября для America/Los_Angeles и Europe/Moscow; проверка timezone worker напоминаний этим не закрывается. См. F0026.

Во втором задании проверены обработчик Celery и API напоминаний с aware datetime, локальное отображение и недельный повтор America/Los_Angeles через DST (25 октября 03:30 PDT → 1 ноября 03:30 PST). Недельный/пользовательский интервал используют timezone_name; старые напоминания сохраняют UTC-интервал по умолчанию. Beat-задача 60 с объявлена, работа production worker/beat после выкатки ещё не подтверждена. См. F0031.
