<h1>AniLux</h1></div>

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
