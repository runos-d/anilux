# Продолжение локального roadmap, 29 октября

Ветка `codex/scalability-roadmap`; production/main не переключались. Сохранены синтетические volumes и исходный failed evidence. Общий Docker Desktop 8 CPU, рабочие контейнеры продолжают работать. Ресурсы и dataset — в manifests/resources каждого прогона; observer отдельный. Это **не подтверждение 6000/миллиона**.

| Профиль 120 users / 240 WS / 4 API, 10 HTTP/s + 1 send/s, 60с | HTTP p95/p99, мс | Chat p95/p99, мс | Доставка |
|---|---|---|---|
| `baseline-addressed`, instrumented `3576edd` | 356/615 | 3190/3880 | 7200/7200; SLO/smoke FAIL |
| `union-users`, experimental tracked diff в manifest | 154/239 | 681/895 | 7200/7200; smoke PASS, p95 SLO FAIL |
| `indexed-projection`, social.0039 + viewer IDs | 150/196 | 598/791 | 7200/7200; smoke PASS, p95 SLO FAIL |
| `discarded-redundant-acl`, **удалённый эксперимент** | 136/264 | 615/787 | 7200/7200; p95 не улучшен |

Оба: 600/600 HTTP 200, 60 ACK, duplicates/unexpected/frame errors/drops = 0. Generator scheduler p99 10/6мс, CPU 5,55/3,84с, RSS ~52MiB. Dataset 120 users/3000 anime/10000 posts, две комнаты по 60 плюс broker-probe rooms, история растёт. Перезапуск API меняет cache/process state; последовательные короткие результаты не дают универсального коэффициента ускорения.

`phases.json` — deltas всех четырёх реплик только внутри load window (51/56с между observer samples); p95/p99 — **верхние границы histogram buckets**, не точные процентили. Вложенные work/connection/SQL/prepare/serialize/send не суммируются. У baseline mean global publication-to-handler ~754мс, room ~57мс; executor ~2мс, formatter/JSON <2мс; worker fanout mean ~126мс. После union global ~30мс, room ~33мс, projection callbacks 373→144 за разные sampled windows. Вклад transport подтверждён изменением pipeline и полным повтором; одного queue snapshot для вывода не использовали. Remaining correlated unread SQL и DB connections требуют дальнейшей работы.

Проверки реализации: 24 initial transport/session/projection checks (5,833с), затем 63 native Redis/fallback/privacy/revocation/history/delivery checks (21,204с). Дополнительно реальные Redis multicast → global+room → успешная доставка → удаление Django Session или membership → повтор старого event: защищённый payload не доставляется. Два таких security tests, три native Redis tests и четыре независимых media-inventory tests: 9 PASS (3,007с). Инвентаризация медиа — отдельная следующая поставка, не часть load image принятого сравнения.

`manifest.json` хранит фактический image/diff; новые результаты не приписываются image предыдущей сессии. Worker logs содержат только фазы/event IDs/counts, без payload/credentials. Исходные ignored artifacts остаются в `.tmp/scalability`.

`indexed-projection`: 75 regression tests PASS (29,775с), drift отсутствует. В warm single-call probe на 60 viewers/359 messages последний unread SQL 61,6→44,6мс после индекса; EXPLAIN `ALL/Range checked for each record`→`ref/message_unread_scan/Using index`. [До](projection-before-index.json), [после](projection-after-index.json). Это одна локальная microprobe с cProfile, не оценка устойчивого ускорения. Subsequent macro включает также viewer IDs вместо полных профилей и более длинную историю; chat p95 ещё >500мс. Индекс не устраняет зависимость точного unread count от длины истории. Production migration требует штатной backup/restore и оценки времени DDL на реальном объёме; она здесь не выполнялась.

Эксперимент без отдельного ACL callback перед полной current projection прошёл 84 regression tests (119,596с), но не улучшил end-to-end p95. [Patch/результат/решение](discarded-redundant-acl/disposition.json) сохранены, runtime-код возвращён к явному ACL pipeline; это не регрессия, доказанная статистически, и не retained optimization. На возвращённом коде ещё 6 real Redis/security tests PASS (4,347с), включая rich reply → ban → old replay без доставки.

[Reconnect/rich replay](reconnect-rich-replay/result.json): 5 offline messages, 4 quoted replies, idempotent duplicate command, reconnect, HTTP replay без дублей, cross-room denial, текущие edits/deletions PASS. Это небольшой функциональный сценарий, не acceptance больших комнат, mass reconnect или rich fanout.

Общий unread подсчёт был проверен ещё в трёх **удалённых** вариантах: [ORM](discarded-grouped-orm/result.json) 2281/3030мс, [ORM + command timing](discarded-grouped-orm-command/result.json) 3051/3437мс, [fixed parameterized SQL](discarded-grouped-raw/result.json) 2357/2816мс. Все 7200 доставки получены, но smoke/SLO FAIL. SQL microprobe стал дешевле; при этом выросли CPU пики API и ACK (в двух последних p95 2560/1657мс). Command work/connection/SQL теперь измеряются отдельно. Из этих последовательных прогонов нельзя заключить, что один SQL query является причиной всех хвостов; server/host scheduling и pre-publication pipeline ещё требуют профиля. Все три reader patches удалены, текущий код сохраняет `a34ba3b` reader/индекс. Disposition/patch/manifests/resources и failed results сохранены, новые equivalence tests разных sender/read/clear/join bounds оставлены как регрессии.

На возвращённом reader: 19 telemetry/projection/real Redis security checks PASS (13,295с). Безопасность и отсутствие избыточного SQL не заменяют capacity acceptance.

## Более длинный профиль и восемь API

| Retained code, 120 users/240 WS, 10 HTTP/s + 1 send/s | HTTP p95/p99 | ACK p95/p99 | Chat p95/p99 | HTTP / ACK / unique deliveries |
|---|---|---|---|---|
| [4 API, 300с](soak-300-four-api/result.json) | 315/952мс | 5449/7483мс | 5998/8177мс | 3000/3000; 300/300; 36000/36000 |
| [8 API, 60с](mixed-120-eight-api/result.json) | 179/269мс | 255/421мс | 714/1079мс | 600/600; 60/60; 7200/7200 |

В обоих duplicates/unexpected recipients/socket closures/frame errors/generator drops = 0. Первый smoke/SLO **FAIL**, второй smoke PASS, строгий SLO **FAIL**. 4 API по 1 CPU/1GiB, затем 8 с теми же лимитами; увеличенная сумма CPU ceilings делит тот же 8 CPU host с DB/workers и другими сервисами. Кеши/history/process placement отличаются, коэффициент ускорения не заявлен. Это 5 минут, не требуемые 30–60 минут/full-domain/weak-client/storm acceptance.

Generator: 300с — scheduler p99 10мс, CPU 24,8с/RSS 55MiB; 60с — 9мс, CPU 4,36с/RSS 53MiB. [58 наблюдений длинного прогона](soak-300-four-api/resources-summary.json): outbox pending ≤1, oldest ≤0,137с, DB connections 1..9; dataset messages 666→960 внутри sample window. В 8 API — 11 snapshots, pending 0, connections 1..7, messages 968→1021. Это редкие snapshots, не доказательство отсутствия коротких spikes. Raw resources сжаты в `resources.jsonl.gz`, исходные JSONL сохранены ignored; manifests/phase histograms доступны рядом. Длинный ACK хвост и насыщение отдельных API требуют дальнейшей работы; малый sampled outbox не объясняет задержку сам по себе.

## Реплика и восстановление брокера

[Replication evidence](replication/): новый private volume, source/replica server-id 101/102, согласованный file/position dump 8394461 bytes, SHA-256 и совпавшие counts/checksums шести таблиц. Bootstrap result сохраняет source/image/resources fingerprints; SQL dump с synthetic sessions **не опубликован**. Recover: остановленный applier отстаёт, resume достигает checkpoint, application write отвергнут, restart сохраняет read-only и одну обновлённую строку — PASS, 8,328с. Повторный bootstrap непустой schema **ожидаемо отвергнут** (отдельный `passed=false`/RuntimeError report), данные не перезаписаны. Три host guard tests и два phase summary tests PASS (0,013с).

[Paused broker](replication/outbox-paused-recovery.json) после новых chat изменений: durable SQL остался pending, unpause/retry опубликовали outbox, duplicate task безопасна; producer/recovery CLI 4,141/2,407с с Docker/Django startup. Защита finally снимает pause. Это публикация в transport, не доказательство получения клиентом.

Ни один API/ACL/session read не маршрутизируется на replica; writer не продвигался. Это локальная пара на одном host, self-signed lab TLS без production CA identity, без host HA/RPO/RTO/promotion acceptance. Команды/границы: [replication guide](../../../deploy/scalability/REPLICATION.md).
