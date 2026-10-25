---
id: configured-public-brand
title: Пользовательский бренд и публичные адреса берутся только из конфигурации
status: active
date: '2026-10-19'
tags:
- release
- environment
- guardrail
governed-by: D0029
grounded-in: F0043
---

## Guardrail

Новые пользовательские тексты, письма, sender addresses и ссылки не содержат рабочие имена репозитория или продукта. Код использует `PROJECT_BRAND_NAME`, `FRONTEND_PUBLIC_URL` и полный `TRANSACTIONAL_FROM_EMAIL`; production startup отклоняет placeholder-домен, localhost, Mailpit и неполные Brevo credentials.

## Enforcement

`backend/config/settings.py` валидирует production-конфигурацию, а `apps.users.application.email_service` является единственной точкой формирования транзакционных писем.
