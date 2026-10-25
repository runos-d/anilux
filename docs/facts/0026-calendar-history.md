---
id: F0026
title: Постоянная история календаря и миграция сохранённого снимка
status: active
date: '2026-10-12'
tags:
- catalog
- data-integrity
- api-contracts
kind: environmental
governed-by: D0019
---

CalendarRelease имеет уникальность (shikimori_id, episode); ненумерованный релиз использует episode=0. Миграция anime.0009 копирует нормализованный/старый снимок без изменения исходного JSON. sync_calendar валидирует весь массив и транзакционно объединяет его с историей, включая успешный пустой и неизменившийся дамп. CalendarSnapshot блокирует параллельное объединение и задаёт ревизию API-кэша. Ошибка загрузки/разбора не отмечает исчезновение.

GET /api/anime/calendar/ читает CalendarRelease через AnimeService.get_calendar. Поиск без month охватывает сохранённую историю. UI загружает месяцы при недельной навигации и показывает schedule_uncertain. История начинается с реально сохранённого снимка/импортов. Политика времени описана в F0021.

Источники: `backend/apps/anime/application/calendar_history.py`, `kodik_dump_service.py`, `anime_service.py`, `backend/apps/anime/presentation/views/anime_views.py`, `backend/apps/anime/migrations/0009_calendarrelease.py`, `frontend/src/api/anime.ts`, `frontend/src/components/page/anime/CalendarView.vue`.
