---
id: F0029
title: Доступность серий отделена от планового числа серий
status: active
date: '2026-10-12'
tags: [catalog, integrations, data-integrity]
kind: environmental
governed-by: D0022
---

KodikAvailability хранит подтверждённые номера и последний доступный номер. Импорт использует эпизоды с URL/last_episode и ссылку Kodik, не episodes_total/episodes_aired. Частичное наблюдение объединяется с последним удачным; успешный полный дамп заменяет текущую доступность и обрабатывает исчезновение. Ошибки источника не обновляют доступность из старых файлов.

UserLibrary хранит исходный набор доступных серий и watched_through для старого/ручного прогресса; UserEpisodeProgress уточняет номера и пропуски. Новые непросмотренные серии переводят completed в started. GET /api/anime/home/ возвращает случайно перемешанные new_episodes только владельцу; карточки содержат latest_episode, unwatched_count и next_episode. Ответ всегда private/no-store с Vary Authorization/Cookie, клиент меняет версию запроса.

Источники: `backend/apps/anime/application/episode_availability.py`, `kodik_dump_service.py`, `backend/apps/users/application/library_episodes.py`, `backend/apps/anime/presentation/views/anime_views.py`, `frontend/src/components/page/other/HomeView.vue`.
