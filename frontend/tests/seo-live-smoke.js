async page => {
  const origin = 'http://localhost:8080';
  const catalog = await (await page.request.get(origin + '/api/seo/page/', { params: { path: '/anime' } })).json();
  const anime = catalog.items[0].path;
  const detail = await (await page.request.get(origin + '/api/seo/page/', { params: { path: anime } })).json();
  const franchise = detail.related.find(link => link.path.startsWith('/franchise/'))?.path;
  const results = [];
  for (const theme of ['dark', 'polnochnaya', 'light']) {
    const context = await page.context().browser().newContext({ viewport: { width: 1365, height: 900 }, serviceWorkers: 'block' });
    await context.addInitScript(theme => localStorage.setItem('appearance:v1', JSON.stringify({ s: { theme }, o: {} })), theme);
    const tab = await context.newPage(), errors = [];
    tab.on('pageerror', error => errors.push(error.message));
    const paths = theme === 'dark' ? ['/', '/anime', ...catalog.related.map(link => link.path), anime, anime + '/watch', ...(franchise ? [franchise] : [])] : ['/', '/anime', '/anime/year/2026', '/anime/year/2020', anime, ...(franchise ? [franchise] : [])];
    try {
      for (const path of [...new Set(paths)]) {
        const response = await tab.goto(origin + path, { waitUntil: 'domcontentloaded' });
        await tab.waitForFunction(() => document.documentElement.dataset.seoMode === 'app', null, { timeout: 45000 });
        if (response.status() !== 200) throw new Error(path + ': HTTP ' + response.status());
        if (path === '/') { await tab.locator('.home-hero').waitFor(); if (await tab.locator('.seo-grid').count()) throw new Error('Extra home catalogue'); }
        else if (path.startsWith('/franchise/')) await tab.locator('.franchise-page .hero-title').waitFor();
        else if (path.endsWith('/watch')) await tab.locator('.player-container').waitFor();
        else if (path === anime) await tab.locator('.anime-detail-card').waitFor();
        else if (path === '/anime' || path.includes('section=catalog')) { await tab.locator('.av-tabs').waitFor(); await tab.locator('.catalog-grid > *').first().waitFor(); }
        else { await tab.locator('.seo-collection .afb').waitFor(); await tab.locator('.seo-collection .anime-card').first().waitFor(); await tab.locator('.collection-header h1').waitFor(); }
        if (await tab.locator('#seo-base-style').count()) throw new Error('Fallback CSS leaked');
        if (await tab.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2)) throw new Error('Overflow ' + path);
        results.push({ theme, path, status: response.status(), nativeApplication: true });
      }
      if (errors.length) throw new Error(errors.join('; '));
      await tab.goto(origin + '/anime/year/2026', { waitUntil: 'domcontentloaded' });
      await tab.locator('.seo-collection .anime-card').first().waitFor();
      await tab.screenshot({ path: 'artifacts/seo/live-' + theme + '.png', fullPage: false });
      await tab.locator('.seo-navigation-panel').scrollIntoViewIfNeeded();
      await tab.screenshot({ path: 'artifacts/seo/live-footer-' + theme + '.png', fullPage: false });
    } finally { await context.close(); }
  }
  return { origin, checks: results.length, results, errors: [] };
}