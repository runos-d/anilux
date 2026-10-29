# Контракты измерений всех активностей

Начальные сценарии для [roadmap](SCALABILITY_ROADMAP_2026-10-29.md). Числа ниже — предлагаемые профили синтетического стенда, а не замеры или прогноз аудитории. Каждый профиль запускается отдельно cold/warm, затем в смешанном сценарии; автономные microbenchmarks не складываются в ёмкость сайта.

| Домен | Реальный сценарий | Данные/интенсивность начального профиля | Обязательная проверка |
|---|---|---|---|
| Главная/SEO/календарь | Гость открывает главную, карточку/канонический URL, месяц календаря | 10k и 100k anime; 1 действие/10 с; 1k обновлений каталога | Cold HTML/API, актуальная видимость, URL/status/canonical, негативный slug |
| Каталог/поиск | Фильтр/сортировка, ввод 3 символов, отмена предыдущего запроса, следующая страница | 20/100 карточек; 2 ввода/с; 100k anime; страницы 1/100/1000 | Ограниченные результаты/SQL; 0 персональных полей в shared cache; search ACL |
| Лента/посты | Чтение 20 карточек, прокрутка 200 страниц, публикация/редактирование/удаление | 60k/1m posts; 1 read/5 с; 1 публикация/5 мин; авторы 10/100k followers | Cursor stability, bounded DOM/RAM, visibility change немедленно скрывает post |
| Комментарии/реакции | Открыть ветку, ответить, повторить команду после timeout, снять реакцию | 10k comments/post; 1 reaction/30 с; горячий post 100 actions/с | Idempotency, counts/revision, permission/unique constraints, hot-row latency |
| Библиотеки/плейлисты | Страница пользователя, фильтр, добавить/убрать anime, private/public list | 10k library/user; 10k items/list; 1 read/10 с; 1 write/мин | Owner isolation, bounded page, public IDs, cache invalidation |
| История/рекомендации | Открыть рекомендации cold/warm; progress каждые 15 с; очистить историю | 100k progress rows/user; 1 read/мин; replay повторной записи | Быстрый fallback; очищенная история не возвращается из проекции/поиска |
| Чаты/присутствие | Global+room, send/read/edit/delete, typing, reconnect/replay | Rooms 2/60/500/2000/10000; 1 send/мин/user; typing 2/с с coalesce; 1 read/5 с | ACK после SQL commit; уникальные доставки; текущие session/account/ACL на следующем действии/доставке; ban/clear/prejoin |
| Уведомления | Входящее событие, список, read/mute; scheduled episode/reminder | 10k notifications/user; fanout 1/1000/100k; провайдер с 429 | Dedupe, mute/consent, bounded batches/retry/backlog age |
| Файлы/видео | Загрузка, обработка, private fetch/Range, отзыв доступа во время просмотра | 1/25/250 MiB; 0.1/1/10 uploads/с; video 1/4/8 Mbit/s | Квоты, bounded memory/disk/FFmpeg, Range 206/416, revoke на следующий fetch |
| Импорт/экспорт | Импорт 100/10k записей, повтор задачи, экспорт/expiry | Провайдер 100мс/2с/timeout/429; 1/10 jobs | API 202, отдельный worker/connection budget, не терять progress/retry |
| Модерация/админка | Ban/delete/hide во время чтения/поиска/replay | 1/10 commands/с, 100k pending records | Текущие права на primary, быстрое удаление из публичных выдач |
| Аналитика | Согласие/отказ, batch ingestion, отчёт/удаление данных | 1 event/10с/user; пачки 10/100; 1m synthetic events | Согласие до сбора, bounded retention, отчёты вне API/events worker |

Начальная смесь: 35% catalog/home/search, 20% feed/posts/comments, 15% libraries/playlists/history, 10% recommendations, 10% chats/read, 5% notifications, 3% upload/status, 2% moderation/import/admin/analytics. Это доли **действий**, не HTTP-запросов: сохранять HTTP amplification и клиентские доставки на действие. Chat sends/typing/progress задаются отдельными rates, независимо от read RPS.

Приёмочные ступени: smoke → 120 → 1000 → 6000 → 10000 → 100000 активных пользователей; миллион только после успешных предыдущих и расчёта трафика/записи. Для каждого: 10мин ramp, 60мин mix, 6–24ч soak; reconnect 10/50/100% с jitter, замедление/потеря API, Redis, broker и primary. Не запускать недоказанную следующую ступень, если растёт backlog/ошибки; сохранить результат и откатить только тестовый эксперимент.

К каждому evidence JSON прилагать git SHA и dirty diff digest, immutable image IDs, CPU/RAM/IO/network/FD лимиты, версии DB/broker, объём данных и распределение комнат, число пользователей/вкладок/WS, предложенный/завершённый RPS, sends/deliveries/с, уникальные ACK/получателей, ошибки/429/403 отдельно, p50/p95/p99, outbox oldest age и queue lag во времени. CPU/RAM/network генератора и p99 scheduler delay обязательны: при его насыщении нельзя объявлять предел backend. При отказе не скрывать запросы retries.

Существующий новый `public-http-smoke` автоматизирует только анонимные HTTP чтения. Остальные строки — явный backlog автоматизации, а не уже выполненные сценарии. Для browser cold/warm использовать production frontend, фиксированные CPU/network/device профили и отсутствие накопления DOM/heap в длительной сессии.
