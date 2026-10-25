---
id: bootstrap-audit
title: 'Bootstrap: происхождение, расхождения и долг'
status: draft
date: '2026-10-11'
tags:
- knowledge-management
- documentation
- guardrail
kms-generated: true
---

Скан: исходные Markdown-документы, история git (последние 40 коммитов и целевой поиск), build/Compose/settings, tests/scripts. Рабочая ветка `chat-system-rebuild`, HEAD `64d0197`; незакоммиченный код учитывается как наблюдение, не как принятое решение. Ранее каталогов artifacts и project AGENTS/LOCAL_INSTRUCTIONS не было. За пределами manifest не копируются внешние API-справочники.

Существующих типизированных guardrail/skill файлов не найдено: аудит missing governed-by/grounded-in/derivation-note и извлечение встроенных в них таблиц/дефолтов имеют пустой исходный набор. Ограничения из планов и инструкций извлечены как draft decisions/facts; исходники не переписаны. Встроенные рекомендации аватарок и budgets сохранены в F0017/F0019/F0020. Step 8 добавляет пять шаблонных guardrails с намеренным TBD-долгом; другие guardrails в этом проходе не утверждались.

| Долг | Наблюдение / правило | Предлагаемое основание и действие |
| --- | --- | --- |
| B01 | D0001–D0018 draft; нет accepted-by | Доменные владельцы классифицируют и принимают; мотивация bootstrap не заменяет полное решение |
| B02 | F0001, F0005, F0011, F0019 и docs-manifest без собственного governing intent | governed-by: TBD; связать после review, для F0019 нужен intent о бюджете импорта |
| B03 | Факты с governed-by Dxxxx ссылаются на draft | Не трактовать их как подтверждение принятой политики; environmental - наблюдения кода, decision facts требуют review |
| B04 | no-redundant-guardrails без declared derivation | governing TBD; grounding TBD; кандидат - будущее решение о границах процедур; note: локальное правило процедуры должно жить в ней, если нет системного intent |
| B05 | no-unenforced-guardrail без declared derivation | governing TBD; grounding TBD; кандидат - будущее решение о согласованности нормы и процедуры; note: required behavior должен присутствовать в исполняемой процедуре |
| B06 | one-statement-one-job без declared derivation | governing TBD; grounding TBD; кандидат - будущее решение о независимой актуализации утверждений; note: независимые утверждения разделяются для отдельного управления |
| B07 | tags-from-canonical-list без declared derivation | governing TBD; grounding: tags после review; кандидат - решение о едином словаре; note: общий словарь исключает неуправляемые синонимы |
| B08 | token-economy без declared derivation | governing TBD; grounding TBD; кандидат - решение о бюджете контекста; note: краткие процедуры уменьшают повторную стоимость чтения |
| B09 | Drift README, post plan, SEO, avatars и старых chat prompts | F0011/F0009/F0015/F0016; сверить текущий код, сохранить историческую границу отчётов; D0010/D0014 не финализировать до сверки |
| B10 | Unit/transport/browser/schema/build проверки должны сопровождать затронутые изменения | D0009; механизмы есть, общего обязательного CI запуска не найдено; кандидат - pipeline для изолированной MySQL/Redis и build |
| B11 | Сверять сохранность данных и restore перед migration/cutover | D0004; scripts есть, обязательного release gate нет; кандидат - rehearsal + fingerprint/row/link comparison |
| B12 | Один канонический noindex-порог и подтверждённый bot response | D0010; документы конфликтуют, обязательной bot/boundary-проверки не найдено; сначала выбрать политику, затем автоматизировать |
| B13 | Видимость/команды одинаковы через все входы; API/TS контракты не расходятся | D0003/D0005/D0006; точечные tests есть, полной автоматически проверяемой матрицы и генерации контрактов не найдено; кандидат - cross-transport/schema checks |
| B14 | Для avatar conventions есть проверяемый lookup и валидные файлы | D0014; инструкции расходятся с helper, автоматического полного inventory check не найдено; сначала выбрать реальный путь/форматы, затем проверить |
| B15 | Manifest, tags, indexes и derivation должны оставаться актуальными | governing TBD; механизм kms capture/lint есть, постоянного repo gate нет; кандидат - структурный валидатор и проверка watch paths |
| B16 | UTC storage и local display reminders | D0015/F0021; в старом отчёте runtime-проверка открыта; кандидат - timezone/beat-тест, adoption после сверки |
| B17 | Явные внешние HTTP-таймауты | D0018/F0022; в коде есть значения, общего enforced transport gate не найдено; кандидат - mock timeout/retry тесты ключевых клиентов |

Словарь tags создан из документации и seed vocabulary. Активных решений 0, поэтому umbrella-маркеров нет. Все original doc sections включены в docs-manifest; last-verified оставлен пустым для capture. Новые artifacts индексируются отдельно, manifest не индексирует сам себя. Расхождения и TBD - ожидаемые результаты bootstrap, не свидетельство здоровой финализированной базы.

Для версионирования docs/skills добавлены узкие исключения в .gitignore: прежний шаблон skills/ скрывал этот каталог. Структурная проверка YAML, IDs/ссылок, тегов, нумерации, индексов, watch paths и соответствия seed-шаблонов прошла; 48 документов, 294 раздела. Это проверка artifacts, а не runtime-приёмка или полный kms lint.
