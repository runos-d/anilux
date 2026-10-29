# Изолированный стенд масштабирования

Этот Compose создаёт только ресурсы проекта `animecore-scalability-lab`. Образы собираются из checkout, frontend — Vite production build и штатный nginx; две реплики Django/Daphne работают с `DEBUG=False`. Тестовые настройки жёстко требуют `lab-mysql/scalability_lab`. MySQL/Redis не публикуют порты; рабочие `.env`, bind mounts и данные не подключаются. Фиктивные ключи в Compose годятся только для этого стенда. Почта отключена. Внутренняя сеть app/data не имеет внешнего egress. Это не production deployment.

Из корня checkout, всегда с указанным `--env-file`, чтобы Compose не считывал рабочую `.env`:

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml config --quiet
docker compose --env-file .env.example -f deploy/scalability/compose.yml build
docker compose --env-file .env.example -f deploy/scalability/compose.yml up -d
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm migrate python manage.py seed_scalability_lab --users 120 --anime 3000 --posts 10000
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm generator --rate 5 --seconds 20
```

Frontend доступен на `127.0.0.1:4480`. Сначала проверить `/__lab_identity` и `/health/ready/`. Генератор работает отдельным процессом/контейнером, принимает только `http://frontend` и проверяет маркер БД перед нагрузкой. Его CPU ещё разделяет Docker-хост с приложением; для сертификации нужен отдельный Linux-генератор и ограниченный private/VPN маршрут к тестовому deployment. Проверка маркера необходима, но не заменяет изоляцию сети.

Профиль `public-http-smoke` — четыре равновероятных чтения каталога, ленты, поиска каталога и рекомендаций. У него нет активных авторизованных пользователей или WS; его RPS нельзя переводить в онлайн. Фиксируются предложенный и завершённый RPS, ошибки без retry, p50/p95/p99, полученные байты, CPU/RSS генератора, p99 отставания планировщика. Семплы хранятся в ограниченной гистограмме (1 мс, 60 с); число одновременных запросов ограничено. При насыщении генератора считаются пропущенные запросы и проверка не проходит. Начальный smoke-порог p95 ≤1 с не заменяет SLO roadmap 300/500 мс.

## Техническая наблюдаемость

`OPERATIONAL_METRICS_ENABLED=true` включает process-local Prometheus-метрики `/internal/metrics`; обязательный `Authorization: Bearer $OPERATIONAL_METRICS_TOKEN`, при отсутствии/ошибке — 404. Публиковать endpoint только в private сети. Scrape каждой ASGI-реплики отдельно, суммировать rate/histogram на стороне Prometheus. Scrape балансировщика не видит все процессы. Имя домена и класс статуса имеют конечное множество значений; URL, user/session IDs, заголовки, тела запросов и вложения не сохраняются.

HTTP получает `X-Trace-Id`; корректный W3C trace ID переносится, прочие значения заменяются случайным ID. `OPERATIONAL_TRACE_SAMPLE_RATE=0.01` включает семплированный структурированный transport log (только домен, статус, время, байты, trace ID). Входящий sampling flag не может навязать логирование. Это корреляция HTTP/transport, **не полная OpenTelemetry-трасса команды, SQL, Celery и доставки**. При выключенном флаге wrapper прозрачен. Метрики HTTP включают время до завершения streaming; отмены освобождают active gauge.

Снимок очередей/БД без пользовательских payload:

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm migrate python manage.py scalability_snapshot
docker stats --no-stream --format json --filter label=com.docker.compose.project=animecore-scalability-lab
```

Для Docker без поддержки `stats --filter` получить IDs через `docker ps -q --filter label=com.docker.compose.project=animecore-scalability-lab` и передать их `docker stats --no-stream --format json`. Сохранять снимки до, во время и после прогона, а не только финальные значения. Snapshot показывает pending count/oldest age по индексируемому outbox, очередь задач по Redis LLEN и ограниченный набор MySQL status. Это on-demand probe; нельзя вызывать его на каждый HTTP request. Prometheus/Grafana, SQL spans, broker timestamps и client delivery histogram ещё предстоит подключить.

## Регрессии и откат

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm migrate python manage.py check
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm migrate python manage.py makemigrations --check --dry-run
docker compose --env-file .env.example -f deploy/scalability/compose.yml run --rm migrate python manage.py test core --settings=config.settings_scalability_test --noinput
```

Тесты используют отдельную `test_scalability_lab`; не запускать одновременно с нагрузкой. Новая telemetry выключается env-флагом без миграций. Остановка стенда: `docker compose --env-file .env.example -f deploy/scalability/compose.yml down`; тома сохраняются. Удалять disposable volumes можно только после сохранения evidence и проверки project label. Рабочие volumes и контейнеры не трогать.

Перед каждой поставкой: отдельная backup/restore rehearsal, проверки приватности и replay, migration plan, canary на тестовом deployment, возврат предыдущих digest и флагов. Прямое переключение production не входит в эти команды.
