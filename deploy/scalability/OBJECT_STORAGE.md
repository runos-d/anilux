# Подготовка миграции файлов в объектное хранилище

Текущие private URLs и права обслуживает Django; chat/post ASGI fallback теперь потоковый. `mirror_media_file` подготавливает **копию**, не включает live S3/CDN и не переименовывает файлы, поля FileField, ID или URL. Существующий файловый storage остаётся авторитетным. Это позволяет проверить провайдера и manifest до переключения.

Зависимости S3 находятся в отдельном `requirements-object-storage.lock` с hashes и constraints основного lock. Они устанавливаются только в migration-worker образ:

```sh
docker build --build-arg BACKEND_IMAGE=YOUR_TESTED_BACKEND_DIGEST -f backend/Dockerfile.object-storage -t YOUR_MIGRATION_IMAGE backend
```

Проверить конфигурацию workload identity/IAM и private bucket у выбранного провайдера. Отключить anonymous access и public ACL, включить шифрование/версионирование/backup по политике владельца. Не давать migration identity права удаления источника. Стандартная цепочка credentials SDK используется без записи ключей в код или manifest. Endpoint только HTTPS; TLS verification не отключается. До `--apply` команда не создаёт S3 client и не обращается к сети.

```sh
python manage.py mirror_media_file --domain chat --name attachments/example.bin --bucket PRIVATE_BUCKET
python manage.py mirror_media_file --domain chat --name attachments/example.bin --bucket PRIVATE_BUCKET --apply --manifest /private-manifests/chat.ndjson
```

Домены: chat/post/public с соответствующими storage roots. Legacy `posts/` в MEDIA_ROOT копировать с `--domain public`; классификация публичной выдачи из имени домена **не следует**. Manifest с приватными путями должен находиться вне checkout, с правами 600. Один writer на manifest. Копирование: SHA-256 источника → content-addressed key → streaming multipart upload → чтение удалённых байтов и проверка SHA-256/размера → fsync verified mapping. Проверяется, что источник не изменился. Перезапуск идемпотентен по ключу; на обрыв/повреждение нет verified mapping. Повторное копирование может создать новую S3 version; lifecycle orphan/incomplete multipart настраивается отдельно.

Память ограничена блоками 64 KiB, transfer concurrency 2, I/O queue 4; retries максимум 3, connect/read deadlines 2/10с, pool 4. Используется classic transfer implementation, чтобы лимиты не заменялись автоматическим CRT. [Boto3 transfer configuration](https://docs.aws.amazon.com/boto3/latest/guide/s3.html).

Перед cutover ещё нужны: пакетный inventory/manifest всех реально используемых путей; проверка checksum/Range выбранного S3 provider; dual-read/dual-write и отслеживание изменений во время копирования; изменение path-based FFmpeg/export/storage consumers; приватная proxy/X-Accel выдача с проверкой **текущих** ACL/сессии на каждый запрос, включая Range/HEAD/304. Presigned TTL не заменяет немедленный отзыв. Нельзя включать S3 private URLs напрямую в shared cache/CDN. CDN public whitelist — posters/covers и статические build assets, никогда attachments/backups/exports по одному расширению файла. До практической проверки и отдельного cutover исходники не удаляются. Провайдер/CDN и настоящие buckets этим кодом не созданы.

Проверено локально: optional SDK image собирается, mock copy/dry-run/corruption/path traversal tests проходят. Это не S3 compatibility или production migration; нужны внешние endpoint/identity и разрешённые тестовые файлы.
