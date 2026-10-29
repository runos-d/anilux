---
id: F0055
title: Рейтинговый курсор удерживает ограниченное окно ID с актуальной видимостью
status: active
date: '2026-10-29'
tags: [posts, performance, api-contracts, access-control, verification]
kind: implementation
governed-by: D0006
---

`post_feed.page` оставляет follows/groups в SQL, не загружая весь граф в Python. Mutable ranking фиксирует до 200 ID в сжатом подписанном viewer-bound cursor; затем продолжает keyset. Каждая страница заново проверяет текущую видимость. Внутри окна изменение реакций не пропускает unread post; глобальный порядок за окном не заморожен. Полного списка всех ID в БД/cache нет. 45 site-rebuild tests PASS, включая границу окна/приватность/owner.
