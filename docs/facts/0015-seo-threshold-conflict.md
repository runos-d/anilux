---
id: F0015
title: Документы SEO расходятся по порогу noindex
status: superseded
date: '2026-10-11'
tags:
- seo
- documentation
kind: environmental
governed-by: D0010
---

`SEO_JOURNAL.md` и presentation/seo_templates.md указывают noindex при count < 5; `backend/seo_templates.md` задаёт noindex_threshold: 3 для хабов. Bootstrap не определяет актуальную продуктовую политику по этим противоречивым шаблонам.

2026-10-15: запрос пользователя явно установил порог 5. Исполняемая политика - `apps.seo.service.MIN_TITLES`, решение D0028; старые Markdown-шаблоны не являются runtime-конфигурацией.

Источники: `SEO_JOURNAL.md`, `backend/apps/anime/presentation/seo_templates.md`, `backend/seo_templates.md`.
