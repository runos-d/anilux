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

## Пакетный inventory FileFields

`inventory_media_page --describe` перечисляет зарегистрированные FileFields и поддержанные local storage domains без чтения БД/файлов. Затем один запуск читает максимум 500 строк выбранной модели по integer PK, с фиксированным верхним watermark. Имена/PK/file metadata попадают только в новый private JSON manifest вне checkout (exclusive creation, mode 600); stdout содержит counts/status/cursor. Source files и live paths не меняются; SDK/сеть не нужны.

```sh
python manage.py inventory_media_page --describe
python manage.py inventory_media_page --model social.Attachment --limit 100 --manifest /private-manifests/attachments-page-001.json
python manage.py inventory_media_page --model social.Attachment --after-id LAST_ID --through-id FIRST_PAGE_WATERMARK --limit 100 --hash-budget-mib 64 --manifest /private-manifests/attachments-page-002.json
```

Сохранять `through_id` первой страницы и продолжать `next_after_id`, пока `has_more=false`; новые записи после watermark обрабатываются следующей серией. Лимит hash I/O 0..64MiB на страницу, по умолчанию 0 (только stat); большие файлы откладываются без SHA, changed/missing/invalid/unreadable отмечаются отдельно. Рост файла во время hashing ограничен исходным размером +1 байт. Это наблюдение, не transaction snapshot файлов и не verified S3 mapping. После копирования повторять inventory и checksum, изменения за время обхода ещё требуют reconciliation/dual-write.

Название `public` означает только MEDIA_ROOT: **видимость из storage domain не выводится**, profile/private legacy files не разрешаются для CDN. Unsupported storages сохраняются как явный status. Команда охватывает FileFields, а не пути внутри JSON/настроек, orphan files, export/download/FFmpeg caches или внешние URLs; `complete_storage_inventory=false` не позволяет принять такую страницу за полный manifest миграции. Не публиковать private pages в Git/logs/evidence.

## Физические файлы и файлы без ссылок

`inventory_storage_tree` дополняет FileField pages потоковым JSONL обходом public/chat/post/downloads roots. Работает в Linux storage-worker container, без SQL/SDK/сети. Встреченные файлы без ORM-ссылки, JSON/exports и caches тоже попадают в manifest, если физически находятся под выбранным root. Связь с владельцами/ACL и содержимое JSON команда не определяет. Defaults post/downloads совпадают с live storage даже при отсутствии optional settings.

```sh
python manage.py inventory_storage_tree --domain public --manifest /private-manifests/public-tree.jsonl --max-entries 100000 --max-seconds 300 --hash-budget-mib 64
python manage.py inventory_storage_tree --domain downloads --prefix ready --manifest /private-manifests/downloads-ready.jsonl
```

Вывод: header, по одной строке на entry и footer с counts/scan_completed/tree_exhausted. Имена находятся только в новом private manifest вне checkout; stdout без путей. Обход удерживает максимум 64 directory handles, до 1 млн entries / 3600с и 0..64MiB hashing; defaults 10000 / 30с / metadata only. Дедлайн проверяется между filesystem operations, не прерывает зависший kernel/NFS call. При лимите/ошибке footer явно частичный; это не resumable cursor. Для большого дерева выделять непересекающиеся prefixes и сохранять каждый manifest отдельно; полный последующий проход/reconciliation обязателен.

Directory-relative Linux descriptors с O_NOFOLLOW не обходят symlink, в том числе при замене каталога; special files не открываются. Hashing сверяет inode/mtime/ctime и имя после чтения, изменённые/нечитаемые файлы отмечаются ошибкой. Источники не меняются. Для согласованной inventory нужен readonly snapshot/freeze или повторная сверка: `scan_completed=true` означает завершённый наблюдаемый tree, **не** согласованный snapshot всех ссылок и файлов. `complete_storage_inventory=false` сохраняется: внешние roots/JSON references/legacy fallback mapping, reconciliation, dual-write и live migration ещё открыты.
