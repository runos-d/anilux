---
id: F0030
title: Автоподписка и сохранение прогресса при удалении из коллекции
status: active
date: '2026-10-12'
tags: [notifications, catalog, data-integrity]
kind: environmental
governed-by: D0023
---

post_save UserLibrary включает EpisodeSubscription только при новом членстве. Обычные saves не включают ручную отписку. pre_delete сохраняет поля прогресса в UserLibraryArchive и отключает подписку; каскад удаления пользователя/аниме архив не создаёт. Последующий просмотр сохраняет UserEpisodeProgress и архив без восстановления членства. Повторное добавление восстанавливает прогресс и включает подписку.

EpisodeNotice имеет уникальный ключ пользователь/тайтл/серия/фаза и переживает удаление уведомления. Cursor/набор известных номеров и блокировки предотвращают повторные/параллельные доставки. API подписок использует ID подписки, владельца, умеет читать и включать неактивную запись; диалог исправлен для этого контракта.

Миграция notifications.0007 переносит доказанную доступность из raw_kodik_data, сохраняет прежние поля прогресса и явные отключения, добавляет недостающие подписки. Первый неизвестный исторический импорт становится базой, а не вымышленным новым выходом.

Источники: `backend/apps/users/application/library_episodes.py`, `backend/apps/notifications/application/episode_events.py`, `backend/apps/notifications/migrations/0007_episode_baselines.py`, `frontend/src/components/Modals/ReminderModal.vue`.
