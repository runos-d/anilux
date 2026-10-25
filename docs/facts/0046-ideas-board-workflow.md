---
id: F0046
title: Доска идей связывает публичный просмотр с управляемым статусным процессом
status: active
date: '2026-10-23'
tags: [frontend, api-contracts, access-control, data-integrity, seo, verification]
kind: implementation
governed-by: TBD
---

`/ideas` публично показывает идеи, ошибки и улучшения в виде канбана или списка; подробности открываются в боковой карточке. Вошедший пользователь создаёт запись только со статусом `pending`, голосует один раз и может изменить либо удалить свою запись до модерации. Staff управляет статусом, приоритетом и публичным комментарием, в том числе переносит карточку между колонками. Уникальность голоса обеспечена ограничением БД, а счётчик обновляется транзакционно. Страница включена в общую навигацию, SEO-проекцию и sitemap.

Проверка: `python manage.py test apps.ideas --keepdb`; `python manage.py test apps.seo.tests.SeoTests.test_ideas_page_has_public_metadata --keepdb`; `python manage.py check`; `python manage.py makemigrations --check --dry-run`; `npm run type-check`; `npx eslint src/components/page/ideas/IdeasView.vue src/api/ideas.ts`; `npm run build-only`; браузерная проверка Playwright на 1440×900 и 390×844.
