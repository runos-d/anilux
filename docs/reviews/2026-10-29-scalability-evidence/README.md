# Реализация roadmap: локальная проверка

Дата: 2026-10-29. Roadmap реализован **частично**. Сводка этапов/открытой работы: [progress](../../SCALABILITY_PROGRESS.md). Production и рабочая пользовательская БД не переключались. Владелец подтвердил, что доступна только локальная среда. 6000 и миллион активных пользователей **не сертифицированы**.

## Проверки кода и конфигурации

- [Validation](validation.json): основной release-image набор **334/334 backend tests PASS** за 481,789с на отдельной MySQL `test_scalability_lab`. Session/account revocation, ACL/bans/history/clear, projection equivalence, conversation/recovery, ranked feed и private media включены. [Summary](backend-summary.txt). Fresh schema migrate, Django check, отсутствие model drift прошли. После этого для static inventory и дополнительных isolated routes — **7 targeted checks PASS** за 0,012с без сети/БД; legacy default/ACL/delivery pipeline не менялись.
- Frontend: 91 files / 284 tests PASS; types, ESLint, analytics architecture, production build и bundle budget PASS (entry JS 148227, CSS 70960 bytes). Frontend source относительно исходного `102b9cb` не менялся; официальный Centrifugo SDK добавлен только в отдельный test package.
- [Browser](browser.json): настоящий production frontend/API, синтетическая авторизация, профиль 200, рекомендации на 1280/390px без page/console errors и horizontal overflow. Время до heading 2,7/3,1с — локальное наблюдение, не LCP/слабое устройство/универсальный UX SLA.
- Lab Compose (base/queues/RabbitMQ/Centrifugo), production isolated-worker override и nginx syntax валидны. Все backend/frontend/transport-probe/optional S3 images собраны. Optional S3 SDK `boto3 1.43.121`: pip check и bounded TransferConfig PASS; реальный endpoint не проверялся.
- [Карта обработчиков](surface-map.json): 994 HTTP entries (включая один lab identity), 3 WS patterns, 88 application tasks. Beat registrations полные; все 88 task queues совпали с actual Celery router при isolated profile, в default остались только debug/lab probe. Карта и проверка выполнены с `--network none`, без выполнения самих задач или ACL. Она отражает текущие feature flags; caller queue override имеет приоритет. Inventory выявил legacy notification/media/import/native jobs в default: добавлены isolated routes, legacy сохранён.

## HTTP + долговечные сообщения

Все данные искусственные: **120 пользователей, 3000 anime, 10000 posts**. Две комнаты по 60 участников плюс отдельные небольшие комнаты broker probes. Растущая история сообщений и точные counts находятся в resource snapshots. Аккаунты не имеют реалистичной многолетней библиотеки/уведомлений/реакций/вложений.

Равномерные HTTP читают catalog/feed/search/recommendations, identities вращаются. Один sender делает **1 durable send/s** в первой комнате; global+chat sockets открыты также во второй комнате для проверки изоляции. Это заданный профиль, а не каждый пользователь, отправляющий сообщение раз в минуту. Автоматических retries нет. После стадии — до 10с drain; неполученное в окно не доказывает потерю SQL-записи. Пара `(command, recipient, socket)` дедуплицируется. Данные после закрытия тестового окна не считаются успешной доставкой.

| Прогон | API | Клиенты / WS | HTTP/s, sends/s, время | HTTP / ACK / unique deliveries | p95/p99 HTTP, мс | p95/p99 delivery, мс | Итог |
|---|---:|---|---|---|---|---|---|
| [12 / 2 API](mixed-12-two-api/result.json) | 2×1 CPU | 12 / 24, 6+6 по комнатам | 5 / 1 / 20с | 100/100; 20/20; 240/240 | 87 / 170 | 365 / 590 | Короткий smoke PASS |
| [120 / 2 API](mixed-120-two-api/result.json) | 2×1 CPU | 120 / 240, 60+60 | 10 / 1 / 60с | 600/600; 60/60; 6688/7200 | 1744 / 2865 | 18808 / 19450 | FAIL, вырос backlog клиента |
| [120 / 4 API](mixed-120-four-api/result.json) | 4×1 CPU | 120 / 240, 60+60 | 10 / 1 / 60с | 600/600; 60/60; 7200/7200 | 184 / 276 | 982 / 1313 | Smoke p95 ≤1с PASS; chat SLO 500/1000мс FAIL |

В трёх прогонах duplicates/unexpected recipients/frame errors = 0; HTTP non-200 и generator drops = 0. Generator scheduler p99: **6 / 13 / 8мс**, CPU **0,60 / 5,87 / 4,00с** за полный процесс с ramp; max RSS около **38 / 51 / 52 MiB**. Это свидетельствует об отсутствии обнаруженного насыщения генератора в этих профилях, не доказывает его пригодность для больших ступеней.

В каждом каталоге сохранены `manifest.json` (чистый source commit, hashes, immutable image IDs и cgroup limits) и `resources.jsonl` (CPU/RAM/network/PIDs, SQL/DB connections, outbox age, RabbitMQ ready/unacked и per-replica metrics во времени). [Агрегаты](load-summary.json). Samples включают ramp, а probes раз в 5с могут пропускать кратковременные пики. Нулевой sampled backlog не доказывает нулевую задержку между samples.

Перед публикацией из каждого manifest исключён hash одного ignored local-only конфига, с явными `published_source_hashes_tracked_only`/`omitted_ignored_source_hashes_count`; содержимое этого файла не публиковалось. Raw evidence сохранены локально. Collector исправлен для tracked-only selection; Docker context дополнительно исключает local config/helpers, `.env.*`, ключи и дампы. Новый image `sha256:03c02d6e97a6c39177f2a836848b8f2ce45fe1cee9ff22eccd6d9beed9c39715` собран, отсутствие этих файлов проверено с `--network none`. Load manifests сохраняют фактические прежние image IDs; результаты после пересборки не приписываются новому image.

Ресурсы lab: API по 1 CPU / 1 GiB; MySQL 2 CPU / 1536 MiB, buffer 256 MiB, max connections 128; events и background по 1 CPU / 1 GiB; RabbitMQ 1 CPU / 768 MiB; realtime/cache/broker — разные Redis процессы по 0,5 CPU, 256/192/192 MiB; nginx 0,5 CPU / 256 MiB; generator 1 CPU / 256 MiB; observer 0,25 CPU / 256 MiB. Всё делит Docker Desktop **8 CPU** с другими рабочими сервисами; сумма cgroup ceilings не равна физическому резерву. Здесь HTTP без публичного TLS/CDN, не production network. Прогоны последовательные, cache/history состояния отличаются; коэффициент ускорения и гарантированный онлайн не выводятся.

Первоначально collector запускал Django probe внутри API quota и искажал нагрузку (scheduler p99 126мс, недостающие ACK/доставки). Этот результат исключён из capacity comparisons, raw diagnostic остаётся в ignored `.tmp`. Исправлено отдельным observer, импортирующим Django один раз. Incoming server frame cap 64 KiB не равен client response budget: snapshot здесь ~66,5 KiB; bounded client response cap 1 MiB. Rich payload acceptance ещё требуется.

## Брокер, транспорт, восстановление

- [Остановленный broker](broker-outage.json), [recovery](broker-recovery.json): SQL message сохранён, event остаётся pending; после старта worker опубликовал outbox, duplicate task безопасно завершился. Это публикация в transport, не клиентская доставка.
- [Paused broker](broker-paused.json), [время](broker-paused-time.json), [recovery](broker-paused-recovery.json): CLI завершился за 4,15с вместе с контейнером/Django startup; SQL сохранён, outbox pending, после unpause восстановлен. Publish/confirm/read/write deadlines заданы отдельно; эта CLI цифра не является чистым confirm latency.
- [Countdown retry](rabbit-retry-final.json) прошёл на Celery 5.6.3/Kombu 5.6.2/RabbitMQ 4.4.0. Применена lab at-least-once DLQ policy. Один broker node не даёт quorum HA; poison/DLQ replay и потеря host ещё открыты.
- [Centrifugo](centrifugo-final.json): два узла 6.10.2, официальный JS SDK 5.8.0, 60 clients / 20 publications / 1200 unique deliveries; p95/p99 32/50мс. В этом synthetic transport нет SQL-команды, fresh session/ACL и viewer projection. Сравнивать время с chat pipeline нельзя. `security_equivalence=false`, защищённые события не переключены.
- [DB restore](restore-result.json): synthetic single-transaction dump 5751305 bytes, restore в новую schema того же test MySQL за 71,984с; counts/MySQL checksums шести таблиц совпали. Сильный SHA-256 dump сохранён в отчёте. Это не полное побайтовое доказательство всех таблиц, media restore, новый host или production RPO/RTO.

## Повторение и переход

Команды сборки/seed/проб: [lab README](../../../deploy/scalability/README.md). Для RabbitMQ сначала подготовить isolated consumers и fixed queues/policy: [broker guide](../../../deploy/scalability/BROKERS.md). Перед сравнением четырёх API поднять `api` с `--scale api=4`, дождаться readiness и перезапустить **только lab frontend** для нового upstream состояния. Не запускать backend regressions/build/другую нагрузку одновременно с capacity probe.

Большие комнаты, rich messages, typing/read/edits/deletes, длительный soak, reconnect/replay, все остальные активности, S3/CDN, MySQL replica/promotion и отказ хоста ещё не приняты. Следующий конкретный шаг — профилировать connection setup, SQL/serializer и executor waiting после transport publish на 120/4 API, снизить chat p95/p99 без stale authorization, затем расширять workload и datasets. Старые пути и legacy routing остаются до подтверждения замены. Production, DNS и paid resources не менялись.

После сбора результатов остановлен только Compose project `animecore-scalability-lab`, без `--volumes`; синтетические volumes и ignored backup/evidence сохранены. Рабочие пользовательские контейнеры продолжают работать. Ветка `codex/scalability-roadmap`, реализация `11e8c0a`–`a50cbf4`; основной load source commit — `fc6f982`. Последующие packaging/inventory/routing commits не выдаются за повторную mixed-load приёмку. Слияния в `main` нет.
