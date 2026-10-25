async host => {
  const accounts = __ACCOUNTS__;
  const ids = __IDS__;
  const origin = 'http://localhost:5186';
  const browser = host.context().browser();
  const themes = ['dark', 'light', 'polnochnaya'];
  const screens = [
    [320, 568], [360, 800], [390, 844], [430, 932], [768, 1024],
    [1024, 768], [1280, 720], [1440, 900], [1920, 1080],
  ];
  const targets = {
    guest: [
      '/', '/login', '/register', '/anime?section=catalog',
      '/anime?section=ongoings', '/anime?section=announcements',
      '/anime?section=recommendations', '/anime?section=calendar',
      '/anime?section=currently_watching', '/anime/year/2026',
      '/anime/genre/drama', '/anime/type/tv', '/anime/status/ongoing',
      '/anime/season/2026/fall', '/anime/browse', '/anime/collection/popular',
      `/anime/${ids.animeSlug}`, `/anime/${ids.animeSlug}/watch`,
      `/franchise/${ids.franchiseSlug}`, `/profile/@ui-reader`,
      `/post/${ids.post}`, '/people', `/people/${ids.person}`, '/add-anime',
      '/playlists?tab=public', `/playlist/${ids.playlist}`, '/news', '/app',
      '/donate', '/contacts', '/terms', '/privacy', '/license',
      '/playlist/shared/invalid-test-token', '/chats/invite/invalidtesttoken',
    ],
    owner: [
      '/profile', '/library', '/stats', '/feed', `/post/${ids.otherPost}`,
      '/chats', `/chats/${ids.chat}`, `/chats/${ids.group}`,
      '/chats/groups', '/chats/create-group', '/playlists?tab=my',
      '/playlists?tab=favorites', '/playlists/create',
      `/playlists/${ids.playlist}/edit`, '/notifications',
      '/notifications?tab=unread', '/notifications?tab=reminders',
      '/notifications/settings', '/settings', '/achievements', '/support',
      '/excerpts',
    ],
    admin: ['/admin', '/admin/complaints', '/admin/franchises'],
  };
  const rows = [];
  const errors = [];
  const requests = [];
  const failures = [];

  const appearance = (theme, fontSize = 14) => JSON.stringify({
    s: { theme, fontSize, smoothAnimations: false, parallaxEffect: false },
    o: { sakura: false, newYear: false, halloween: false, loveDay: false },
  });
  const createContext = async (role, theme, fontSize = 14) => {
    const context = await browser.newContext({
      viewport: { width: 390, height: 844 }, serviceWorkers: 'block',
      reducedMotion: 'reduce', timezoneId: 'Europe/Moscow', hasTouch: true,
    });
    await context.addInitScript(({ account, cache }) => {
      localStorage.setItem('appearance:v1', cache);
      if (account) {
        localStorage.setItem('anilux_user_v1', JSON.stringify(account.user));
        localStorage.setItem('anilux_access_token_v1', account.tokens.access);
        localStorage.setItem('anilux_refresh_token_v1', account.tokens.refresh);
      }
    }, { account: accounts[role] || null, cache: appearance(theme, fontSize) });
    await context.route('**/api/users/theme-settings/**', route => route.fulfill({
      json: { theme, font_size: fontSize, smooth_animations: false, parallax_effect: false },
    }));
    return context;
  };
  const measure = async (page, role, theme, path, label, expectedTheme = theme) => {
    const state = await page.evaluate(() => {
      const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
      };
      const excludedScroller = el => el.closest([
        '[class*="carousel"]', '[class*="tabs"]', '[class*="scroll"]',
        '[class*="slider"]', '.cal-week-days', '.genres-track',
        '.cal-filter-chips', '.cal-strip', '.recommendations-grid',
      ].join(','));
      const outside = [...document.querySelectorAll('main *, body > [role="dialog"] *')]
        .filter(visible).map(el => ({ el, r: el.getBoundingClientRect() }))
        .filter(({ el, r }) => !excludedScroller(el) && (r.left < -1 || r.right > innerWidth + 1))
        .slice(0, 20).map(({ el, r }) => ({
          tag: el.tagName, class: String(el.className?.baseVal ?? el.className).slice(0, 120),
          x: Math.round(r.x), width: Math.round(r.width),
        }));
      const roundMismatch = [...document.querySelectorAll([
        '[class*="avatar"]', '[class*="icon-btn"]', '[class*="round"]',
        '[class*="circle"]', '[class*="dot"]', '[class*="indicator"]',
      ].join(','))].filter(visible).map(el => ({ el, r: el.getBoundingClientRect(), s: getComputedStyle(el) }))
        .filter(({ r, s }) => {
          const radius = parseFloat(s.borderTopLeftRadius);
          return radius >= Math.min(r.width, r.height) * .45 && Math.abs(r.width - r.height) > 1.5;
        }).slice(0, 20).map(({ el, r }) => ({
          class: String(el.className?.baseVal ?? el.className).slice(0, 120),
          width: Math.round(r.width * 10) / 10, height: Math.round(r.height * 10) / 10,
        }));
      const dialogs = [...document.querySelectorAll('[role="dialog"], .modal-content, .modal-container')]
        .filter(visible).map(el => {
          const r = el.getBoundingClientRect();
          return { class: String(el.className).slice(0, 100), top: Math.round(r.top), bottom: Math.round(r.bottom), width: Math.round(r.width) };
        });
      return {
        width: innerWidth, height: innerHeight,
        scrollWidth: document.documentElement.scrollWidth,
        scrollHeight: document.documentElement.scrollHeight,
        theme: document.documentElement.dataset.theme,
        outside, roundMismatch, dialogs,
        bodyOverflow: getComputedStyle(document.body).overflow,
      };
    });
    rows.push({ role, theme, path, label, url: page.url().replace(origin, ''), ...state });
    if (expectedTheme && state.theme !== expectedTheme) failures.push({ role, theme, path, label, error: `theme=${state.theme}` });
  };

  for (const theme of themes) {
    for (const [role, paths] of Object.entries(targets)) {
      const context = await createContext(role, theme);
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      page.on('pageerror', error => errors.push({ role, theme, url: page.url(), error: error.message }));
      page.on('response', response => {
        if (response.status() >= 400 && response.url().includes('/api/')) {
          requests.push({ role, theme, path: new URL(response.url()).pathname, status: response.status() });
        }
      });
      for (const [index, path] of paths.entries()) {
        try {
          await page.goto(origin + path, { waitUntil: 'domcontentloaded' });
          await page.locator('main').first().waitFor();
          await page.waitForTimeout(500);
          for (const [width, height] of screens) {
            await page.setViewportSize({ width, height });
            await page.waitForTimeout(60);
            await measure(page, role, theme, path, `${width}x${height}`);
          }
          if (['/', '/anime?section=catalog', '/playlists?tab=public', '/settings', '/admin'].includes(path)) {
            await page.setViewportSize({ width: 390, height: 844 });
            await page.screenshot({
              path: `backend/data/local_release/ui-review/full-${theme}-${role}-${index}-390.png`,
              fullPage: true, animations: 'disabled', timeout: 15000,
            });
            await page.setViewportSize({ width: 1440, height: 900 });
            await page.screenshot({
              path: `backend/data/local_release/ui-review/full-${theme}-${role}-${index}-1440.png`,
              fullPage: true, animations: 'disabled', timeout: 15000,
            });
          }
        } catch (error) {
          failures.push({ role, theme, path, error: error.message });
        }
        await host.evaluate(report => sessionStorage.setItem('ui-comprehensive', JSON.stringify(report)), { rows, errors, requests, failures });
      }
      await context.close();
    }
  }

  const breakpointContext = await createContext('owner', 'dark');
  const breakpointPage = await breakpointContext.newPage();
  for (const path of ['/anime?section=catalog', '/playlists?tab=public', '/settings']) {
    await breakpointPage.goto(origin + path, { waitUntil: 'domcontentloaded' });
    await breakpointPage.waitForTimeout(500);
    for (const [width, height] of [[359, 800], [360, 800], [361, 800], [479, 844], [480, 844], [481, 844], [767, 900], [768, 900], [769, 900], [1023, 768], [1024, 768], [1025, 768], [844, 390], [568, 320]]) {
      await breakpointPage.setViewportSize({ width, height });
      await breakpointPage.waitForTimeout(60);
      await measure(breakpointPage, 'owner', 'dark', path, `breakpoint-${width}x${height}`);
    }
  }
  await breakpointContext.close();

  const textContext = await createContext('owner', 'dark', 22);
  const textPage = await textContext.newPage();
  for (const path of ['/anime?section=catalog', '/playlists?tab=public', '/settings']) {
    await textPage.goto(origin + path, { waitUntil: 'domcontentloaded' });
    await textPage.waitForTimeout(500);
    for (const [width, height] of [[320, 568], [390, 844], [768, 1024]]) {
      await textPage.setViewportSize({ width, height });
      await measure(textPage, 'owner', 'dark-large-text', path, `${width}x${height}`, 'dark');
    }
  }
  await textContext.close();

  const zoomContext = await createContext('owner', 'dark');
  const zoomPage = await zoomContext.newPage();
  for (const path of ['/anime?section=catalog', '/playlists?tab=public', '/settings']) {
    await zoomPage.goto(origin + path, { waitUntil: 'domcontentloaded' });
    await zoomPage.setViewportSize({ width: 720, height: 450 });
    await zoomPage.evaluate(() => { document.body.style.zoom = '2'; });
    await zoomPage.waitForTimeout(100);
    await measure(zoomPage, 'owner', 'dark-zoom-200', path, '1440x900@200%', 'dark');
  }
  await zoomContext.close();

  await host.evaluate(report => sessionStorage.setItem('ui-comprehensive', JSON.stringify(report)), { rows, errors, requests, failures });
  return {
    rows: rows.length,
    failures: failures.length,
    errors: errors.length,
    requests: requests.length,
    documentOverflow: rows.filter(row => row.scrollWidth > row.width + 1).length,
    outside: rows.filter(row => row.outside.length).length,
    roundMismatch: rows.filter(row => row.roundMismatch.length).length,
  };
}
