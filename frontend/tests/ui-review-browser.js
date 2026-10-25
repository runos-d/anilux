async page => {
  const accounts = __ACCOUNTS__, ids = __IDS__;
  const rows = [], errors = [], requests = [];
  const browser = page.context().browser();
  const origin = 'http://localhost:5186';
  const targets = {
    guest: ['/', '/login', '/register', '/anime', '/anime?section=ongoings', '/anime?section=recommendations', '/anime?section=calendar', '/anime?section=currently_watching', '/anime/'+ids.animeSlug, '/anime/'+ids.animeSlug+'/watch', '/franchise/'+ids.franchiseSlug, '/people', '/add-anime', '/donate', '/playlist/shared/invalid-test-token', '/chats/invite/invalidtesttoken'],
    owner: ['/', '/profile', '/profile/@ui-reader', '/library', '/stats', '/feed', '/post/'+ids.post, '/chats', '/chats/'+ids.chat, '/chats/'+ids.group, '/playlists', '/playlist/'+ids.playlist, '/playlists/create', '/playlists/'+ids.playlist+'/edit', '/notifications', '/settings', '/achievements', '/people'],
    admin: ['/admin', '/admin/complaints', '/admin/franchises'],
  };
  for (const [role, paths] of Object.entries(targets)) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block', reducedMotion: 'reduce', timezoneId: 'Europe/Moscow' });
    if (accounts[role]) await context.addInitScript(account => {
      localStorage.setItem('anilux_user_v1', JSON.stringify(account.user));
      localStorage.setItem('anilux_access_token_v1', account.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1', account.tokens.refresh);
    }, accounts[role]);
    const tab = await context.newPage();
    tab.on('pageerror', error => errors.push({ role, url: tab.url(), error: error.stack || error.message }));
    tab.on('response', response => { if (response.status() >= 400 && response.url().includes('/api/')) requests.push({ role, url: response.url(), status: response.status() }); });
    for (const [index, path] of paths.entries()) {
      await tab.goto(origin+path, {waitUntil:'domcontentloaded'});
      await tab.locator('main').first().waitFor();
      await tab.waitForTimeout(1400);
      for (const close of await tab.locator('.notification-toast-close').all()) await close.click().catch(() => {});
      for (const width of [320,390,768,1280,1920]) {
        await tab.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
        await tab.waitForTimeout(120);
        const result = await tab.evaluate(() => {
          const visible = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width && r.height && s.display !== 'none' && s.visibility !== 'hidden'; };
          const overflow = [...document.querySelectorAll('main *')].filter(visible).map(el => ({ el, r: el.getBoundingClientRect() }))
            .filter(({el,r}) => (r.right > innerWidth + 1 || r.left < -1) && !el.closest('[class*="carousel"], [class*="tabs"], [class*="scroll"], [class*="slider"], .cal-week-days, .genres-track'))
            .slice(0,12).map(({el,r}) => ({ tag: el.tagName, class: el.className?.baseVal ?? el.className, x: Math.round(r.x), width: Math.round(r.width) }));
          const symbols = [...document.querySelectorAll('button, h1, h2, h3, label, [class*="empty"], [class*="avatar-icon"], [class*="notif-icon"]')].filter(visible)
            .filter(el => /[\p{Extended_Pictographic}★☆×✕✓✔▶←→]/u.test(el.textContent || ''))
            .filter(el => !el.closest('.emoji-picker, .reactions, .message-reactions, .reaction-picker'))
            .slice(0,15).map(el => ({ class: el.className, text: el.textContent.trim().slice(0,140) }));
          const components = [...new Set([...document.querySelectorAll('main *')].map(el => el.__vueParentComponent?.type?.__file).filter(Boolean))];
          return { scrollWidth: document.documentElement.scrollWidth, width: innerWidth, overflow, symbols, components, text: document.querySelector('main')?.innerText.slice(0,240) };
        });
        rows.push({ role, path, url: tab.url().replace(origin,''), ...result });
        await page.evaluate(({phase,report}) => sessionStorage.setItem('ui-review-'+phase,JSON.stringify(report)), {phase:__PHASE__,report:{rows,errors,requests}});
        await tab.screenshot({ path: `backend/data/local_release/ui-review/${__PHASE__}-${role}-${index}-${width}.png`, fullPage: true, animations:'disabled', timeout:15000 });
      }
    }
    await context.close();
  }
  return { rows, errors, requests };
}
