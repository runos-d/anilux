async page => {
  const origin = 'http://localhost:8096';
  const browser = page.context().browser();
  const desktop = await browser.newContext({ viewport: { width: 1365, height: 900 }, serviceWorkers: 'block' });
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, serviceWorkers: 'block' });
  const results = [], failures = [];
  await mobile.addInitScript(() => {
    window.__seoLabVitals = { lcp: 0, cls: 0, maxInteractionDuration: 0 };
    for (const type of ['largest-contentful-paint', 'layout-shift', 'event']) {
      try { new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          if (type === 'largest-contentful-paint') window.__seoLabVitals.lcp = entry.startTime;
          if (type === 'layout-shift' && !entry.hadRecentInput) window.__seoLabVitals.cls += entry.value;
          if (type === 'event' && entry.interactionId) window.__seoLabVitals.maxInteractionDuration = Math.max(window.__seoLabVitals.maxInteractionDuration, entry.duration);
        }
      }).observe({ type, buffered: true, durationThreshold: 16 }); } catch { /* Report unsupported entries as unavailable. */ }
    }
  });
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  try {
    const tab = await desktop.newPage();
    tab.on('pageerror', error => failures.push(error.message));
    const profile = await (await tab.request.get(origin + '/api/seo/page/', { params: { path: '/@reader' } })).json();
    const catalog = await (await tab.request.get(origin + '/api/seo/page/', { params: { path: '/anime' } })).json();
    check(catalog.items?.length > 0, 'Acceptance database is not seeded');
    const animePath = catalog.items[0].path;
    const paths = ['/', '/anime', animePath, '/franchise/public-franchise', '/anime/year/2025', '/anime/genre/romance',
      '/anime/season/2025/winter', '/anime/type/tv', '/anime/status/finished', '/anime/collection/romance-2025',
      '/anime/genre/small', '/anime/year/2025?page=2', '/@reader', ...profile.related.map(link => link.path)];
    for (const path of paths) {
      const source = await (await tab.request.get(origin + path)).text();
      const metadata = await (await tab.request.get(origin + '/api/seo/page/', { params: { path } })).json();
      await tab.goto(origin + path);
      await tab.waitForFunction(title => document.title === title, metadata.title, { timeout: 45000 });
      await tab.waitForFunction(() => document.documentElement.dataset.seoMode === 'app', null, { timeout: 45000 });
      if (path !== '/' && path !== '/anime') await tab.getByRole('heading', { name: metadata.h1, exact: true }).first().waitFor({ timeout: 45000 });
      check((await tab.locator('head link[rel=canonical]').count()) === 1, 'Duplicate canonical ' + path);
      check((await tab.locator('head meta[name=robots]').count()) === 1, 'Duplicate robots ' + path);
      check(await tab.locator('head meta[name=description]').getAttribute('content') === metadata.description, 'Description differs ' + path);
      check(source.includes('<h1>'), 'Source missing content ' + path);
      if (path === '/') await tab.locator('.home-hero').waitFor();
      if (path === '/anime') await tab.locator('.av-tabs').waitFor();
      check(await tab.locator('.app .sidebar, .app aside').count() > 0, 'Application navigation missing ' + path);
      check(await tab.locator('#seo-base-style').count() === 0, 'Fallback CSS leaked into Vue ' + path);
      results.push({ path, title: await tab.title(), h1: await tab.locator('h1').allTextContents(),
        canonical: await tab.locator('link[rel=canonical]').getAttribute('href') });
    }
    await tab.goto(origin + '/anime');
    await tab.locator('.av-tabs').waitFor();
    await tab.waitForFunction(() => document.querySelectorAll('.catalog-grid .anime-card, .catalog-grid .franchise-card').length > 0);
    check(await tab.locator('.av-tab').count() >= 5, 'Catalogue tabs disappeared');
    check(await tab.locator('.seo-grid').count() === 0, 'Fallback catalogue replaced the application');
    await tab.evaluate(() => { window.__seoDocumentIdentity = Math.random(); });
    const identity = await tab.evaluate(() => window.__seoDocumentIdentity);
    const searchBox = tab.getByPlaceholder('Поиск аниме по названию...');
    const filterApplied = tab.waitForResponse(response => {
      const url = new URL(response.url());
      return url.pathname === '/api/anime/' && url.searchParams.get('search') === 'тестовое';
    });
    await searchBox.fill('Тестовое');
    await filterApplied;
    const shuffle = tab.getByTitle('Перемешать', { exact: true });
    await shuffle.click();
    await tab.waitForFunction(() => document.querySelector('[title="Перемешать"]')?.getAttribute('aria-pressed') === 'true');
    await tab.locator('.catalog-grid .franchise-card, .catalog-grid .anime-card').first().click();
    await tab.locator('.franchise-page, .anime-detail-card').first().waitFor();
    check(await tab.evaluate(() => window.__seoDocumentIdentity) === identity, 'Card click reloaded the app');
    await tab.goBack();
    await tab.getByPlaceholder('Поиск аниме по названию...').waitFor();
    check((await tab.getByPlaceholder('Поиск аниме по названию...').inputValue()).toLowerCase() === 'тестовое', 'Card back lost search');
    await tab.waitForFunction(() => document.querySelectorAll('.catalog-grid > .franchise-card, .catalog-grid > .anime-card').length === 1);
    await tab.locator('a[href="/anime/year/2025"]').first().click();
    await tab.waitForURL(/\/anime\/year\/2025/);
    await tab.goBack();
    await tab.getByPlaceholder('Поиск аниме по названию...').waitFor();
    check(await tab.getByPlaceholder('Поиск аниме по названию...').inputValue() === 'Тестовое', 'Back lost catalogue filter');
    check(await tab.getByTitle('Перемешать', { exact: true }).getAttribute('aria-pressed') === 'true', 'Back lost shuffle mode');
    const phone = await mobile.newPage();
    await phone.goto(origin + '/anime/collection/romance-2025');
    await phone.locator('.seo-collection .anime-card').first().waitFor();
    await phone.waitForFunction(() => document.documentElement.dataset.seoMode === 'app');
    const layout = await phone.evaluate(() => ({ width: innerWidth, scrollWidth: document.documentElement.scrollWidth,
      links: [...document.querySelectorAll('.seo-collection .anime-card')].length, h1: document.querySelector('h1')?.textContent }));
    check(layout.links === 24, 'Mobile lost primary content');
    check(layout.scrollWidth <= layout.width + 2, 'Mobile content overflows horizontally');
    await phone.getByRole('button', { name: 'Следующая страница', exact: true }).click();
    await phone.waitForFunction(() => document.title.includes('страница 2'));
    await phone.waitForFunction(() => document.querySelectorAll('.seo-collection .anime-card').length === 6);
    await phone.reload();
    await phone.waitForFunction(() => document.querySelectorAll('.seo-collection .anime-card').length === 6);
    await phone.evaluate(() => new Promise(resolve => requestIdleCallback(resolve, { timeout: 3000 })));
    const lab = await phone.evaluate(() => ({ ...window.__seoLabVitals,
      scripts: performance.getEntriesByType('resource').filter(entry => entry.name.includes('.js')).map(entry => ({ url: entry.name, bytes: entry.transferSize, duration: entry.duration })),
      frames: [...document.querySelectorAll('iframe')].map(frame => frame.src) }));
    await phone.screenshot({ path: 'artifacts/seo/mobile.png', fullPage: true });
    await tab.screenshot({ path: 'artifacts/seo/desktop.png', fullPage: true });
    check(!failures.length, 'Browser errors: ' + failures.join('; '));
    return { results, applicationNavigation: true, nativeCatalogue: true, richFranchise: true, paginationReload: true, filtersBack: true, shuffleBack: true, mobile: layout, lab, fieldData: null, errors: failures };
  } finally { await desktop.close(); await mobile.close(); }
}
