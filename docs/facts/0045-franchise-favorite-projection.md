---
id: F0045
title: Полностью избранная франшиза сворачивается в одну карточку коллекции
status: active
date: '2026-10-22'
tags: [catalog, data-integrity, api-contracts, frontend, verification]
kind: implementation
governed-by: D0009
---

Избранное франшизы является производным от всех доступных частей: массовое включение или выключение транзакционно синхронизирует `FavoriteAnime` и `UserLibrary.is_favorite`. Выдача коллекции с `is_favorite=true&group_franchises=true` заменяет полный набор частей одной карточкой франшизы; неполный набор остаётся отдельными карточками аниме. Общий Pinia-store распространяет изменение на уже показанные карточки частей.

Проверка: `python manage.py test apps.playlists.test_franchise_favorites --verbosity 2`; `npx vitest run src/components/Cards/FranchiseCard.test.ts --pool=threads --maxWorkers=1`; `npm run type-check`; `python manage.py check`.
