---
id: D0030
title: Внешняя аналитика требует явного согласия и не использует идентификацию пользователя
status: active
date: '2026-10-27'
tags:
- frontend
- integrations
- access-control
- data-integrity
- api-contracts
track: product
---

AniLux не загружает внешние analytics SDK и не сохраняет их cookies до явного `granted`. События до согласия отбрасываются, payload ограничен типизированным allowlist, а route tracking не содержит query, fragment и raw params. User-ID, хешированный ID, Webvisor/session replay и рекламная персонализация запрещены в первой версии. Яндекс Метрика является первым поддержанным, но выключенным до production-конфигурации провайдером; Google Analytics остаётся независимым opt-in адаптером.

Экспорт и удаление принадлежат тому же privacy boundary: экспорт содержит только данные субъекта и живёт ограниченный TTL, а аккаунт удаляется одним немедленным подтверждённым workflow с очисткой БД, credentials и файлов. Включение production provider отложено до утверждения оператора, инфраструктуры, получателей и сроков хранения.
