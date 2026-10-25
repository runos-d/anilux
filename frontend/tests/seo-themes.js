async page => {
  const origin = new URL(page.url()).origin;
  const browser = page.context().browser();
  const results = [];
  for (const width of [1365, 390, 430]) for (const theme of ['dark', 'polnochnaya', 'light']) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: 'block' });
    await context.addInitScript(theme => localStorage.setItem('appearance:v1', JSON.stringify({ s: { theme }, o: {} })), theme);
    const tab = await context.newPage();
    const errors = [];
    tab.on('pageerror', error => errors.push(error.message));
    const inspect = async () => {
      await tab.waitForFunction(() => document.getAnimations().every(animation => animation.effect?.getTiming().iterations === Infinity || animation.playState !== 'running'));
      return tab.evaluate(() => {
      const card = document.querySelector('.catalog-grid .anime-card');
      const grid = document.querySelector('.catalog-grid');
      const footer = document.querySelector('.seo-navigation a');
      const result = { overflow: document.documentElement.scrollWidth > innerWidth + 2, theme: document.documentElement.dataset.theme };
      if (card) {
        const css = getComputedStyle(card), rect = card.getBoundingClientRect();
        const title = getComputedStyle(card.querySelector('.anime-title'));
        result.card = { width: rect.width, height: rect.height, bg: css.backgroundColor, border: css.border, radius: css.borderRadius, shadow: css.boxShadow, font: css.fontFamily, titleSize: title.fontSize, titleLine: title.lineHeight, titleColor: title.color };
        const g = getComputedStyle(grid);
        result.grid = { columns: g.gridTemplateColumns.split(' ').length, gap: g.gap, width: grid.getBoundingClientRect().width };
      }
      if (footer) { const css = getComputedStyle(footer); result.footer = { color: css.color, font: css.fontFamily, size: css.fontSize, line: css.lineHeight }; }
      return result;
      });
    };
    try {
      await tab.goto(origin + '/anime?section=catalog', { waitUntil: 'domcontentloaded' });
      await tab.locator('.catalog-grid .anime-card').first().waitFor({ timeout: 45000 });
      await tab.waitForFunction(theme => document.documentElement.dataset.theme === theme, theme);
      await tab.locator('.seo-navigation a').first().waitFor();
      const reference = await inspect();
      const links = await tab.locator('.seo-navigation a').evaluateAll(links => [...new Set(links.map(link => link.getAttribute('href')))]);
      for (const path of links) {
        await tab.goto(origin + path, { waitUntil: 'domcontentloaded' });
        await tab.waitForFunction(() => document.documentElement.dataset.seoMode === 'app', null, { timeout: 45000 });
        if (path !== '/anime/browse') await tab.locator('.catalog-grid .anime-card').first().waitFor({ timeout: 45000 });
        await tab.locator('.seo-navigation a').first().waitFor();
        const actual = await inspect();
        if (actual.theme !== theme || actual.overflow) throw new Error(JSON.stringify({ path, width, theme, actual }));
        if (actual.card) {
          for (const key of Object.keys(reference.card)) {
            const equal = typeof actual.card[key] === 'number' ? Math.abs(actual.card[key] - reference.card[key]) < 1 : actual.card[key] === reference.card[key];
            if (!equal) throw new Error(JSON.stringify({ path, width, theme, key, expected: reference.card[key], actual: actual.card[key] }));
          }
          if (JSON.stringify(actual.grid) !== JSON.stringify(reference.grid)) throw new Error(JSON.stringify({ path, width, theme, referenceGrid: reference.grid, actualGrid: actual.grid }));
        }
        if (JSON.stringify(actual.footer) !== JSON.stringify(reference.footer)) throw new Error(JSON.stringify({ message: 'Footer style differs', theme, path, reference: reference.footer, actual: actual.footer }));
        results.push({ theme, width, path, columns: actual.grid?.columns, cardWidth: actual.card?.width, cardHeight: actual.card?.height, matched: true });
      }
      await tab.goto(origin + '/anime/year/2020', { waitUntil: 'domcontentloaded' });
      await tab.locator('.seo-collection .anime-card').first().waitFor();
      await tab.waitForFunction(() => { const cards = [...document.querySelectorAll('.catalog-grid .anime-card')].slice(0, innerWidth < 414 ? 2 : innerWidth < 768 ? 3 : 5); return cards.length && cards.every(card => { const img = card.querySelector('img'); return img?.complete && img.naturalWidth > 0; }); }, null, { timeout: 15000 });
      await tab.screenshot({ path: 'artifacts/seo/theme-' + theme + '-' + width + '.png', fullPage: false });
      if (errors.length) throw new Error(errors.join('; '));
    } catch (error) {
      await tab.screenshot({ path: 'artifacts/seo/theme-failure.png', fullPage: false });
      throw new Error(JSON.stringify({ message: String(error), url: tab.url(), theme, width, errors, last: results.slice(-3), body: (await tab.locator('main').innerText()).slice(0, 1000) }));
    } finally { await context.close(); }
  }
  return { origin, checks: results.length, results, errors: [] };
}