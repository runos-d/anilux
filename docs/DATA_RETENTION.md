# Матрица хранения данных AniLux

Статус на 27 октября 2026 года. Значение «до удаления аккаунта» описывает текущий программный lifecycle, а не утверждённый юридический срок. Строки `не утверждено` являются release blockers, а не обещанием пользователю.

| Категория | Цель и источник | Получатели | Текущий срок | Удаление | Экспорт |
|---|---|---|---|---|---|
| Аккаунт и профиль | вход, профиль; пользователь | AniLux, auth/email providers по выбору | до удаления аккаунта; юридические исключения не утверждены | unified account cleanup + физические avatar/cover files | да, `profile` |
| Django/JWT сессии | аутентификация; сервер | AniLux | до expiry/logout/account deletion | session delete; refresh tokens blacklist и cascade | нет, security credential |
| Security/access logs | безопасность; web/app/database infrastructure | оператор и инфраструктура | **не утверждено** | инфраструктурная ротация должна быть документирована | обычно нет; порядок ответа по запросу не утверждён |
| Сообщения | общение; пользователь | участники чата, AniLux | до удаления/удаления аккаунта по текущим FK; исключения целостности не утверждены | cascade/команды чата, physical attachments cleanup | только сообщения, автором которых является субъект |
| Посты и комментарии | публикация; пользователь | аудитория по visibility | до удаления материала или аккаунта | cascade и file cleanup | комментарии — да; посты пока не выделены отдельной категорией export |
| Медиа и вложения | функции профиля, постов, чатов | аудитория по access rules, storage | вместе с владеющей записью | Django Collector inventory + storage delete | metadata/content coverage зависит от категории; требует расширения |
| Библиотека и watch history | прогресс и рекомендации; действия пользователя | AniLux | до удаления пользователем/аккаунта | API delete или account cascade | да, `history`/`favorites` |
| Рекомендации | персонализация; library/history | AniLux | производная до обновления snapshot; точный срок **не утверждено** | refresh/cascade; отдельный регламент нужен | исходные history/favorites — да |
| Настройки и consent | работа интерфейса и фиксация выбора; пользователь | AniLux | до изменения/аккаунта; local consent до очистки/смены версии | settings/account cascade; local reset; provider cleanup | да, `settings` |
| Product analytics | улучшение продукта; только после consent | включённый provider | provider retention **не утверждено**, production disabled | revoke/reset; provider-side срок требует настройки | не в account export: данные не содержат User-ID |
| Error/performance telemetry | надёжность/скорость; только после consent | включённый provider | provider retention **не утверждено**, production disabled | revoke/reset; provider-side срок требует настройки | не в account export: данные не содержат User-ID |
| Data exports | реализация права доступа; запрос пользователя | только владелец | 168 часов по умолчанию (`DATA_EXPORT_TTL_HOURS`) | ежедневная expiry-задача + удаление файла; account cleanup | сам ZIP |
| Provider cookies/local keys | необязательная аналитика; provider после consent | включённый provider | срок SDK **не утверждено** | известные `_ym*`/`_ga*` удаляются при revoke | нет |
| Push subscriptions | доставка уведомлений; browser/OS | push provider | до unsubscribe/account deletion; provider срок **не утверждено** | endpoint revoke/cascade | в текущий export не входит |
| Резервные копии | восстановление | инфраструктура/оператор | **не утверждено** | ротация и процедура удаления требуют решения | не выдаются напрямую; восстановленные данные подчиняются основному lifecycle |

## Обязательные решения до production analytics

- утвердить оператора и инфраструктурную юрисдикцию;
- установить сроки для security logs, backups, закрытых support records и recommendation snapshots;
- выбрать provider retention и отключить ненужные provider features;
- подтвердить получателей и трансграничные передачи;
- определить юридически необходимые audit records после удаления, либо подтвердить их отсутствие;
- расширить export coverage для постов, файлов и push metadata либо явно обосновать исключения.
