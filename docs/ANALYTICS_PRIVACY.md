# Аналитика, согласие и управление пользовательскими данными

Актуально на 27 октября 2026 года. Документ описывает реализованный технический контракт. Он не заменяет юридическое утверждение целей обработки, реквизитов оператора и сроков хранения.

## Граница аналитики

Аналитика выключена по умолчанию. `src/analytics/core.ts` начинает с no-op адаптера и не создаёт provider script, cookie или очередь событий при состояниях `unknown` и `denied`. События до согласия отбрасываются без последующей отправки. Ошибка SDK изолирована от приложения.

Согласие имеет состояния `unknown`, `granted`, `denied`, версию `2026-10-27.1`, время решения и источник. Гостевое решение хранится в `localStorage` под ключом `anilux.analytics.consent`. Для вошедшего пользователя оно синхронизируется через:

- `GET /api/users/privacy-settings/me/`;
- `PATCH /api/users/privacy-settings/me/`.

Локальный отказ применяется сразу, даже если backend недоступен. Изменение версии политики сбрасывает старое решение в `unknown`. Отзыв удаляет подключённые scripts, известные provider cookies и local keys. UI доступен в consent banner и в настройках конфиденциальности.

## Провайдеры и конфигурация

Яндекс Метрика включается только при одновременно заданных `VITE_YANDEX_METRIKA_ENABLED=true` и валидном числовом `VITE_YANDEX_METRIKA_ID`. Webvisor, clickmap, trackLinks и User-ID выключены.

Google Analytics — отдельный, выключенный по умолчанию адаптер. Для него нужны `VITE_GOOGLE_ANALYTICS_ENABLED=true` и валидный `VITE_GOOGLE_ANALYTICS_ID`. Рекламное хранилище, Google Signals и персонализация рекламы выключены; автоматический page view отключён.

Разрешённые внешние адреса:

| Назначение | Адреса |
|---|---|
| Yandex script/connect/img | `https://mc.yandex.ru`, `https://mc.yandex.com` |
| Google script | `https://www.googletagmanager.com` |
| Google connect/img | `https://www.google-analytics.com`, `https://region1.google-analytics.com` |

Они перечислены явно в CSP (`backend/config/middleware.py`). Новому провайдеру необходимы отдельный адаптер, consent reset при изменении целей/получателей, обновление CSP и этого документа.

## Каталог данных

Payload проходит default-deny sanitizer до каждого адаптера. Неизвестное событие, поле, enum или значение отклоняется; в development/test это явная ошибка.

| Событие | Разрешённые поля | Когда отправляется |
|---|---|---|
| `filter_applied` | группа фильтра, число активных фильтров | пользователь применил каталоговые фильтры |
| `card_opened` | безопасная категория источника | открытие карточки из известного раздела |
| `playback_started` | категория точки входа | реальное событие play плеера |
| `episode_selected` | `season` или `episode` | фактическая смена выбора |
| `library_status_changed` | нормализованный статус | успешный ответ create/update/delete API |
| `playlist_created` | `public`, `private`, `unlisted` | успешное создание |
| `post_published` | `none`, `image`, `video`, `mixed` | успешная публикация |
| `technical_error` | стабильный код, route template | browser error без объекта ошибки/stack |
| `performance_metric` | имя метрики, диапазон | navigation/LCP/CLS/INP без raw user data |

Запрещены email, телефон, nickname, user ID, токены, cookies/headers, сообщения, комментарии, тексты и значения форм, поиск, query/fragment, имена файлов, DOM-текст, stack traces и произвольные URL. Хеш пользовательского идентификатора также не допускается.

Router tracking работает после успешного `afterEach`, использует только route name в шаблоне `/route/<name>`, нормализует динамические профили/чаты и исключает OAuth, подтверждение email, reset password, invites, shared tokens, admin и moderation. Query, fragment и реальные params не читаются.

## Экспорт и удаление

Экспорт имеет состояния `queued`, `processing`, `ready`, `expired`, `failed`, `canceled`. Архив создаётся Celery-задачей, содержит manifest и только выбранные данные субъекта. Сообщения экспортируются только при авторстве пользователя; чужие контакты, email и телефоны не включаются.

- `GET/POST /api/users/export-data/` — список и создание;
- `GET/DELETE /api/users/export-data/<id>/` — статус и отмена;
- `GET /api/users/export-data/<id>/download/` — owner-only ZIP с `private, no-store`.

Архив удаляется после `DATA_EXPORT_TTL_HOURS` (по умолчанию 168 часов) вместе с физическим файлом.

Удаление аккаунта имеет один контракт: `POST /api/users/account-deletion/` с паролем, `final_confirmation: true` и кодом 2FA, если 2FA включена. Оно немедленно и необратимо удаляет каскадные записи, push subscriptions, Django sessions, outstanding refresh tokens, файлы и экспортный каталог. `DELETE /api/users/me/` возвращает 405. Cleanup идемпотентен по отсутствующему user ID.

## Проверки и эксплуатация

Перед выпуском:

```text
cd frontend
npm run type-check
npm run check:analytics-architecture
npx vitest run src/analytics

cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.users.test_privacy_data_management --keepdb
```

`check:analytics-architecture` запрещает `ym`, `gtag`, `dataLayer` и прямые provider scripts вне adapters. CI запускает эту проверку. Provider IDs не должны попадать в репозиторий и fixtures.

Production-включение заблокировано до подтверждения реквизитов оператора, местоположения инфраструктуры, применимых правил локализации/трансграничной передачи, утверждённой retention matrix, перечня получателей и решения о необходимости Google Analytics.
