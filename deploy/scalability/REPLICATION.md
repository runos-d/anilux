# Локальная репетиция MySQL replication

Только project `animecore-scalability-lab`, private lab network и синтетическая schema. Overlay добавляет binlog/уникальный server-id primary и отдельный read-only replica volume. API/WS/авторизация/ACL продолжают читать primary: добавление реплики само по себе не разрешает routing критичных чтений. Никаких writer promotion, DNS или production cutover.

Не совмещать с load/regressions: primary перезапускается, dump кратковременно получает read lock для согласованного checkpoint. Перед overlay остановить только lab API/workers/observer, сохранить существующие volumes. Команды из корня:

```sh
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.queues.yml -f deploy/scalability/compose.rabbitmq.yml stop api events background observer frontend
docker compose --env-file .env.example -f deploy/scalability/compose.yml -f deploy/scalability/compose.replica.yml up -d --no-deps --wait lab-mysql lab-replica
python tests/scalability/replica_probe.py bootstrap
python tests/scalability/replica_probe.py recover
```

`bootstrap` проверяет container labels, точные schema/server-id/binlog и **пустоту replica schema до любых изменений**. Существующая копия никогда не очищается. Создаёт отдельного replication user с REQUIRE SSL, dump `--single-transaction --source-data=2 --set-gtid-purged=OFF --skip-add-drop-table`, восстанавливает новую пустую копию, задаёт file/position checkpoint, включает replication и сохраняет `super_read_only=ON`. Dump с synthetic sessions остаётся только в ignored `.tmp`; наружу counts/checksums шести таблиц, SHA-256, размер и состояния threads. Ошибка/partial import требует отдельного разбора; повторный bootstrap отказывается перезаписывать данные.

Выбран file/position bootstrap: существующий lab имеет историю без GTID. GTID нельзя объявить простым эквивалентом переключения флага поверх старых backups/logs. Основания: [согласованный mysqldump checkpoint](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html), [ограничения включения GTID](https://dev.mysql.com/doc/refman/8.0/en/replication-gtids-howto.html). Автоматизация ограничена этой MySQL 8.0 image, не является универсальным production bootstrap.

`recover` останавливает только SQL applier, фиксирует отсутствие новой synthetic записи на replica, возобновляет и ждёт точный source checkpoint. Проверяет отказ root application write через super-read-only, рестарт replica, сохранность read-only fence и единственную строку с новой версией после catch-up. `skip-replica-start` намеренно требует явного START REPLICA после restart; automatic failover не реализован. Probe markers сохраняются; таблицы/тома и старые backups не удаляются.

В lab source connection зашифрован (SOURCE_SSL=1, REQUIRE SSL); автоматический self-signed MySQL certificate **не подтверждает hostname/CA identity**. Production обязан использовать private replication network, отдельные минимальные credentials и CA/hostname verification (`SOURCE_SSL_CA`, `SOURCE_SSL_VERIFY_SERVER_CERT=1`), мониторинг ошибок и lag, binlog retention/backup и согласованный RPO/RTO. Значения lab credentials и TLS настройки не переносить в production.

Перед реальным promotion нужны fencing старого writer, доказательство полного catch-up/допустимого RPO, запрет двух writers, переподключение ORM/workers, проверка outbox/idempotency, обратная репликация и восстановление нового host/media. Эти критерии не закрыты локальной парой контейнеров. Реплика отстаёт по определению; session/account/ACL/visibility и критичные read-after-write по D0031 на неё не переносятся.

После rehearsal остановить replica или весь lab без `--volumes`. При следующем load явно выбрать обычный либо replica overlay и записать конфигурацию: лишняя реплика меняет ресурсы и стоимость записи primary. Для продолжения синхронизации после остановки снова запустить тот же overlay и выполнить START REPLICA; повторный bootstrap не нужен.
