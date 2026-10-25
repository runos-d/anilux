---
id: F0033
title: PWA использует один service worker с подтверждаемым обновлением
status: active
date: '2026-10-13'
tags: [frontend, notifications, verification]
kind: environmental
governed-by: TBD
---

vite-plugin-pwa создаёт manifest.webmanifest и sw.js; отдельные public/manifest.json и public/sw.js удалены. Регистрация единственная, режим prompt: новая версия ждёт действия пользователя. Оболочка SPA и её chunks предкэшируются вместе; новые вложенные маршруты открывают оболочку без сети. Публичные списки используют существующий IndexedDB-кэш с ограничением в сутки; API, личные сообщения и приватные медиа не попадают в Cache Storage.

Установка и управление уведомлениями доступны на /app. Серверная Web Push отправка работает с VAPID, настройками типов/тихих часов и отключением истёкших подписок. Пара ключей создаётся один раз scripts/setup_web_push.py в игнорируемом .env. Проверены реальные подписка, доставка при закрытой странице и отключение в Chrome и Edge. Нативная установка на физическом телефоне не проверялась.

При отказе установки worker /app показывает ошибку сохранения файлов и кнопку повторной подготовки; при отказе обновления сохраняет прежнюю офлайн-версию. Подтверждённое обновление ждёт controllerchange и перезагружает документ, включая клиента после первого открытия, с таймаутом активации 15 секунд. Проверены реальные install-event failure/recovery и смена worker в Chrome/WebKit, мобильные online/offline состояния WebKit. Старый открытый документ нужно один раз перезагрузить для получения исправленного обработчика.

Источники: frontend/vite.config.ts; frontend/src/sw.ts; frontend/src/composables/usePwa.ts; frontend/src/lib/devicePush.ts; backend/apps/notifications/presentation/views/push_views.py; backend/apps/notifications/application/celery_tasks.py; docs/API_PWA_REVIEW_2026-10-13.md.
