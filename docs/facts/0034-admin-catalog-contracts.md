---
id: F0034
title: Административные API франшиз и скрытия каталога реализованы
status: active
date: '2026-10-13'
tags: [catalog, api-contracts, data-integrity]
kind: environmental
governed-by: TBD
---

/anime/admin/franchises/ поддерживает CRUD, add-anime, remove-anime и полный reorder без дубликатов/чужих частей. Ручные связи и порядок защищены franchise_manual от автоматической синхронизации. Поиск Kodik и сохранение графов используют общую проверку anime-узлов Shikimori и хронологический порядок; остальные результаты поиска сохраняются.

catalog-options, catalog-rules, catalog-hidden и anime-search доступны администраторам. Скрытие хранится отдельно от is_available и пользовательского прогресса. Правила учитывают новые импорты, пересечения, ручное скрытие и явное восстановление; apply отменяет исключения восстановленных тайтлов. Изменения инвалидируют каталог и рекомендации. Миграция anime.0013 добавляет два управляющих класса и флаг ручной связи.

Источники: backend/apps/anime/presentation/views/admin_catalog_views.py; backend/apps/anime/application/catalog_visibility.py; backend/apps/anime/application/franchise_sync.py; backend/apps/anime/application/test_admin_catalog.py; docs/API_PWA_REVIEW_2026-10-13.md.

Интерфейс проверяет роль из API (is_admin/is_staff), а не имя аккаунта. В локальной базе восстановлен is_staff существующего владельца id=6; is_superuser не менялся. Настройка group_franchises была сохранена выключенной и включена по запросу пользователя. Изменение настройки в CatalogManager инвалидирует общий клиентский ключ catalog-settings; сохранённый экран каталога обновляет группировку при возвращении. Состояние до исправления и SQL-копия находятся в backend/data/local_release/reported-fixes-20261013-175720/.
