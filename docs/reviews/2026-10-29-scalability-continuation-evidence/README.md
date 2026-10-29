# Продолжение локального roadmap, 29 октября

Ветка `codex/scalability-roadmap`; production/main не переключались. Сохранены синтетические volumes и исходный failed evidence. Общий Docker Desktop 8 CPU, рабочие контейнеры продолжают работать. Ресурсы и dataset — в manifests/resources каждого прогона; observer отдельный. Это **не подтверждение 6000/миллиона**.

| Профиль 120 users / 240 WS / 4 API, 10 HTTP/s + 1 send/s, 60с | HTTP p95/p99, мс | Chat p95/p99, мс | Доставка |
|---|---|---|---|
| `baseline-addressed`, instrumented `3576edd` | 356/615 | 3190/3880 | 7200/7200; SLO/smoke FAIL |
| `union-users`, experimental tracked diff в manifest | 154/239 | 681/895 | 7200/7200; smoke PASS, p95 SLO FAIL |

Оба: 600/600 HTTP 200, 60 ACK, duplicates/unexpected/frame errors/drops = 0. Generator scheduler p99 10/6мс, CPU 5,55/3,84с, RSS ~52MiB. Dataset 120 users/3000 anime/10000 posts, две комнаты по 60 плюс broker-probe rooms, история растёт. Перезапуск API меняет cache/process state; последовательные короткие результаты не дают универсального коэффициента ускорения.

`phases.json` — deltas всех четырёх реплик только внутри load window (51/56с между observer samples); p95/p99 — **верхние границы histogram buckets**, не точные процентили. Вложенные work/connection/SQL/prepare/serialize/send не суммируются. У baseline mean global publication-to-handler ~754мс, room ~57мс; executor ~2мс, formatter/JSON <2мс; worker fanout mean ~126мс. После union global ~30мс, room ~33мс, projection callbacks 373→144 за разные sampled windows. Вклад transport подтверждён изменением pipeline и полным повтором; одного queue snapshot для вывода не использовали. Remaining correlated unread SQL и DB connections требуют дальнейшей работы.

Проверки реализации: 24 initial transport/session/projection checks (5,833с), затем 63 native Redis/fallback/privacy/revocation/history/delivery checks (21,204с). Дополнительно реальные Redis multicast → global+room → успешная доставка → удаление Django Session или membership → повтор старого event: защищённый payload не доставляется. Два таких security tests, три native Redis tests и четыре независимых media-inventory tests: 9 PASS (3,007с). Инвентаризация медиа — отдельная следующая поставка, не часть load image принятого сравнения.

`manifest.json` хранит фактический image/diff; новые результаты не приписываются image предыдущей сессии. Worker logs содержат только фазы/event IDs/counts, без payload/credentials. Исходные ignored artifacts остаются в `.tmp/scalability`.
