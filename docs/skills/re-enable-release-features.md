---
id: re-enable-release-features
title: Безопасное включение отложенных release-функций
status: active
date: '2026-10-19'
tags:
- release
- verification
- access-control
kms-generated: false
---

Включать один модуль за изменение. Сначала устранить его открытые security/data-integrity задачи и добавить anonymous/user/admin API matrix, query budgets и frontend router/component tests. Затем установить одинаковый server flag и `VITE_` flag в целевом окружении, пересобрать frontend и перезапустить backend. Проверить прямые URL, фоновые запросы, permissions, throttles и rollback выключением обоих flags. Данные и миграции при выключении не удалять.

Флаги: `FEATURE_DUBS_ENABLED`, `FEATURE_REACTOR_ENABLED`, `FEATURE_TWO_FACTOR_ENABLED`, `FEATURE_STUDIO_REACTIONS_ENABLED`, `FEATURE_STUDIO_SYNC_ENABLED`; frontend использует соответствующие `VITE_FEATURE_*`.
