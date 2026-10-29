---
id: F0049
title: Повторное ревью производительности 28 октября 2026
status: active
date: '2026-10-28'
tags: [performance, verification]
kind: implementation
governed-by: TBD
---

Повторное ревью охватило 72 маршрута с browser fixtures, изолированные SQL-пробы и streaming в Docker-образе. Зафиксированы N+1 для франшиз и contact-only фото, полное чтение каталога при неизвестном slug, повторы HTTP, рост DOM ленты и риски realtime/видео. Отчёт и воспроизводимые результаты: `docs/reviews/2026-10-28-performance-review.md`, `docs/reviews/2026-10-28-performance-evidence/`. Подтверждённой пропускной способности production-подобного MySQL/Redis/Daphne нет; fixtures и SQLite её не доказывают.

Последующие исправления и измеренные ограничения нагрузки записаны в F0050 и `docs/reviews/2026-10-28-performance-remediation.md`.
