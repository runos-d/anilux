---
id: F0037
title: Установщики собираются отдельным worker с актуальным адресом сайта
status: active
date: '2026-10-16'
tags: [release, build, integrations, verification]
kind: implementation
governed-by: TBD
---

Запуск Daphne ставит сборку в очередь native_builds. Отдельный native_builder создаёт Windows EXE (WebView2/NSIS), подписанный Android APK и Linux DEB/AppImage/Flatpak. Origin выбирается только из доверенных настроек NATIVE_APP_SITE_URL, SEO_PUBLIC_ORIGIN, SITE_URL, с нормализацией IDNA. Адрес посетителя не запускает сборки. Ключ выпуска учитывает origin, версию и исходники native. Готовые установщики кешируются по платформе и проверяются по SHA-256 перед повторным использованием. Смена домена требует обновления настроек и перезапуска backend.

GET /api/application/releases/ публично отдаёт состояния и ссылки только на существующие файлы. POST повторной сборки доступен staff/superuser. Загрузки используют асинхронный поток; приватные логи, manifest и ключи не доступны. /app показывает пять готовых форматов и установку PWA; IPA требует доступного Mac и Apple signing, без них статус requires_signing. Android keystore в DATA_DIR/native_signing постоянный: его необходимо резервировать для обновлений APK.

После перезапуска Docker зависимости Compose могут не задержать автоматически перезапускаемые контейнеры. docker_entrypoint.py ожидает аутентифицированное соединение с MySQL до проверки схемы (DB_STARTUP_TIMEOUT, по умолчанию 600 секунд). Неверная схема по-прежнему останавливает запуск. Healthcheck MySQL использует TCP с пятиминутным стартовым периодом; worker сборок и beat зависят от готовой базы и завершённых миграций. Каталог необязательной frontend-статики добавляется в STATICFILES_DIRS только при наличии.

Источники: backend/apps/native_apps/; backend/native/; backend/docker_entrypoint.py; docker-compose{,.native,.production}.yml; docs/NATIVE_APPLICATIONS.md; docs/NATIVE_APPLICATIONS_REVIEW_2026-10-16.md.
