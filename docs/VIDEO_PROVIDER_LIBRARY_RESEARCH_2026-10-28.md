# Аудит библиотек видеопровайдеров для AniLux

**Дата среза:** 2026-10-28  
**Проект:** [runos-d/anilux](https://github.com/runos-d/anilux), локальный HEAD `61525e51cae39b74b25e7858fedc68e318b19f12`  
**Режим исследования:** статический аудит исходного кода, GitHub API/code search, документация, issues и сохранённые fixtures. Реальные защищённые media endpoints, cookies и токены не запрашивались и не сохранялись.

## 1. Вывод в одном абзаце

Разумного безопасного «универсального пакета для всех аниме-источников» не найдено. Для первого PoC лучшая основа — официальный playback contract AniLibria/AniLiberty через `py-aniliberty`, с собственным тонким `ProviderAdapter`; вторым полезным объектом проверки является `anime-dl-core`, но только его изолированные AniLibria/SovetRomantica/public-VK extractors. Multi-provider проекты полезны прежде всего как архитектурные референсы: значительная их часть зависит от scraping, короткоживущих URL, `Referer`, Cloudflare/Anubis, удалённых дешифраторов или API неизвестного происхождения. Они включены в статистику, в том числе проекты с bypass/decryption, но такие механизмы не рекомендуются и не воспроизводились.

## 2. Цель, границы и терминология

Цель — найти GitHub-проекты, которые могут вернуть воспроизводимый ресурс без зависимости только от Kodik:

- HLS master/media manifest (`m3u8`);
- MPEG-DASH manifest (`mpd`);
- прямой MP4/WebM;
- структурированный набор потоков по качеству/дорожке;
- официальный playback URL или иной разрешённый media endpoint.

В этом отчёте **прямая ссылка** означает не iframe и не страницу просмотра, а URL media resource либо manifest, который плеер может передать HLS/DASH/native-video клиенту вместе с явно описанным playback context: `Referer`, `Origin`, headers, cookies, срок действия, geo/auth/DRM. URL, который работает только после обхода защиты или с чужой сессией, технически является media URL, но юридически и продуктово не считается пригодным для AniLux.

Обозначения доказательности:

- **Код** — поведение подтверждено исходниками на зафиксированном commit.
- **Fixture/test** — есть offline fixture или unit/contract test; это не доказывает, что внешний сайт жив сегодня.
- **Заявлено** — только README/каталог plugin; рабочим не считается.
- **Live не проверялось** — намеренно, если потребовались бы anti-bot, дешифрование, чужие cookies, платный доступ или публикация URL.

Классы:

- **A** — подходит для дальнейшего безопасного PoC.
- **B** — условно подходит после проверки прав, contract и эксплуатационных ограничений.
- **C** — архитектурный референс, не готовая интеграция.
- **D** — отклонён для интеграции; оставлен в полном списке и статистике.

## 3. Исходная архитектура AniLux и требования к адаптеру

Перед поиском проверены Epic [#4](https://github.com/runos-d/anilux/issues/4) и задачи [#15](https://github.com/runos-d/anilux/issues/15)–[#35](https://github.com/runos-d/anilux/issues/35), особенно контракты [#16](https://github.com/runos-d/anilux/issues/16), [#17](https://github.com/runos-d/anilux/issues/17), comparison fixture [#33](https://github.com/runos-d/anilux/issues/33), scrubbed fixtures [#34](https://github.com/runos-d/anilux/issues/34) и integration tests [#35](https://github.com/runos-d/anilux/issues/35).

Фактическая интеграционная поверхность уже удобна для provider layer:

- `Anime` хранит `shikimori_id`, сезоны, серии, переводы и Kodik-поля отдельно: [`anime.py`](../backend/apps/anime/infrastructure/models/anime.py).
- альтернативный resolver уже нормализует AnimeGO/AniBoom/CVH в `translations` и sources, а view отдаёт `streams -> translations -> sources`: [`animego_streams.py`](../backend/apps/anime/infrastructure/clients/animego_streams.py), [`alternative_stream_views.py`](../backend/apps/anime/presentation/views/alternative_stream_views.py).
- собственный frontend-плеер принимает sources, переводы, сезоны и серии: [`AniLuxPlayer.vue`](../frontend/src/components/Players/AniLuxPlayer.vue); Kodik остаётся отдельным iframe/postMessage transport: [`KodikPlayer.vue`](../frontend/src/components/Players/KodikPlayer.vue).

Следовательно, новый provider не должен отдавать «голую строку». Минимальный `PlaybackSource` должен включать `url`, `kind`, `quality`, `container/codecs`, audio/subtitles, `headers`, `cookies_required`, `expires_at`, `drm`, `proxy_policy`, provenance и confidence. Metadata/discovery и ephemeral playback должны быть разными методами и разными cache TTL.

## 4. Методика и ограничения полноты

### 4.1 Что было проверено

1. GitHub repository search, code search, REST/GraphQL API и `gh` по терминам `anime streaming api`, `extractor`, `m3u8`, `mpd`, `provider`, `source`, `player`, `AnimeGO`, `YummyAnime`, `AniLibria`, `AniLiberty`, `Anime365`, `SovetRomantica`, вариантам написания и доменам.
2. Python, TypeScript/JavaScript, Go, Rust, Kotlin и shell; PyPI/npm-проекты только при наличии GitHub source.
3. Frameworks CloudStream/Aniyomi/anipy/yt-dlp/Streamlink, self-hosted API, приложения с выделенными extractors, архивы и активные forks.
4. Для основных кандидатов — clone на exact commit, просмотр моделей результата, provider/player paths, HTTP flow, headers/auth, error taxonomy, tests/fixtures и manifest зависимостей.
5. GitHub activity: archive flag, последний commit, releases, открытые issues/PR. Stars использовались только как контекст, не как доказательство работоспособности.

### 4.2 Безопасные проверки

Unit/live tests сторонних библиотек не запускались: задача требует прежде всего статического аудита, а часть test suites содержит real-network E2E. Зависимости в AniLux не устанавливались. Были просмотрены offline fixtures и tests; реальные media URL из них в отчёт не перенесены. Для официальных клиентов проверен contract в исходниках и документации, но не выполнено воспроизведение контента.

### 4.3 Почему список не называется абсолютно полным

GitHub Search имеет задержку индексации и лимит результатов; private/deleted/DMCA-blocked repositories недоступны; plugin catalogs меняются ежедневно; forks могут не содержать самостоятельного кода; часть проектов скрывает источник за удалённым API. Срез покрывает найденную публичную экосистему по описанной методике, но не может доказать отсутствие неизвестного или нового репозитория.

## 5. Сводная статистика

Проверено **32 самостоятельных репозитория/контракта** в основной таблице и **5 Kodik-only репозиториев** отдельно.

| Класс | Количество | Смысл |
|---|---:|---|
| A | 3 | безопасный следующий PoC |
| B | 5 | условный PoC после правовой/технической проверки |
| C | 8 | архитектурный референс |
| D | 16 | отклонены для интеграции |
| Kodik-only | 5 | исключены по условию задачи |

Для shortlist дополнительно зафиксирован snapshot открытых issues/PR: `py-aniliberty` 0/0, `anime-dl-core` 0/0, `anilibria-api-client` 0/0, `anicli-api` 1/1, AnimeParsers 3/1, yt-dlp 2054/682. Это индикатор очереди, а не качества: нули у маленького нового проекта могут означать низкое использование, а большие числа yt-dlp — масштаб проекта. Для остальных кандидатов archive flag, last push и наличие issue/PR activity проверялись через GitHub API; в таблице оставлен более устойчивый last-push/archive signal, поскольку точные счётчики быстро меняются.

## 6. Сравнительная таблица всех кандидатов

В колонке «Активность» приведён последний push/commit, доступный на момент среза. SHA — точная ревизия аудита. «Нет лицензии» означает отсутствие распознанной OSS-лицензии, а не разрешение на использование.

| Проект | Репозиторий / SHA | Язык | Лицензия | Активность | Подтверждённые non-Kodik источники | Результат | Headers/cookies/runtime | DRM/обход | Тесты | AniLux | Риск | Вердикт |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AniLibria API docs | [repo](https://github.com/anilibria/docs/tree/8ddcb219c6a155633389c11a0fc87e5c75760bbb) `8ddcb21` | Docs/API | нет лицензии на repo | 2025-07-08 | AniLibria | HLS 480/720/1080 | публичный API; auth только для account features | DRM не видно | schema/examples | прямой HTTP adapter | права на API/контент надо подтвердить | **A** contract |
| py-aniliberty | [repo](https://github.com/LLIJIYAPNIK/py-aniliberty/tree/21008bcdc38204e82c103bddd95a73dec29780f2) `21008bc` | Python | MIT | 2026-10-18; v1.0.0 | AniLiberty/AniLibria | HLS qualities | `httpx`, async; публичные playback поля | нет bypass в playback path | extensive unit/integration/cassettes | native Python | новый, один основной maintainer | **A** |
| anime-dl-core | [repo](https://github.com/ialakey/anime-dl-core/tree/f23b7c1b1403c7adc7eaa60ba6323a75e35c9771) `f23b7c1` | Python | MIT | 2026-09-20; v0.5.1 | sources: AnimeGO, AniMedia, Alloha; players: AniLibria, AniBoom, CVH, AniMedia, Sibnet, SovetRomantica, VK | HLS/DASH/MP4 + headers | `requests`; optional aiohttp; часто Referer/Origin | mixed; безопасны не все modules | offline fixtures + live suite | native, хорошая модель | scraper breakage/legal per source | **A** только whitelist modules |
| anilibria-api-client | [repo](https://github.com/whynotix/anilibria-api-client/tree/50ad0564afa95690cfdc66e60afabc1cb6fcbb8b) `50ad056` | Python | Unlicense | 2026-10-26; v1.0.2 | AniLiberty/AniLibria | API models с HLS | aiohttp/async | нет bypass | unit/method tests | native | маленький проект; contract дублирует A | **B** |
| anicli-api | [repo](https://github.com/vypivshiy/anicli-api/tree/ab79153c504dd1e6877749d64c978c362a2936a2) `ab79153` | Python | MIT | 2026-08-22 | AnimeGO, YummyAnime, AniLibria, AniLib.me, AnimeVost, Dreamcast, HDRezka, SameBand; players AniBoom/CVH/Sibnet/Aksor/CSST | structured Video/HLS/DASH/MP4 | httpx, headers/cookies/proxy | есть Anubis anti-bot path | unit + opt-in E2E | native contract полезен | protected sources нельзя включать | **B** только AniLibria; остальное C/D |
| AnimeParsers | [repo](https://github.com/YaNesyTortiK/AnimeParsers/tree/cac4c83e03e43f2829506ef202a1279a4e0b78bf) `cac4c83` | Python | MIT | 2026-09-05; v1.18.0 | AnimeGO (AniBoom/CVH), AniLiberty, Jut.su; Shikimori metadata | HLS/DASH/MP4 | requests/aiohttp, Referer; sync+async | смешанный scraper/Kodik parser | parser tests, часть network | native | хрупкость DOM/player; права | **B** limited |
| AniLibria-Stremio | [repo](https://github.com/PabloKolaso/AniLibria-Stremio/tree/d97c859594516daa2a517782f88efe3fb6737f57) `d97c859` | JS | NOASSERTION | 2026-10-01 | AniLibria | Stremio stream entries/HLS | Node service | официальный API path | нет зрелого contract suite | sidecar/reference | лицензия неясна | **B** |
| yt-dlp | [repo](https://github.com/yt-dlp/yt-dlp/tree/f264a6cbd1f630894da0f368df00f8aae50140e0) `f264a6c` | Python | Unlicense | 2026-10-26; release | ADN, HiDive, Bilibili/Bangumi; также Abema | HLS/DASH/direct formats | service auth/cookies/geo; CLI/library | часть сервисов DRM/спец. license; не обходить | огромная suite | subprocess/library JSON | ToS, geo, paid/DRM, extractor churn | **B** только authorized non-DRM |
| anilibria-app | [repo](https://github.com/anilibria/anilibria-app/tree/a188bfd5e49fd5afee5ff3ec253db92176eaf532) `a188bfd` | Kotlin | GPL-3.0 | 2026-08-17 | AniLibria | HLS playback | Android runtime | нет нужды в bypass для API | app tests/build | reference/sidecar only | GPL, mobile coupling | **C** |
| anipy-cli | [repo](https://github.com/sdaqo/anipy-cli/tree/a293cf1f20c7532d1f06fd18cfe656c3b8e61ebb) `a293cf1` | Python | GPL-3.0 | 2026-09-13 | exported: AnimeHub, AniDBApp; files также AllAnime/AnimeKai | ProviderStream + subtitles/referrer | Python; remote keys/expressions у disabled providers | AES/RC4/decode/eval-like remote rules | ограниченно | interface reference | GPL + remote execution/decryption risk | **C**; unsafe paths D |
| CloudStream | [repo](https://github.com/recloudstream/cloudstream/tree/a7ac454af8fbd64574c96847a936905855911720) `a7ac454` | Kotlin | GPL-3.0 | 2026-10-22 | framework; providers живут в plugins | VIDEO/M3U8/DASH, headers, tracks, DRM flag | Android/Kotlin; optional WebView/interceptor | plugins heterogeneous | framework tests | architecture/sidecar | GPL; no single trusted catalog | **C** |
| Aniyomi extensions (official) | [repo](https://github.com/aniyomiorg/aniyomi-extensions/tree/0ccdcfb44aaa2064e51406e5f168fe73e79a3cc9) `0ccdcfb` | Kotlin | Apache-2.0 | archived; 2024-08-19 | plugin catalog, exact set frozen at commit | video list/qualities | Android extension runtime | provider-dependent | per-extension mixed | architecture only | archived/stale | **C** |
| yuzono/anime-extensions | [repo](https://github.com/yuzono/anime-extensions/tree/2d070ab5f37e7b112279ee875485505fc59e6fe3) `2d070ab` | Kotlin | Apache-2.0 | 2026-10-27 | active Aniyomi plugin catalog | video list/qualities | Android runtime | provider-dependent | CI/catalog | possible miwayomi sidecar | legal/operational variance | **C** |
| miwayomi | [repo](https://github.com/SeoMavares/miwayomi/tree/a3a776ebd26f91f558cd59a4bd57fff9119ee987) `a3a776e` | Kotlin | Apache-2.0 | 2026-08-14 | executes Aniyomi extensions | normalized extension output | separate JVM/backend | inherits plugin behavior | project tests | possible isolated service | large trust boundary | **C** |
| Streamlink | [repo](https://github.com/streamlink/streamlink/tree/7d2b6d6d1cdb0a5692208f37b3413c8f1a0eeda5) `7d2b6d6` | Python | BSD-2-Clause | 2026-10-27 | AbemaTV VOD/live, Bilibili **live** | stream objects/HLS | Python, session headers | Abema custom license/key protocol | mature suite | plugin interface reference | Abema protection; Bilibili not catalog VOD | **C** |
| libanime_schema | [repo](https://github.com/libanime/libanime_schema/tree/3fd812ed593dca7c56ebf5ad878542d58da1df75) `3fd812e` | Python/schema | нет лицензии | 2025-06-29 | schemas, not provider | metadata/schema only | Python | n/a | schema tests | model reference | no playback, no license | **C** |
| ani-cli | [repo](https://github.com/pystardust/ani-cli/tree/0301d67d5768d332b049821a30082ad43d9a215a) `0301d67` | shell | GPL-3.0 | 2026-10-22 | HiAnime only | HLS + audio/subtitles | curl/impersonation, Referer | anti-bot/obfuscation path | shell checks | poor | protected single source | **D** |
| anime-sdk | [repo](https://github.com/hexxt-git/anime-sdk/tree/72d734f1f9bc6d59183ead2fcb0f172ad6018cdf) `72d734f` | TypeScript | нет лицензии | 2026-06-25 | multiple claimed providers | streams | Node/proxy | decryption/proxy mechanisms | limited | sidecar only | no license, protected flows | **D** |
| aryaniiil/anime-api | [repo](https://github.com/aryaniiil/anime-api/tree/d9a785ad030d6fc6a8ad709291be9612c864449e) `d9a785a` | TypeScript | MIT | 2026-09-11 | multiple aggregators claimed | M3U8/pipe | Node/serverless/proxy | README/source explicitly bypass/forged pipe, AES/WASM | limited | no | bypass and provenance | **D** |
| Aniraku Backend | [repo](https://github.com/Aniraku/Aniraku-Backend/tree/a45c47e569bda68f6f007c3ef8599ce3fc51cf85) `a45c47e` | Go | MIT | 2026-10-27 | 13 providers claimed | relay/streams | separate service | decrypt/relay/provider-specific | young | sidecar possible | very new, bypass-heavy | **D** |
| MiruroAPI | [repo](https://github.com/Shineii86/MiruroAPI/tree/78029e369b7c8830697a21a71100b36b466b35af) `78029e3` | TypeScript | MIT | 2026-08-25 | 12 Miruro pipe providers + 2 embeds claimed | M3U8/embed | Node, remote pipe, optional scraper/FlareSolverr | Cloudflare bypass explicitly proposed | docs/examples, little contract isolation | no | remote provenance/anti-bot | **D** |
| wajik-anime-api | [repo](https://github.com/wajik45/wajik-anime-api/tree/0c2cb09b6d2baab7d15f1d03f3777f1b52d18e02) `0c2cb09` | TypeScript | MIT | 2026-07-21 | Indonesian third-party sites | HLS/download URLs | Node scraping | site-specific reverse endpoints | mixed | sidecar | rights and churn | **D** |
| amvstrm/api | [repo](https://github.com/amvstrm/api/tree/3706a646bf3a76922130c89063710e34b6bcd99f) `3706a64` | TypeScript | GPL-3.0 | archived; 2025-07-08 | remote anime aggregators | streaming API | remote upstreams | opaque/reverse flows | stale | no | archived + GPL + provenance | **D** |
| sr-wrapper | [repo](https://github.com/omashune/sr-wrapper/tree/187b30e27898a1314327b6d3da8b2a43eccc50d0) `187b30e` | JavaScript | MIT | 2020-07-20 | Shikimori | metadata/page | Node | n/a | minimal | no playback | does not return media | **D** |
| yummyanime-aniyomi | [repo](https://github.com/sw1ftin/yummyanime-aniyomi/tree/aba84695e307e2de8ba4c454bedbe695406380ee) `aba8469` | Kotlin | MIT | 2026-06-04 | YummyAnime | video list | Android/session headers | protected source; static audit only | limited | no | anti-bot/source rights | **D** |
| AnimeX CloudStream plugins | [repo](https://github.com/HatsuneMikuUwU/AnimeX/tree/e0a5085f2a3f0a00ce9b8aa226a63a17bfafc9f5) `e0a5085` | Kotlin | нет лицензии | 2026-10-14 | anime/donghua plugins | M3U8/embed by plugin | CloudStream runtime | heterogeneous | plugin build | no | no license + provider risk | **D** |
| oce CloudStream plugins | [repo](https://github.com/byimam2nd/oce/tree/1c5c7cb0087bd1081eb258c787253206176e9a75) `1c5c7cb` | Kotlin | нет лицензии | 2026-10-23 | many provider/extractor plugins | M3U8/embed | CloudStream runtime | heterogeneous | plugin build | no | no license + opaque providers | **D** |
| anime1v-api | [repo](https://github.com/FxxMorgan/anime1v-api/tree/6e54a75d894532b033c9e933772cdf3720842206) `6e54a75` | TypeScript | MIT | 2026-06-05 | multiple streaming sites | streams/downloads | browser/Puppeteer/yt-dlp fallbacks | unpack/decrypt/browser evasion paths | mixed | no | bypass, very broad attack surface | **D** |
| apikuoshi | [repo](https://github.com/koudex/apikuoshi/tree/145f431789140f1d8a90ef4a024171b59b8715a7) `145f431` | TypeScript | MIT | 2026-09-16 | Kuoshi-like remote source | tokenized playback | Node, short-lived token | AES/token reconstruction | limited | no | technical protection/90s-like tokens | **D** |
| Consumet | [repo](https://github.com/consumet/consumet.ts) | TypeScript | unavailable at audit | HTTP 451/DMCA 2026-03 | formerly many | formerly streams | Node | mixed reverse-engineering | unavailable | historical reference only | repository blocked by DMCA | **D** |
| gogoanime-api | [repo](https://github.com/riimuru/gogoanime-api) | TypeScript | unavailable at audit | HTTP 451/DMCA 2024-04 | formerly Gogoanime | formerly HLS | Node scraping | protected/removed | unavailable | no | DMCA, no auditable current commit | **D** |
| aniwatch-api | [repo](https://github.com/ghoshRitesh12/aniwatch-api) | TypeScript | unavailable at audit | HTTP 451/DMCA 2026-03 | formerly HiAnime/AniWatch | formerly streams | Node scraping | protected/removed | unavailable | no | DMCA, no auditable current commit | **D** |

DMCA references: [Consumet notice](https://github.com/github/dmca/blob/master/2026/03/2026-03-12-dramacool.md), [gogoanime-api notice](https://github.com/github/dmca/blob/master/2024/04/2024-04-18-corsearch.md), [aniwatch-api notice](https://github.com/github/dmca/blob/master/2026/03/2026-03-23-crunchyroll.md). Для HTTP 451 проектов exact current commit не указан намеренно: текущий код нельзя было независимо проверить, а старый fork нельзя выдавать за ревизию origin.

## 7. Карточки shortlist

### 7.1 Официальный AniLibria/AniLiberty contract + `py-aniliberty` — доверие высокое

**Что возвращает.** Episode model содержит HLS поля для 480/720/1080; example выбирает best playlist. Это конечные manifests, не iframe. Подтверждение: [`episode.py`](https://github.com/LLIJIYAPNIK/py-aniliberty/blob/21008bcdc38204e82c103bddd95a73dec29780f2/src/aniliberty/models/episode.py), [`episodes.py`](https://github.com/LLIJIYAPNIK/py-aniliberty/blob/21008bcdc38204e82c103bddd95a73dec29780f2/src/aniliberty/resources/episodes.py), [HLS example](https://github.com/LLIJIYAPNIK/py-aniliberty/blob/21008bcdc38204e82c103bddd95a73dec29780f2/examples/04_episodes_and_hls_links.py). Старый официальный contract также описывает `host + episode.hls.{fhd,hd,sd}`: [`api_v3.md`](https://github.com/anilibria/docs/blob/8ddcb219c6a155633389c11a0fc87e5c75760bbb/api_v3.md).

**Подтверждено:** AniLiberty/AniLibria public release/episode API, quality variants, async typed client. **Только заявлено/не проверено live:** фактическая доступность конкретного релиза, geo и разрешение third-party playback на дату запуска продукта.

**Ограничения.** URL может зависеть от mirror/host и политики издателя; account endpoints требуют auth, playback model сам по себе публичный. API-код и MIT SDK не дают AniLux лицензию на контент. Repo docs не имеет распознанной лицензии, поэтому контракт можно реализовать самостоятельно, не копируя его код.

**Ошибки и fixtures.** SDK имеет typed exceptions, retry/cache layers, unit/integration suites, VCR cassettes и отдельную проверку scrubber: [`tests`](https://github.com/LLIJIYAPNIK/py-aniliberty/tree/21008bcdc38204e82c103bddd95a73dec29780f2/tests). Это лучший источник для offline happy/not-found/schema fixtures после полного удаления host paths, query и identifiers.

**Интеграция.** Python 3.11 совпадает с AniLux; зависимости — `httpx>=0.27`, `pydantic>=2.7`. Предпочтение: собственный `AniLibertyProvider` поверх SDK или тонкого HTTP client, mapper в canonical model, bounded timeout и kill switch. Отдельный runtime не нужен.

### 7.2 `anime-dl-core` — доверие среднее-высокое к коду, среднее к внешним источникам

**Что возвращает.** `Stream`/`PlayerResult` нормализуют kind, URL, quality и headers; player modules возвращают HLS/DASH/MP4. Подтверждение: [`models.py`](https://github.com/ialakey/anime-dl-core/blob/f23b7c1b1403c7adc7eaa60ba6323a75e35c9771/src/anime_dl_core/models.py), [`players`](https://github.com/ialakey/anime-dl-core/tree/f23b7c1b1403c7adc7eaa60ba6323a75e35c9771/src/anime_dl_core/players).

**Источники.** Кодом подтверждены AnimeGO/AniMedia/Alloha discovery и AniLibria, AniBoom, CVH, AniMedia, Sibnet, SovetRomantica, VK players. Для первого PoC whitelist только `anilibria.py`; после продуктовой проверки — публичные SovetRomantica/VK embeds. AnimeGO/AniBoom/CVH/Alloha/Sibnet не считать автоматически допустимыми.

**Ограничения.** Referer/Origin являются частью `Stream.headers`; часть manifests временная. Scraper modules ломаются от DOM/player changes. Необходимо запретить provider-у любые redirects к private/link-local hosts и не проксировать произвольные headers/cookies.

**Ошибки и fixtures.** Есть `UnsupportedUrl`, `NetworkError`, `ServiceError`, `ExtractionError`, `NoStreamsFound`, `DecryptionError`, `ContentBlocked`, `NotFound`: [`errors.py`](https://github.com/ialakey/anime-dl-core/blob/f23b7c1b1403c7adc7eaa60ba6323a75e35c9771/src/anime_dl_core/errors.py). Offline fixtures покрывают AniLibria, SovetRomantica, VK, manifests и players: [`test_players_offline.py`](https://github.com/ialakey/anime-dl-core/blob/f23b7c1b1403c7adc7eaa60ba6323a75e35c9771/tests/test_players_offline.py).

**Интеграция.** Python-native (`requests`, optional `aiohttp`), но лучше не импортировать registry целиком. Обернуть только разрешённые modules собственным adapter-ом и преобразовать исключения в canonical `not_found/unavailable/rate_limited/blocked/schema_changed`. Отдельный service не нужен.

### 7.3 `whynotix/anilibria-api-client` — доверие среднее

**Что возвращает.** Typed async client к тому же AniLiberty/AniLibria API; playback приходит внутри API response models. Source: [`api_client.py`](https://github.com/whynotix/anilibria-api-client/blob/50ad0564afa95690cfdc66e60afabc1cb6fcbb8b/anilibria_api_client/api_client.py), [tests](https://github.com/whynotix/anilibria-api-client/tree/50ad0564afa95690cfdc66e60afabc1cb6fcbb8b/tests).

**Почему не A.** У проекта 22 releases и свежий commit, но малая adoption и он не даёт нового источника относительно `py-aniliberty`. Unlicense юридически проста для кода, однако разрешение API/контента всё равно отдельное.

**Интеграция.** Альтернативный клиент для сравнительного PoC: проверить одинаковый релиз через оба SDK на scrubbed fixture и выбрать тот, у которого устойчивее модели/errors. Отдельный runtime не нужен.

### 7.4 `yt-dlp` для официальных сервисов — доверие высокое к реализации, среднее к применимости

**Что возвращает.** Extractors ADN, HiDive и Bilibili/Bangumi строят formats, включая HLS/DASH/direct resources: [`adn.py`](https://github.com/yt-dlp/yt-dlp/blob/f264a6cbd1f630894da0f368df00f8aae50140e0/yt_dlp/extractor/adn.py), [`hidive.py`](https://github.com/yt-dlp/yt-dlp/blob/f264a6cbd1f630894da0f368df00f8aae50140e0/yt_dlp/extractor/hidive.py), [`bilibili.py`](https://github.com/yt-dlp/yt-dlp/blob/f264a6cbd1f630894da0f368df00f8aae50140e0/yt_dlp/extractor/bilibili.py).

**Ограничения.** Нужны собственные легитимные account cookies/credentials, subscription и geo availability; часть title/quality может быть DRM. AniLux не должен принимать пользовательские/чужие cookies, обходить paywall/geo/DRM или кешировать account-bound URL. Abema path из-за custom license/key handling исключить из PoC. Crunchyroll extractor в проверенной ревизии не найден; поддержку не приписываем.

**Интеграция.** Если продукт получит письменное право — отдельный constrained worker или subprocess `--dump-single-json` с domain allowlist, output size/time limits и без download. Прямое долгоживущее импортирование yt-dlp увеличивает attack surface. Fixtures должны содержать только обезличенную структуру formats.

### 7.5 `anicli-api` / `AnimeParsers` — доверие среднее к интерфейсам, низкое к protected sources

Оба проекта реально возвращают `Video`/manifests без Kodik, а не просто iframe. У `anicli-api` полезны [`base.py`](https://github.com/vypivshiy/anicli-api/blob/ab79153c504dd1e6877749d64c978c362a2936a2/anicli_api/base.py) и [`player/base.py`](https://github.com/vypivshiy/anicli-api/blob/ab79153c504dd1e6877749d64c978c362a2936a2/anicli_api/player/base.py); у AnimeParsers — [`api_aniliberty.py`](https://github.com/YaNesyTortiK/AnimeParsers/blob/cac4c83e03e43f2829506ef202a1279a4e0b78bf/src/anime_parsers_ru/api_aniliberty.py) и AnimeGO parsers.

Но `anicli-api` содержит отдельный [`test_anubis_bypass.py`](https://github.com/vypivshiy/anicli-api/blob/ab79153c504dd1e6877749d64c978c362a2936a2/tests/test_anubis_bypass.py), а Yummy/AnimeGO paths зависят от site-specific protection. Этот код включён в аудит и статистику, но не должен запускаться или переноситься. Допустимый PoC — только сравнение AniLibria adapter/interface и offline error mapping; остальные modules — архитектурный материал либо D.

## 8. Что фактически работает без Kodik

Наличие Kodik-файла не дисквалифицировало multi-provider проект. По исходному коду, независимо от Kodik:

| Проект | Non-Kodik path, подтверждённый кодом | Уровень результата | Примечание |
|---|---|---|---|
| py-aniliberty / AniLibria API | AniLiberty/AniLibria episode HLS variants | manifest/qualities | официальный API contract |
| anime-dl-core | AniLibria, SovetRomantica, VK, AniMedia, AnimeGO→AniBoom/CVH, Sibnet, Alloha | HLS/DASH/MP4 | допустимость решается отдельно для каждого module |
| anicli-api | AniLibria; AnimeGO/YummyAnime/AniLib.me/AnimeVost/Dreamcast/HDRezka/SameBand и non-Kodik players | Video/manifest/direct | только AniLibria предлагается в PoC; protected paths не запускать |
| AnimeParsers | AniLiberty, AnimeGO/AniBoom/CVH, Jut.su | HLS/DASH/MP4 | scraping и source rights делают его B/D по module |
| yt-dlp | authorized ADN, HiDive, Bilibili/Bangumi | formats/HLS/DASH | только собственная авторизация и non-DRM content |
| anipy-cli | AnimeHub/AniDBApp; unexported AllAnime/AnimeKai | ProviderStream | последние содержат remote decoding/crypto и отклонены |
| CloudStream/Aniyomi ecosystems | каждый plugin реализует собственный `loadLinks`/video list | streams/embeds | framework contract подтверждён, конкретный plugin — отдельный trust decision |
| Streamlink | AbemaTV, Bilibili live | HLS stream objects | Abema custom license path исключён; Bilibili plugin не Bangumi VOD |

Иными словами, `anime-dl-core`, `anicli-api` и AnimeParsers действительно имеют non-Kodik playback code; они не являются замаскированными Kodik-only wrappers. Это не означает, что все перечисленные источники разрешены или live-работоспособны.

## 9. Отклонённые механизмы и security review

### 9.1 Почему bypass/decryption проекты сохранены в отчёте, но не в PoC

Они важны для статистики и позволяют увидеть типовые failure modes, однако их исполнение расширило бы задачу за допустимые границы:

- `ani-cli` использует impersonation при блокировке и декодирует obfuscated payload одного защищённого источника.
- unexported providers `anipy-cli` загружают ключи/decode rules из удалённого GitHub content; AnimeKai path выполняет внешнее выражение через expression evaluator и декодирует endpoint. Это supply-chain и remote-code/rule risk.
- `anicli-api` содержит явную проверку обхода Anubis; Yummy path нельзя считать обычным публичным API.
- `MiruroAPI` документирует ScraperAPI/FlareSolverr как средство обойти Cloudflare и зависит от Miruro pipe; direct embeds всё равно не являются конечным media contract.
- `aryaniiil/anime-api`, `anime-sdk`, `Aniraku`, `anime1v-api`, `apikuoshi` содержат pipe forging, token reconstruction, AES/WASM/RC4-like decoding, browser fallback либо relay неизвестного происхождения.
- Streamlink Abema adapter реализует специальный license/key protocol. Наличие исходника не даёт права повторять этот flow в AniLux.

Для этих проектов в отчёте не приводятся алгоритмы, payloads, ключи, media URLs или пошаговые инструкции.

### 9.2 Общие security-риски

1. **SSRF/open proxy.** Manifest proxy AniLux должен иметь provider-owned domain allowlist, повторную проверку каждого redirect и URI внутри playlist, запрет private/link-local/metadata IP и ограничение размера/числа вложенных playlists.
2. **Header/cookie leakage.** Разрешать только adapter-declared `Referer`, `Origin`, `User-Agent`, `Range`; никогда не пересылать browser cookies/Authorization между providers.
3. **Remote rules/keys.** Не исполнять JS/eval/expression и не загружать decrypt rules с mutable branch. Даже pin по commit не делает обход допустимым.
4. **Short-lived URLs.** Не хранить playback URLs в `Anime`; кешировать только envelope с `expires_at`, source id и минимальным TTL.
5. **Dependency surface.** Предпочесть `httpx`/`requests` client официального API. Puppeteer, FlareSolverr, browser automation и универсальные relay существенно увеличивают attack surface.
6. **Fixture hygiene.** Удалять hostname path/query, signatures, cookies, account ids и media tokens. Fixture должна доказывать shape, а не сохранять работающую ссылку.

### 9.3 Юридические и эксплуатационные причины D

| Причина | Проекты |
|---|---|
| anti-bot/Cloudflare/Anubis/browser evasion | ani-cli, MiruroAPI, Yummy modules, anime1v-api |
| decrypt/token reconstruction/remote decode rules | anime-sdk, aryaniiil/anime-api, Aniraku, apikuoshi, unexported anipy providers, Streamlink Abema |
| отсутствует лицензия | anime-sdk, AnimeX, oce, libanime_schema (последний оставлен только C как schema reference) |
| архив/неподдерживаемый upstream | amvstrm/api, official Aniyomi extensions |
| metadata/page, но не playback | sr-wrapper, libanime_schema |
| удалён/недоступен по DMCA | Consumet, gogoanime-api, aniwatch-api |
| remote opaque provider/provenance | MiruroAPI, wajik-anime-api, amvstrm/api и большая часть generic plugin catalogs |

## 10. Kodik-only проекты, исключённые из основной оценки

Эти репозитории просмотрены на уровне metadata/search и не учитываются как независимые провайдеры:

| Проект | Exact revision | Лицензия | Причина исключения |
|---|---|---|---|
| [negezor/kodik-api-rust](https://github.com/negezor/kodik-api-rust/tree/7e78e83c7e5c7dd686c2b225d4902cf4489f6707) | `7e78e83` | MIT | только typed Kodik API client |
| [hksm-app/kodik-api](https://github.com/hksm-app/kodik-api/tree/1447d82e9bf6e84144ecf2fc228fb634ca6e87b4) | `1447d82` | MIT | только Go Kodik client |
| [blassonad/kodik-api](https://github.com/blassonad/kodik-api/tree/ca7d29a8387964c6f620ec715f9e2a24ea738e64) | `ca7d29a` | MIT | только Rust public Kodik API client |
| [10kkyvl/kodik-api-animaru](https://github.com/10kkyvl/kodik-api-animaru/tree/95e222a769aed4851f57bc31b05422ab1a7fcd66) | `95e222a` | нет лицензии | только Kodik API |
| [AN0NCER/tunime-kodik-proxy](https://github.com/AN0NCER/tunime-kodik-proxy/tree/ed36faaa5647c7d169c14492ea0aa57e8422db76) | `ed36faa` | нет лицензии | proxy для Kodik API, независимых источников нет |

Обычные сайты-примеры, которые лишь вставляют Kodik iframe, не добавлялись как библиотеки. Текущий внутренний `KodikWrapper` AniLux также не считается новым кандидатом.

## 11. Архивы, forks и продолжения

| Заброшенный/ограниченный origin | Активное продолжение | Оценка |
|---|---|---|
| `aniyomiorg/aniyomi-extensions` archived (`0ccdcfb`) | [`yuzono/anime-extensions`](https://github.com/yuzono/anime-extensions/tree/2d070ab5f37e7b112279ee875485505fc59e6fe3) (`2d070ab`, push 2026-10-27) | живой Apache-2.0 catalog, но каждый plugin требует отдельного аудита |
| Android-only Aniyomi runtime | [`SeoMavares/miwayomi`](https://github.com/SeoMavares/miwayomi/tree/a3a776ebd26f91f558cd59a4bd57fff9119ee987) (`a3a776e`) | возможный JVM sidecar, не снимает риски extensions |
| YummyAnime extension в большом catalog | [`sw1ftin/yummyanime-aniyomi`](https://github.com/sw1ftin/yummyanime-aniyomi/tree/aba84695e307e2de8ba4c454bedbe695406380ee) (`aba8469`) | активен, но protected-source риск остаётся |
| CloudStream core без доверенного единого plugin repo | `AnimeX` (`e0a5085`), `oce` (`1c5c7cb`) и другие community catalogs | активность есть, но отсутствие лицензии/разный provenance не позволяет считать forks безопасными |

Удалённые DMCA repositories намеренно не «восстанавливались» из forks: это не даёт актуального trusted origin и повышает юридический риск.

## 12. Рекомендуемый порядок PoC

1. **Contract-only PoC AniLiberty/AniLibria.** На scrubbed local fixture сравнить собственный минимальный client, `py-aniliberty` и `whynotix/anilibria-api-client`; выбрать один transport. Никаких реальных URL в fixture.
2. **`anime-dl-core` whitelist PoC.** Подключить только `AnilibriaPlayer` к тому же canonical contract; затем отдельно, только после product/legal approval, проверить SovetRomantica/public VK contract на offline fixtures.
3. **Error/expiry/header PoC.** На синтетических manifests проверить Referer, signed/expired URL, redirect rejection, empty qualities, malformed schema, blocked/rate-limited mapping.
4. **Authorized official-service spike.** Только если есть бизнес-основание и права: constrained yt-dlp worker для одного non-DRM ADN/HiDive/Bilibili example с собственным test account; без download и cookie persistence.
5. **Architecture comparison.** Взять идеи CloudStream/Anipy/Anicli, но не их protected providers: capabilities, link type, referrer, subtitle/audio tracks, error taxonomy.

Не начинать PoC с AnimeGO/YummyAnime/HiAnime/Miruro pipelines: он измерит способность обходить меняющуюся защиту, а не устойчивость ProviderAdapter.

## 13. Предлагаемый ProviderAdapter contract

```text
ProviderAdapter
  capabilities() -> ProviderCapabilities
  search(query, hints) -> list[ProviderTitleMatch]
  get_structure(provider_title_id) -> TitleStructure
  list_episodes(provider_title_id, season) -> list[ProviderEpisode]
  resolve_playback(provider_episode_id, preferences) -> PlaybackResult
```

Минимальные модели:

- `ProviderTitleMatch`: provider/title ids, canonical hints (`shikimori_id`, aliases, year), confidence/evidence.
- `TitleStructure`: franchises/seasons/episodes/translations без playback URLs.
- `PlaybackResult`: provider, episode identity, fetched/expires timestamps, translations, sources, subtitles, warnings.
- `PlaybackSource`: `url`, `kind` (`hls|dash|mp4|webm|embed`), quality/bitrate, codecs/container, audio, headers allowlist, `requires_proxy`, `drm`, `auth_scope`, `geo`, provenance.
- Errors: `not_found`, `ambiguous`, `unavailable`, `blocked`, `auth_required`, `geo_blocked`, `drm`, `rate_limited`, `schema_changed`, `timeout`, `unsafe_redirect`.

Каждый adapter объявляет capabilities и policy: official/public-embed/scrape, domains, allowed headers, URL TTL, auth/DRM, runtime, feature flag и kill switch. Fallback не должен превращать `blocked/drm/auth_required` в попытку обхода другим extractor-ом.

### 13.1 Mapping shortlist в contract

| Кандидат | Способ подключения | Mapping |
|---|---|---|
| py-aniliberty | in-process async Python service/client | release/episode → canonical ids; HLS fields → `PlaybackSource(kind=hls, quality=...)` |
| anime-dl-core | in-process wrapper, explicit module allowlist | `PlayerResult.streams` → sources; `Stream.headers` → validated playback headers; exceptions → canonical errors |
| anilibria-api-client | alternative in-process client | тот же AniLiberty mapper; использовать только один transport в production |
| yt-dlp | isolated subprocess/worker, domain allowlist | sanitized formats/subtitles → sources; account/DRM/geo errors сохранять, не fallback-bypass |
| miwayomi/CloudStream (не PoC) | отдельный JVM/Android-compatible service | adapter boundary по JSON; конкретные extensions отдельно pin/audit/disable |

## 14. Contract fixtures

Минимальный набор, согласованный с #33–#35:

1. AniLiberty release с 1 сезоном, несколькими эпизодами и 480/720/1080 HLS.
2. Тот же title с отсутствующим quality и reordered fields.
3. Несколько переводов/audio tracks и subtitles.
4. Master HLS с relative URIs; nested playlist; URI в tags; headers (`Referer`) как metadata, не реальные secrets.
5. DASH/MP4 source для унификации, даже если первый provider отдаёт только HLS.
6. `expires_at`/signed URL в полностью вымышленном домене `example.invalid`.
7. Empty result, title not found, ambiguous season mapping, episode gap.
8. 401/auth required, 403/geo or blocked, 429 with retry metadata, timeout, 5xx.
9. Schema drift: unknown fields, missing host, malformed source, unexpected iframe-only response.
10. Unsafe cases: redirect/private IP, oversized playlist, forbidden headers, DRM flag — adapter обязан отклонить.

Fixture policy: только `.invalid` URLs и синтетические tokens; fixtures минимальны, вручную проверяемы и не содержат cookies, signatures, реальные CDN paths или персональные данные.

## 15. Вопросы для legal/product до включения источника

1. Есть ли у AniLux письменное право использовать API и воспроизводить контент AniLibria/AniLiberty во внешнем клиенте, включая branding/attribution/ads?
2. Разрешено ли proxying/rewrite manifests или плеер обязан обращаться к CDN напрямую?
3. Можно ли кешировать metadata, playback envelope и на какой срок; требуется ли удаление по запросу правообладателя?
4. Какие страны и возрастные ограничения поддерживает продукт; как отражать geo blocks?
5. Допустимы ли публичные embeds SovetRomantica/VK/AniMedia и разрешает ли их contract third-party playback?
6. Нужны ли официальные account integrations ADN/HiDive/Bilibili; кто хранит credentials и имеет ли AniLux договор/ToS permission?
7. Политика по рекламе, analytics и обязательным player controls источника.
8. Какие licenses совместимы с лицензией/deployment AniLux: MIT/Apache/BSD/Unlicense; можно ли использовать GPL только через отдельный process/service?
9. Кто принимает takedown/DMCA и какой SLA для provider kill switch?
10. Должны ли AnimeGO/YummyAnime/HiAnime и сходные protected sources быть запрещены продуктовой политикой независимо от технической доступности?

## 16. Журнал поиска

| Направление | Примеры запросов/действий | Результат |
|---|---|---|
| GitHub repositories | `anime streaming api extractor m3u8`, `anime scraper API Python TypeScript`, `self hosted anime API`, `anime provider plugin` | multi-provider APIs, SDK и frameworks |
| Именованные RU sources | `AnimeGO extractor`, `YummyAnime API`, `AniLibria AniLiberty HLS`, `Anime365 m3u8`, `SovetRomantica m3u8` | anicli-api, anime-dl-core, AnimeParsers, official clients |
| GitHub code search | домены + `m3u8`, `get_videos`, `loadLinks`, `ProviderStream`, `Referer`, `Origin` | проверка фактических extractor paths вместо README |
| Frameworks | CloudStream `ExtractorLink`, Aniyomi `Video`, anipy `BaseProvider`, yt-dlp `InfoExtractor`, Streamlink plugins | нормализация и error/capability patterns |
| Archives/forks | archive flag, network/search по Aniyomi/CloudStream extensions | yuzono continuation, miwayomi runtime, community catalogs |
| Package manifests | `pyproject.toml`, package/release metadata | Python/runtime/dependency compatibility |
| Activity | GitHub GraphQL: default branch SHA, push, release, issues/PR | pin всех доступных candidates; shortlist свежий |
| Removal/legal signals | HTTP 451 и GitHub DMCA repo | Consumet, gogoanime-api, aniwatch-api не считать рабочими |
| Kodik exclusion | `kodik api` repo/code search | 5 Kodik-only clients/proxies вынесены отдельно |

Покрытые языки: Python, TypeScript/JavaScript, Go, Kotlin, Rust и shell. C#-поиск не дал кандидата с верифицируемым playback contract, который добавлял бы источник к таблице; результаты были приложениями/iframe wrappers либо неактивными snippets. Репозитории `anify-oss/anify-api` и `recloudstream/cloudstream-extensions`, встречающиеся в старых списках, на дату среза не найдены по прежним URL и не учитывались как доступные projects.

## 17. Ответы на финальные вопросы

### 1. Существует ли библиотека, которую разумно встроить напрямую?

Да: `py-aniliberty` разумно проверить для прямого in-process использования; `anime-dl-core` — только через whitelist конкретных modules. Даже для них production-включение зависит от разрешения источника, а не только OSS-лицензии.

### 2. Готовая библиотека, fork или собственные adapters?

Собственные маленькие adapters поверх официальных clients/contracts. Не форкать универсальный scraper без необходимости. Fork допустим только для pin/security fix после подтверждения прав и upstream maintenance plan.

### 3. Какие 3–5 проектов проверить первыми?

1. `py-aniliberty`;
2. `anime-dl-core` (AniLibria module сначала);
3. `whynotix/anilibria-api-client` как контрольный client;
4. `yt-dlp` только при наличии authorized official-service use case;
5. `anicli-api`/AnimeParsers только для contract/error architecture и AniLibria comparison, не protected modules.

### 4. Какие источники имеют официальный или относительно устойчивый playback contract?

Наиболее подтверждён — AniLibria/AniLiberty. ADN/HiDive/Bilibili имеют официальные сервисы, но extractor не равен официальному partner API и требует account/ToS/DRM проверки. Публичные SovetRomantica/VK embeds технически проще, но продуктовые права нужно подтвердить.

### 5. Какие источники исключить сразу?

Все paths, требующие DRM/paywall bypass, чужих cookies, CAPTCHA/Cloudflare/Anubis bypass, remote decrypt rules, forged pipe или неизвестный proxy: HiAnime/AniWatch flows из ani-cli, Yummy protected flow, Miruro pipe-bypass, AnimeKai/AllAnime crypto paths, apikuoshi и похожие token reconstruction projects. Также исключить DMCA-blocked и unlicensed code.

### 6. Какие библиотеки действительно работают без Kodik по коду?

`py-aniliberty`, `anime-dl-core`, `anicli-api`, AnimeParsers, `yt-dlp`, `anipy-cli`, CloudStream/Aniyomi providers и Streamlink имеют independent non-Kodik code. Безопасно рекомендованы не все: подробная module-level граница приведена в разделах 8–9.

### 7. Можно ли получить media URL без browser automation и обхода защиты?

Да: через AniLibria/AniLiberty API; в разрешённых случаях — официальный/account-bound extractor ADN/HiDive/Bilibili и некоторые public embeds. AnimeGO/Yummy/HiAnime-подобные источники не дают столь же устойчивой и безопасной гарантии.

### 8. Какая минимальная общая модель нужна ProviderAdapter?

Раздельные discovery/structure/episodes/playback methods; `PlaybackResult` с translations и `PlaybackSource` с kind, quality, codecs, headers, expiry, auth/geo/DRM/proxy/provenance; capabilities и нормализованная error taxonomy.

### 9. Какие fixtures подготовить?

Scrubbed AniLiberty multi-quality happy path, translations/subtitles, HLS relative/nested URIs, DASH/MP4 normalization, expiry/header cases, empty/ambiguous/not-found, 401/403/429/timeout/schema drift и SSRF/DRM rejection. Только `.invalid` URLs.

### 10. Какие юридические решения нужны?

Письменное разрешение API/third-party playback и proxying; content/territory/age/ads/attribution policy; account credential and DRM policy; OSS/GPL compatibility; caching/retention; takedown SLA и перечень источников, запрещённых независимо от технической доступности.

## 18. Рекомендация

Следующий шаг — не подключение «универсального extractor-а», а небольшой offline PoC контракта из Epic #4: один `AniLibertyProvider`, mapper в canonical `PlaybackResult`, scrubbed fixtures и contract tests. После его review отдельно принять legal/product decision по AniLibria/AniLiberty. Только затем сравнить `anime-dl-core` на том же contract и решить, нужны ли дополнительные разрешённые источники.

