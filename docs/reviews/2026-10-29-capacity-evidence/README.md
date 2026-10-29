# Изолированная проверка ёмкости

Все аккаунты, токены, сообщения и посты в этом стенде искусственные. Нагрузка и тесты не обращаются к рабочей БД. Нагрузочный клиент принимает только `127.0.0.1:4386` и перед отправкой проверяет маркер стенда на балансировщике и **каждой** из четырёх реплик. Доступ к внешним HTTP providers в ASGI probe отключён. Публичные сети, CDN и видео этим прогоном не проверяются.

## Стенд

- Сеть Docker: `animecore-capacity-verification`.
- MySQL 8: отдельный контейнер `animecore-capacity-mysql`, alias `audit-mysql`, schema `chat_test`, root с пустым паролем **только в закрытой тестовой сети без опубликованного порта**; volume `animecore-capacity-mysql`, лимиты 2 CPU/2 GiB, InnoDB buffer 256 MiB.
- Redis 7: `animecore-capacity-redis`, alias `audit-redis`, без host ports, 512 MiB, maxmemory 384 MiB, noeviction. DB 0 channels/presence, 1 cache, 2 broker, 3 results.
- `compose.verify.yml`: 4 Daphne по 1 CPU/1 GiB, HTTP admission 32, socket admission 4096, handshake admission 64; nginx 0,5 CPU/256 MiB; реальный Celery events worker 1 CPU/768 MiB, concurrency 2. Это **больше ресурсов**, чем один production VPS 4 CPU/8 GiB для всех ролей.
- Docker Desktop: общий хост 8 CPU/~15,5 GiB, на нём есть другие локальные сервисы. Замеры нельзя напрямую переводить в production VPS capacity.

Сначала создать только перечисленные отдельные network/volume/DB/Redis (образы зафиксированы digest в `deploy/compose.data.yml`). MySQL запустить с `MYSQL_ALLOW_EMPTY_PASSWORD=yes`, `MYSQL_DATABASE=chat_test`, `--innodb-buffer-pool-size=256M --performance-schema=OFF`; Redis — без persistence. Не подключать backend/data/mysql или настоящие credentials.

Для Python-команд использовать backend образ, read-only mounts `backend:/app`, `docs/reviews/2026-10-28-performance-evidence:/audit`, текущая папка `:/capacity`; окружение `DJANGO_SETTINGS_MODULE=capacity_settings`, `PYTHONPATH=/capacity:/audit:/app`, `DJANGO_SECRET_KEY=disposable-performance-audit-only`, сеть стенда. Выполнить:

1. `python manage.py migrate --noinput` — полная схема, без обхода миграций.
2. `python /capacity/fixture.py` — создаёт 6000 пользователей с настоящими server-bound sessions, 100 групп по 60 участников, по 10 сообщений истории, 10 000 anime и 60 000 постов. `CAPACITY_ROOM_SIZE=2000` создаёт три комнаты по 2000 участников для уточнённого владельцем сценария. Вывод `TOKENS=...` сохранить **во временный локальный файл**, не в репозиторий и не в отчёт. Повторный seed в ту же БД запрещён. После неудачного seed пересоздать/flush только эту disposable schema.
3. `docker compose -f docs/reviews/2026-10-29-capacity-evidence/compose.verify.yml up -d`. Дождаться готовности всех четырёх `/__capacity_identity` на localhost:4387–4390 и Celery. При повторном прогоне после restart API перезапустить gateway **после** готовности всех API: его старые upstream connections/состояния не должны искажать холодный запуск.
4. Из корня checkout с установленными frontend deps:

```powershell
$env:CAPACITY_TOKEN_FILE = '<absolute temporary token file>'
$env:CAPACITY_USERS = '6000'
$env:CAPACITY_RAMP_BATCH = '16'
node docs/reviews/2026-10-29-capacity-evidence/load_client.mjs
```

Клиент создаёт global+chat на пользователя, проверяет init, распределяет heartbeat во времени, затем подаёт стадии `[HTTP RPS, chat sends/s, duration seconds]`: `30/2/20`, `100/5/20`, `300/10/20`, `600/30/20`, `1200/100/30`. `CAPACITY_STAGES` позволяет задать JSON-массив стадий; `[]` проверяет только соединения. Ramp batch влияет на нагрузку подключения и длительность; всегда записывать его рядом с результатом.

Стадия останавливается при HTTP errors >1%, p95 HTTP/доставки >1 с, недостающих message ACK или доставках участникам. Критерий ramp >2% failures/closures — защитная остановка, а не допустимая production ошибка. Клиент не делает автоматических retries, которые скрывали бы отказы. Последняя версия проверяет уникальные `(command, recipient, socket)`, ожидаемое число по открытым сокетам комнаты и отсутствие получателей из другой комнаты. Кадры после окончания окна стадии учитываются отдельно как late deliveries; отсутствие доставки в это окно не доказывает утрату данных в БД. Для строгой сертификации также нужны длительный прогон, replay и recovery.

Вывод — `mixed-load.json`, без credentials. Сохранить результаты отдельных запусков под разными именами. `ramp-6000.json` — попытка разгона к 6000 до последних оптимизаций, остановленная до цели; это не смешанный тест 6000 пользователей. `mixed-120-final.json` — короткий финальный mix на 120 пользователях: первая стадия проходит, следующая не проходит критерии чата. `mixed-60-profiled.json` и `loop-profile.json` — диагностический прогон с включённым profiler на одной реплике, не capacity benchmark. `mixed-120-dispatch-experiment.json` относится к отброшенному изменению dispatch; штатный Channels dispatch сохранён. Не выдавать количество однажды открытых sockets за устойчивый активный онлайн.

## Регрессии

`mysql_test_runner.MigratedAuditRunner` из предыдущей evidence-папки может запускать Django tests поверх этой уже мигрированной schema. Он **flushes** её в начале. Сначала остановить нагрузку и удалить API/worker containers, затем запускать tests; после tests fixture надо создать заново. Runner проверяет точные DB host/name и pending migrations, не работает с production DB.

SQL instrumentation добавляется к переиспользуемому connection object один раз: wrappers сохраняются при `close()`. Первый черновой прогон с повторным добавлением wrappers был отброшен, его цифры не являются результатом проекта. Подключения после горячего restart API без сброса gateway также не считать самостоятельным пределом capacity.

После проверки удалить только test compose services, два перечисленных test контейнера, сеть, volume и временный token file. Рабочие `anilux_*`, их сети/volumes и backup не удалять. Для production проверок использовать отдельный генератор нагрузки, реальные размеры данных/комнат, typing/read/attachments, проверку восстановления и выбранное оборудование; этот короткий локальный harness не заменяет такую приёмку.

## Повторное профилирование TLS

`tls_connection_benchmark.py` сравнивает 20 новых соединений исходного PyMySQL и адаптера, с `SELECT 1` и закрытием каждого соединения. Скрипт проверяет точные host/schema изолированного стенда. `tls-connection-comparison.json`: CPU 938,3 → 262,6 мс за 20 подключений; TLS, required flag и verification options совпали. Это результат операции подключения, не ускорение всего сайта на 72%.

`mixed-120-tls-cache.json` — unprofiled mixed прогон после TLS fix: все HTTP/ACK/доставки получены, но p95 доставки 1,10 с выше порога 1 с. `tls-worker-profile.json` — диагностический cProfile main thread и sync workers, с существенным overhead; его нельзя использовать для capacity. Увеличение окна auth-batch до 20 мс проверялось в `mixed-120-auth-window-experiment.json`, улучшения не показало и в итоговый код не вошло.

Повторный стенд создавался из DDL уже мигрированной локальной схемы и записей `django_migrations`, без строк пользовательских таблиц; перед seed проверялось отсутствие пользователей. Runner проверяет pending migrations и выполняет regression upgrade tests. Это не копия рабочей переписки или аккаунтов. Версии среды: Django 5.2.18, PyMySQL 1.2.3, Channels 4.3.2, channels-redis 4.3.0.

## Большие комнаты и жизненный цикл groups

`ramp-large-rooms-before-parallel-db.json` и `ramp-large-rooms-parallel-db.json` — попытки к 6000 с тремя комнатами по 2000. Оба остановлены до цели. Во втором были 4976 попыток / 9852 открытых sockets / 100 ответов 502; он выполнен до исправления group expiry. Batch различается (32 и 16); не выводить из этого коэффициент ускорения одного изменения.

`group_fanout_benchmark.py` использует отдельный уникальный Redis prefix, 2000 groups / 120 live; проверяет адресата каждого полученного кадра. `group-fanout-comparison.json` хранит три повтора до/после отбора пустых groups. В настоящем worker оставались group entries старых процессов (default Channels expiry — сутки), поэтому одной фильтрации пустых групп оказалось недостаточно. `capacity_celery.py` — диагностический entrypoint вместо `-A config` только для events worker; выводит длительности room send, user fanout и всей задачи без arguments/payload. Результаты — `worker-fanout-timing.jsonl`. Итоговый compose снова использует `-A config`.

Сохраняемый вариант: `WS_GROUP_EXPIRY=300`, текущие subscriptions обновляются authenticated heartbeat через bounded pipelines; ошибки renewal требуют reconnect. `mixed-120-in-large-room-group-expiry.json` — 120 активных из 2000 членов одной комнаты, 240 sockets. Первая ступень 10 HTTP/с + 1 send/с проходит (4800/4800 доставок, p95 969 мс), следующая 30 HTTP/с + 2 sends/с не проходит. `mixed-load.json` указывает на этот сохраняемый вариант.

`mixed-120-in-large-room-parallel-db.json` и `mixed-120-in-large-room-empty-groups.json` относятся к более ранним фазам. `mixed-120-combined-reader-experiment.json` — отброшенное объединение auth/ACL/projection: меньше SQL не улучшило end-to-end SLO. Оно удалено из итоговой реализации. Функциональная проверка итогового кода — 246 tests, 292,775 с, OK; summary в `backend-final-regressions.txt`, список модулей и hashes в `validation.json`. HTTP smoke после обновления локальных сервисов — `local-readiness-phase2.json`. Цель 6000/длительный production soak остаётся неподтверждённой.
