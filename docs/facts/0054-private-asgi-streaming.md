---
id: F0054
title: Приватные chat и post файлы передаются без полной ASGI буферизации
status: active
date: '2026-10-29'
tags: [media, performance, access-control, verification]
kind: implementation
governed-by: D0007
---

`core.file_delivery.private_file_response` использует async iterator с блоками 64 KiB, закрывает файл при завершении/отмене и не читает его для HEAD/416. Chat/post views сохраняют текущие проверки прав и приватные headers; post X-Accel остаётся. Одиночные/suffix Range проверяются с ограничением длины заголовка. Тесты: `core.test_file_delivery`, chat extensions, video cache; active deployment остаётся ASGI.
