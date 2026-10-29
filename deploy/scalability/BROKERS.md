# Постепенное разделение workers и проверка брокеров

`CELERY_QUEUE_PROFILE=legacy` по умолчанию сохраняет прежний маршрут. `isolated` отделяет events, notifications, recommendations, maintenance, reports, imports и media; ещё не классифицированные задачи остаются в `celery`. Изображения в isolated тоже идут в media worker. На всех API/beat/workers нужен одинаковый профиль. Только проверенные идемпотентные chat/post outbox и recommendation refresh получают late ACK / reject on worker loss; прочие задачи сохраняют прежнюю политику.

Production-роли: после `deploy/compose.workers.yml` добавить `deploy/compose.workers.isolated.yml`. Этот override отделяет события, медиа, импорт и отчёты; background сначала совместно обслуживает notifications/recommendations/maintenance/default. Для независимого роста каждой из этих очередей выделить отдельный worker с `-Q NAME` и снять её с background. Не копировать сумму лимитов всех ролей на один маленький хост. Это подготовленная конфигурация, не удалённый deployment.

Порядок Redis routing canary: запустить новые consumers, убедиться, что они слушают нужные очереди, затем включить профиль на API/beat. Старый consumer `celery` нужен для дренирования старых задач. Откат: вернуть producers к legacy, оставить isolated consumers до опустошения их очередей. Не очищать Redis и не терять необработанные задачи при откате.

## RabbitMQ rehearsal

Celery **5.6.3/Kombu 5.6.2** из lock проверены с RabbitMQ **4.4.0**, закреплённым digest. Это одноузловой прототип: quorum type не создаёт репликацию без нескольких broker nodes. Включение `CELERY_QUORUM_QUEUES=true` допускается только с isolated и `amqp[s]://`. Декларации: durable topic task exchange, фиксированные task queues, `confirm_publish`, bounded length с `reject-publish`, delivery limit 20 и отдельная bounded failed queue. Не включать expiry для долговечных outbox events.

Публикация и publisher confirm ограничены 2с, connect — 1с, AMQP read/write — 2с; HTTP не должен бесконечно ждать stalled broker. Для quorum источников установить broker policy `dead-letter-strategy=at-least-once`, `overflow=reject-publish` с точным allowlist task queues (не failed). Lab-команда: `python tests/scalability/apply_broker_policy.py`. [RabbitMQ dead-lettering](https://www.rabbitmq.com/docs/quorum-queues#dead-lettering) удерживает такие события до подтверждения target; недоступная/полная DLQ создаёт backpressure, а не разрешение очищать события. Production policy/HA/poison replay проверять отдельно.

RabbitMQ 4.4 отклоняет transient nonexclusive служебные очереди Celery 5.6. Установлены exclusive event/control queues. Все task queues нужно **объявить до запуска workers**: native delayed delivery связывает даже очереди, у которых ещё нет consumer. Failed queue объявляется отдельно и не входит в список consumers/ETA bindings. [Celery quorum configuration](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/rabbitmq.html#using-quorum-queues), [параметры служебных очередей](https://docs.celeryq.dev/en/v5.6.3/userguide/configuration.html#event-queue-exclusive).

Из корня checkout использовать базовый lab Compose плюс overlays:

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.queues.yml -f deploy/scalability/compose.rabbitmq.yml up -d --wait rabbitmq
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.queues.yml -f deploy/scalability/compose.rabbitmq.yml run --rm --no-deps migrate python manage.py prepare_task_broker --apply
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.queues.yml -f deploy/scalability/compose.rabbitmq.yml up -d --wait api events background
```

Без `--apply` provisioning показывает только фиксированные имена, не URL/credentials. Production должен использовать новый отдельный vhost: тип уже существующей classic queue/exchange нельзя менять тем же именем. Сначала проверить все producers, retries/countdown, task results, повторный запуск worker, poison message и DLQ. Дренирование Redis и переключение producers выполняются отдельным canary; не направлять одновременно два брокера в неидемпотентный consumer. Откат сохраняет новый broker/consumers до дренирования. Список outbox в SQL остаётся источником восстановления.

`tests/scalability/broker_probe.py` проверяет countdown retry и восстановление chat outbox после stopped broker. Запускать через `migrate` с read-only mount `tests/scalability:/load`, `PYTHONPATH=/app`; фазы `produce`, `recover --event-id N`, `retry`. При недоступном RabbitMQ SQL-сообщение сохранено; после restart опубликовано; повторная задача не публикует уже помеченное событие. Это broker/outbox test без клиентских доставок и без доказательства HA. Потеря целого broker host, три quorum nodes, DLQ replay, provider jobs и длительный soak ещё требуют проверки.

## Centrifugo

`compose.centrifugo.yml` поднимает два Centrifugo **6.10.2** с Redis engine и отдельным synthetic namespace, без host ports. Только тестовый JWT и канал `lab:probe-*`; реальные domain events/credentials не подключены. SDK **centrifuge 5.8.0** находится в отдельном тестовом package, не увеличивает frontend bundle. `checkconfig` и официальный JS client проверяют подписку, публикацию, unique recipients и запреты неизвестного namespace/client publish.

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.centrifugo.yml build transport-probe
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.centrifugo.yml up -d centrifugo
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.centrifugo.yml run --rm transport-probe
```

Synthetic smoke: 60 clients, 20 publications, 1200/1200 уникальных доставок, без дублей/посторонних; p95 32мс, p99 50мс на общей машине. **Сравнивать это число с текущим chat pipeline нельзя:** здесь нет SQL-команды, outbox, актуальной сессии и viewer projection. Доказана работоспособность базового transport, не превосходство замены. Защищённые чаты остаются на Channels: JWT при connect и refresh/proxy hooks сами по себе не проверяют отзыв на каждой серверной доставке. В [permission model](https://centrifugal.dev/docs/server/channel_permissions) механизмы проверяются на определённых операциях; это не доказательство D0031.

До миграции обязательны одинаковый mixed workload/ресурсы и тесты current session/account/ban/membership/visibility, clear/prejoin/replay/expiry в момент следующего действия/доставки. История Centrifugo ограничена 100 событиями / 60с и не заменяет БД. В прототипе `security_equivalence=false`; prod feature flag не добавлен. Эксперименты с брокером и транспортом проводятся последовательно; выключить Centrifugo перед следующим экспериментом.
