---
id: F0043
title: Release-функции закрыты fail-closed флагами на backend и frontend
status: active
date: '2026-10-19'
tags:
- release
- access-control
- verification
kind: implementation
governed-by: D0029
---

Пять release-флагов принимают только нормализованные boolean-значения и по умолчанию выключены. Выключенные API-префиксы отвечают `404` до ORM/serializer/integration logic; frontend не собирает соответствующие routes и ссылки. Debug API монтируется только при `DEBUG` и требует staff. Проверка: `config.test_release_hardening`.

Email-конфигурация выбирается через `EMAIL_PROVIDER`; development использует Mailpit, production требует Brevo credentials, HTTPS frontend URL и не-placeholder домен. JWT access действует 15 минут, rotation и blacklist включены. Подтверждение и reset используют подписанные одноразовые токены, а delivery webhook требует отдельный bearer token и сохраняет только отфильтрованные поля.

Источники: `backend/config/{feature_flags,settings,urls}.py`; `backend/apps/users/application/email_service.py`; `backend/apps/users/presentation/views/{users_views,email_webhooks}.py`; `.env.example`; `docker-compose*.yml`.

Production dependencies зафиксированы hash-locked файлом `backend/requirements.lock`, а base images — digest-ами. CI выполняет frontend/backend checks, тесты, bundle budget, production audits и сборку обоих images. Единственное точечное исключение `pip-audit` — `GHSA-8pqf-f4m5-798g`: advisory относится к Twisted IMAP server, который приложение не запускает; исправленной версии на дату проверки нет. Любая другая находка продолжает останавливать pipeline.

Query-budget regressions фиксируют два SQL-запроса для user list и один для `managed_chat_ids`. Email нормализуется в lowercase и уникален на уровне БД; transactional email ставится в Celery с синхронным fallback при недоступности broker.
