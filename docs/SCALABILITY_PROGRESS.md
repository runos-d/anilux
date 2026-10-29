# Выполнение roadmap масштабирования

Рабочая ветка: `codex/scalability-roadmap`. Основание: [roadmap](SCALABILITY_ROADMAP_2026-10-29.md), D0031, D0032, F0051. Production не переключается. Ни одна ступень онлайна пока не сертифицирована. Дата начала: 2026-10-29.

Статусы: **реализовано** — есть код/конфигурация; **проверено** — есть выполненная проверка и результат; **внешнее** — нужен отдельный Linux-стенд/сеть/оборудование; **открыто** — реализации ещё нет. Эти статусы независимы.

| Этап | Приёмка | Реализовано | Проверено | Открыто / внешнее |
|---|---|---|---|---|
| 1. Измерения | Воспроизводимый production build, изолированные данные, отдельный генератор; профили всех доменов; p95/p99, ошибки, CPU/RAM/сеть, lag | В работе | — | Внешние генераторы и production-подобный baseline |
| 2. Клиент/API | Ограниченная стоимость чтения/записи, отмена, бюджеты SQL/DOM, cold/warm | Оптимизации предыдущей сессии сохранены | Исторические результаты: capacity review | Новые бюджеты и устранение оставшихся синхронных пересчётов |
| 3. Данные/проекции | Transactional outbox, повторы, версии, актуальные ACL, перестроение, ограниченные read models | Chat/Post outbox, keyset feed и recommendation snapshots существуют | Исторические privacy/replay tests | Общие контракты доменов, поиск, hybrid feed, дополнительные recovery tests |
| 4. Realtime/очереди | Совместимость транспорта и D0031, bounded fanout/queues, независимые workers, broker failure | Channels остаётся действующим транспортом | Исторические mixed tests не прошли следующую ступень | Centrifugo comparison, RabbitMQ rehearsal, fanout bottleneck |
| 5. Медиа | S3/CDN, приватный Range с текущими ACL, проверяемая миграция, отдельные ресурсы | Текущие media/import/download workers и private delivery сохранены | Исторические Range/FFmpeg tests | Object storage, file migration и внешняя сеть |
| 6. Горизонтальный рост | Несколько API/WS, независимые cache/broker, primary/replica и restore | Ролевые Compose существуют | Историческая config/nginx validation | Разделение ресурсов, restore rehearsal, failover; sharding/K8s только по измерениям |
| 7. Приёмка/переход | Ступени, soak, reconnect/fault, безопасное включение/откат | Исторический короткий harness | 6000 mixed **не подтверждены** | Длительная нагрузка и recovery на отдельной инфраструктуре |

## Журнал результатов

- Исходное состояние: чистый `main`, `102b9cb`; `origin/main` после fetch совпадает. Создана рабочая ветка. Реальная `.env`, данные и локальные пользовательские контейнеры не используются для нагрузки.
- Новые результаты и команды добавляются вместе с проверенными изменениями; исторические evidence не перезаписываются.
- Первая поставка: опциональная ASGI telemetry с bounded labels/private scrape, независимые cache/Channels Redis URL и bounded cache connection pool; отдельный production-build Compose, синтетический seed, HTTP-генератор и snapshot outbox/DB/queue; профили всех доменов. Проверено: 7 новых unit/config/safety tests, Django check (0 issues), Compose config, backend/frontend Docker build. Frontend baseline: 91 files / 284 tests PASS; types, lint, analytics architecture, build/bundle PASS (JS 148227, CSS 70960 bytes). Полная миграция пустой MySQL ещё выполняется; HTTP load и backend domain regressions будут записаны отдельно. kms CLI в окружении отсутствует: knowledge records/индексы обновлены вручную по принятому формату.
- Этапы 2/3: холодное персональное чтение рекомендаций использует общий неперсональный fallback, worker готовит личную проекцию; dirty-проекция не возвращает старые причины из очищенной истории. Live исключения библиотеки/видимости ограничены кандидатами (не всей коллекцией). Catalog invalidation повышает revision и не позволяет уже работающему worker опубликовать устаревший результат. `rebuild_recommendations` делает bounded keyset recovery с dry-run по умолчанию. 6 новых регрессий входят в прошедший целевой MySQL-набор: 54 tests PASS (рекомендации/календарь/chat extensions/oct12). Бесконечная персональная библиотека ещё может дорого обрабатываться фоновым алгоритмом; online путь её больше не материализует.
