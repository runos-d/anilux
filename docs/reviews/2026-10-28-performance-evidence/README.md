# Материалы повторного ревью

Отчёт: [performance review](../2026-10-28-performance-review.md).

## Результаты

- `browser-routes.json`: 72 маршрута, desktop и 390 px; fixtures, 0 pageerror, 3 overflow.
- `browser-desktop.json`: первый проход 20 маршрутов, запросы и локальные paint/long tasks.
- `browser-details.json`: полные повторяющиеся URL и виновники mobile overflow.
- `browser-mobile-feed.json`: CPU slowdown ×4 и рост ленты до 160 карточек. Не является benchmark реального телефона; компьютер был занят. В исходном browser session находились два PerformanceObserver, поэтому некоторые записи long tasks дублируются; максимальная длительность и размеры DOM от этого не меняются.
- `browser-watch.json`: запрос пятой серии при `last_episode=12`, выбранная строка первой серии.
- `backend-sqlite.json`: 10 безопасных проб на синтетических данных, включая 500, N+1 и отрицательное кеширование. Текущая схема создаётся напрямую; миграции и MySQL не проверяются этим runner.
- `streaming-result.json`: 8 МиБ синхронного iterator полностью буферизуются до первого блока в Docker-образе с Django 5.2.18.

Время выполнения локальное и зависит от нагрузки компьютера. Fixtures не проверяют настоящий DTO, медиапровайдеров или пропускную способность API. Реальный сервер на :8000 не использовался для нагрузочных запросов.

## Повтор браузерных проб

Из `frontend` запустить имеющуюся production-сборку через установленный Vite:

```powershell
.\node_modules\.bin\vite.cmd preview --host 127.0.0.1 --port 4398 --strictPort
```

В другом терминале открыть отдельную сессию и выполнить выбранный fragment из корня проекта:

```powershell
playwright-cli -s=animecore-performance open about:blank --browser chromium
& docs/reviews/2026-10-28-performance-evidence/run-browser-probe.ps1 -Probe all-routes
& docs/reviews/2026-10-28-performance-evidence/run-browser-probe.ps1 -Probe details
& docs/reviews/2026-10-28-performance-evidence/run-browser-probe.ps1 -Probe watch
& docs/reviews/2026-10-28-performance-evidence/run-browser-probe.ps1 -Probe stress
playwright-cli -s=animecore-performance close
```

Все API-запросы страниц перехватываются локальными fixtures до navigation. Fragment `stress` намеренно создаёт растущую тестовую ленту. Запускать его отдельно от измерения серверной производительности.

## Backend без рабочей базы

Из корня проекта, с Python и зависимостями backend:

```powershell
$auditRoot = (Get-Location).Path
$env:DJANGO_SETTINGS_MODULE = 'audit_settings'
$env:PYTHONPATH = "$auditRoot/docs/reviews/2026-10-28-evidence;$auditRoot/backend"
python -X utf8 -u docs/reviews/2026-10-28-performance-evidence/backend_probe.py
```

Проба отказывается работать вне SQLite `:memory:` или специально названного disposable MySQL `audit-mysql/chat_test`. SQLite-настройки направляют media и exports во временные каталоги, а обращения за скриншотами подменяются. Проба использует обход миграций только для диагностического создания текущей схемы. Программа печатает стадии, промежуточные `MEASURE=` и итоговый `AUDIT_JSON=`; traceback каждые 60 секунд — диагностический таймер, если выполнение затянулось.

`performance_settings.py` сохранён для воспроизводимости попытки Docker/MySQL. Он требует отдельной сети с `audit-mysql`/`audit-redis`, завершённого `migrate` и read-only mount исходников. Эта попытка не дала завершённого нагрузочного результата; не использовать её как доказательство готовности MySQL или миграций. Все созданные в этом проходе контейнеры и сеть удалены.

`streaming_probe.py` не обращается к БД или видео. Для повторения запустить его в нужном backend-образе через отдельный `docker run --rm --network none` с read-only mount этого каталога.
