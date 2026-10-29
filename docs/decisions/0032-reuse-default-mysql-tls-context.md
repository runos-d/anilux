---
id: D0032
title: Переиспользовать неизменяемый TLS context MySQL без кеширования соединений
status: active
date: '2026-10-29'
tags: [performance, data-integrity, verification]
track: platform
---

ASGI сохраняет `CONN_MAX_AGE=0`. PyMySQL 1.2.3 в default PREFERRED TLS при каждом соединении создаёт `SSLContext` и загружает системные CA. Тонкий MySQL backend `core.db.backends.mysql` наследует Django backend и создаёт `CachedTLSConnection`: переиспользуется только default context с пустыми опциями, неизменяемый после создания. Это не pool: SQL connections, transactions, sessions и результаты авторизации не переиспользуются.

Режим negotiation, required-TLS flag и существующая verification policy драйвера сохраняются. Явные CA/cert/key/options проходят исходный путь при каждом подключении, чтобы ротация продолжала применяться. Явный `SSLContext` передаётся драйверу без замены. Disabled TLS не включается принудительно. После fork контекст и lock создаются заново; есть opt-out `DB_TLS_CONTEXT_CACHE=false`. SQLite backend не меняется.

При обновлении Django/PyMySQL проверять inherited backend connection setup и regression tests. В частности, сохраняется Django bytes-encoder compatibility adjustment. [Python SSLContext](https://docs.python.org/3.11/library/ssl.html#ssl.SSLContext) допускает совместное использование context, если после начала работы его не переконфигурировать. Свежесть проверки доступа по-прежнему регулируется D0031.
