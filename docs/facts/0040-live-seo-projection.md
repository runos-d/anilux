---
id: F0040
title: SEO-выдача использует общую живую проекцию и управляемые подборки
status: active
date: '2026-10-15'
tags: [seo, catalog, verification]
kind: environmental
governed-by: D0028
---

`apps.seo` формирует HTML, canonical, robots, OG/Twitter и JSON-LD; router использует тот же JSON через `/api/seo/page/`. `SiteSeoSettings`, `SeoOverride`, `SeoCollection` доступны в Django admin. Порог подборок - 5, доступность учитывает правила каталога. XML секционируется; кандидаты хабов обновляются Celery/refresh_seo, а права проверяются повторно при выдаче. SW не подменяет документы статическим index.html. Локальный opt-out включён по умолчанию.

Исправление 2026-10-16: standalone-клиент удалён из-за регрессий интерфейса. После серверного HTML запускается прежнее приложение Vue; каталог/франшиза сохраняют исходные компоненты, новые подборки используют AnimeCard и общую catalogGrid.css. Футер общий, цвета берутся из токенов темы. Серверные стили удаляются после mount. DOM writer общий - seoHead.ts. Проверка тёмной, полуночной и белой тем должна сравнивать карточки с обычным каталогом.

Серверные и клиентские проверки: `backend/apps/seo/tests.py`, `frontend/src/composables/useSeo.test.ts`. HTTP/браузер: `scripts/audit_seo_http.py`, `frontend/tests/seo-browser.js`. Актуальные результаты и ограничения выпуска - `docs/SEO_IMPLEMENTATION_2026-10-15.md`, `artifacts/seo/`.

Подборки и /anime/browse используют общий CatalogView, AnimeFilterBar, AnimeCard, Pagination и catalogGrid.css. Уточнение выборки выполняется в service.refine_collection до пагинации для HTML и JSON. Параметры поиска/фильтров/размера/сортировки/shuffle_seed хранятся в URL; пагинация сохраняет их. Проекция принимает JWT только для текущей учётной записи при исключениях библиотеки; её ответы остаются private,no-store. Публичные права доступа и базовые условия подборки не ослабляются.

Футер 2026-10-16 статический: SeoNavigation не зависит от seoPage/API; HTML и Vue используют frontend/public/site-navigation.json, копируемый 40-seo-shell.sh рядом с серверным shell. Контакты и документы доступны без входа; документы с published=false -noindex и вне sitemap-pages. Подборки остаются в /anime/browse; page.related больше не управляет футером. CSS не менялся. Проверки: docs/SEO_FOOTER_AUDIT_2026-10-16.md.
