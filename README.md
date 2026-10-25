<style>
  :root {
    --bg: #14101c;
    --surface: #1c1628;
    --surface-2: #241c33;
    --border: #352a48;
    --accent: #e888b8;
    --accent-2: #b8a0e0;
    --accent-3: #f0b0d0;
    --text: #f2ecf7;
    --text-2: #c4b8d4;
    --text-3: #8a7d9c;
    --radius: 12px;
    --font-sans: "Inter", "Noto Sans JP", sans-serif;
    --font-mono: "JetBrains Mono", monospace;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes floatY {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-5px); }
  }
  @keyframes pulseSoft {
    0%, 100% { opacity: 1; }
    50%      { opacity: 0.55; }
  }

  .al {
    font-family: var(--font-sans);
    color: var(--text);
    background: var(--bg);
    padding: 32px 28px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
  }
  .al h1 {
    font-size: 2.1rem;
    margin: 0 0 6px;
    letter-spacing: -0.02em;
    color: var(--text);
  }
  .al .al-title-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 6px;
  }
  .al .al-title-row h1 { margin: 0; }
  .al .al-title-row svg { flex-shrink: 0; }
  .al .al-tagline {
    color: var(--accent);
    font-weight: 500;
    margin: 0 0 8px;
  }
  .al .al-tech {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-3);
    margin: 0 0 24px;
  }
  .al h2 {
    color: var(--text);
    font-size: 1.15rem;
    margin: 28px 0 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }
  .al-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin: 10px 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
  }
  .al-card svg { flex-shrink: 0; margin-top: 2px; }
  .al-card-title {
    color: var(--text);
    font-weight: 600;
    display: block;
    margin-bottom: 2px;
  }
  .al-card-body { color: var(--text-2); font-size: 0.92rem; }
  .al-chip {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-2);
    margin: 4px 4px 4px 0;
  }
  .al-anim {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 8px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-2);
    margin: 4px 4px 4px 0;
  }
  .al-fade  { animation: fadeIn 0.2s ease-out both; }
  .al-float { animation: floatY 4s ease-in-out infinite; }
  .al-pulse { animation: pulseSoft 3s ease-in-out infinite; }
</style>

<div class="al">

<div class="al-title-row"><svg xmlns="http://www.w3.org/2000/svg" viewBox="-80 -80 160 160" width="56" height="56"><defs><path id="p" d="M0,0 C-15,-10 -31,-30 -23,-54 C-19,-65 -8,-63 0,-52 C8,-63 19,-65 23,-54 C31,-30 15,-10 0,0 Z"/><clipPath id="c"><use href="#p"/></clipPath><g id="pet"><use href="#p" fill="#ffc4da"/><g clip-path="url(#c)"><path d="M24,-60 C33,-30 15,-10 0,1 C11,-20 17,-38 9,-66 Z" fill="#f7a3c3"/><path d="M0,2 C-10,-6 -16,-18 -12,-30 C-6,-26 6,-26 12,-30 C16,-18 10,-6 0,2 Z" fill="#ff86b2"/><path d="M0,-8 L0,-40 M0,-10 L-10,-38 M0,-10 L10,-38" fill="none" stroke="#e8689b" stroke-width="1.3" stroke-linecap="round"/></g><use href="#p" fill="none" stroke="#4a1d3f" stroke-width="3" stroke-linejoin="round"/><path d="M-19,-50 C-24,-41 -23,-31 -18,-23" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/><circle cx="-22" cy="-17" r="1.5" fill="#fff"/></g><g id="s1"><path d="M0,-6 L0,-21" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/><path d="M0,-6 L0,-21" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/><circle cy="-23" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/></g><g id="s2"><path d="M0,-6 L0,-27" stroke="#4a1d3f" stroke-width="3.4" stroke-linecap="round"/><path d="M0,-6 L0,-27" stroke="#ff7fae" stroke-width="1.4" stroke-linecap="round"/><circle cy="-29" r="3.4" fill="#ffd166" stroke="#4a1d3f" stroke-width="1.8"/></g></defs><use href="#pet"/><use href="#pet" transform="rotate(72)"/><use href="#pet" transform="rotate(144)"/><use href="#pet" transform="rotate(216)"/><use href="#pet" transform="rotate(288)"/><use href="#s1" transform="rotate(18)"/><use href="#s2" transform="rotate(54)"/><use href="#s1" transform="rotate(90)"/><use href="#s2" transform="rotate(126)"/><use href="#s1" transform="rotate(162)"/><use href="#s2" transform="rotate(198)"/><use href="#s1" transform="rotate(234)"/><use href="#s2" transform="rotate(270)"/><use href="#s1" transform="rotate(306)"/><use href="#s2" transform="rotate(342)"/><circle r="8" fill="#e0467f" stroke="#4a1d3f" stroke-width="2.6"/><circle r="3.6" fill="#ff86b2"/><circle cx="-2.6" cy="-2.8" r="1.5" fill="#fff"/></svg><h1>AniLux</h1></div>

<p class="al-tech">Vue 3 · TypeScript · Django · MySQL · Redis · Docker · Nginx</p>

## Запуск

```powershell
git clone https://github.com/runos-d/anilux.git
cd anilux
```

```powershell
.\setup.cmd
.\start.cmd
```

`setup.cmd` создаст локальную конфигурацию, установит зависимости и соберёт образы.  
`start.cmd` применит миграции и запустит всё приложение.

## Возможности

<div class="al-card">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e888b8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="9 7 17 12 9 17 9 7" fill="#f0b0d0" stroke="none"/>
    <circle cx="12" cy="12" r="10"/>
  </svg>
  <div>
    <span class="al-card-title">Смотри</span>
    <span class="al-card-body">Любимые тайтлы в одном месте - без лишних кликов.</span>
  </div>
</div>

<div class="al-card">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#b8a0e0" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 5h16v14H4z"/>
    <path d="M4 9h16"/>
    <path d="M8 5v4" stroke="#e888b8"/>
  </svg>
  <div>
    <span class="al-card-title">Собирай</span>
    <span class="al-card-body">Избранное, статусы просмотра, история и собственные плейлисты.</span>
  </div>
</div>

<div class="al-card">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e888b8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
    <path d="M4 4h16v12H8l-4 4z"/>
    <circle cx="9" cy="10" r="1" fill="#f0b0d0" stroke="none"/>
    <circle cx="13" cy="10" r="1" fill="#f0b0d0" stroke="none"/>
    <circle cx="17" cy="10" r="1" fill="#f0b0d0" stroke="none"/>
  </svg>
  <div>
    <span class="al-card-title">Обсуждай</span>
    <span class="al-card-body">Публикации, реакции, комментарии и чаты.</span>
  </div>
</div>

## Технически

<div class="al-card">
  <div>
    <span class="al-card-title">Frontend</span>
    <span class="al-card-body">Vue 3, TypeScript, Vite, Pinia и PWA. Интерфейс общается с API по HTTP и WebSocket.</span>
    <br />
    <span class="al-chip">Vue 3</span>
    <span class="al-chip">TypeScript</span>
    <span class="al-chip">Vitest</span>
  </div>
</div>

<div class="al-card">
  <div>
    <span class="al-card-title">Backend</span>
    <span class="al-card-body">Django REST Framework и Channels обслуживают API, авторизацию и realtime; Celery выполняет фоновые задачи.</span>
    <br />
    <span class="al-chip">Django</span>
    <span class="al-chip">MySQL</span>
    <span class="al-chip">Redis</span>
    <span class="al-chip">Celery</span>
  </div>
</div>

<div class="al-card">
  <div>
    <span class="al-card-title">Инфраструктура</span>
    <span class="al-card-body">Docker Compose поднимает базу, кеш, API, фоновые процессы и локальную почту. Настройки берутся из корневого <code>.env</code>.</span>
  </div>
</div>

## Проверки

```powershell
cd frontend
npm run type-check
npm run lint
npm run test:unit:run
npm run build-only
```

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test
```

Те же проверки автоматически выполняются в GitHub Actions.

</div>
