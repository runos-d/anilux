async page => {
  const origin = 'http://localhost:8098';
  await page.unroute('**/api/seo/page/**');
  const check = (ok, message) => { if (!ok) throw new Error(message); };
  const registry = await (await page.request.get(origin + '/site-navigation.json')).json();
  const expected = registry.groups.flatMap(group => group.links.map(link => link.path));
  const catalog = await (await page.request.get(origin + '/api/seo/page/', { params: { path: '/anime' } })).json();
  const paths = ['/', '/anime', catalog.items[0].path, '/@reader', '/playlists?tab=public', '/contacts', '/terms', '/privacy', '/license', '/missing/page', '/login'];
  const errors = [], results = [];
  page.on('pageerror', error => errors.push(error.message));
  for (const path of paths) {
    const response = await page.request.get(origin + path);
    const source = await response.text();
    const data = await (await page.request.get(origin + '/api/seo/page/', { params: { path } })).json();
    check(response.status() === (path === '/missing/page' ? 404 : 200), 'HTTP status ' + path);
    check((source.match(/<footer\b/g) || []).length === 1, 'One server footer ' + path);
    const serverFooter = source.match(/<footer\b[\s\S]*?<\/footer>/)[0];
    check(!serverFooter.includes('/post/'), 'Post link in footer ' + path);
    for (const ua of ['Googlebot', 'YandexBot']) {
      check(await (await page.request.get(origin + path, { headers: { 'User-Agent': ua } })).text() === source, 'User-Agent mismatch ' + path);
    }
    await page.goto(origin + path);
    await page.waitForFunction(() => document.documentElement.dataset.seoMode === 'app');
    await page.waitForFunction(title => document.title === title, data.title);
    const footer = page.locator('footer.seo-navigation');
    check(await footer.count() === 1, 'One Vue footer ' + path);
    const links = await footer.locator('a[href^="/"]').evaluateAll(elements => elements.map(el => el.getAttribute('href')));
    check(JSON.stringify(links) === JSON.stringify(expected), 'Changing footer links ' + path);
    check(await page.locator('head link[rel=canonical]').count() === 1, 'Canonical ' + path);
    check(await page.locator('head meta[name=description]').count() === 1, 'Description ' + path);
    check(await page.locator('head meta[name=robots]').getAttribute('content') === data.robots, 'Robots ' + path);
    const image = await footer.locator('img').evaluate(el => ({ loaded: el.complete && el.naturalWidth > 0, width: el.width, height: el.height }));
    check(image.loaded && image.width === 28 && image.height === 28, 'Sakura SVG ' + path);
    results.push({ path, title: data.title, robots: data.robots, links: links.length });
  }
  for (const path of expected) check((await page.request.get(origin + path)).status() === 200, 'Broken footer link ' + path);
  check((await page.request.get(origin + '/sakura.svg')).headers()['cache-control'].includes('max-age=604800'), 'SVG cache');
  const layouts = [];
  for (const theme of ['dark', 'light', 'polnochnaya']) for (const width of [390, 1365]) {
    const context = await page.context().browser().newContext({ viewport: { width, height: 900 }, serviceWorkers: 'block' });
    await context.addInitScript(theme => {
      localStorage.setItem('appearance:v1', JSON.stringify({ s: { theme } }));
      localStorage.setItem('sakuraOverlayEnabled', 'false');
    }, theme);
    const tab = await context.newPage();
    await tab.goto(origin + '/contacts');
    await tab.waitForFunction(() => document.documentElement.dataset.seoMode === 'app');
    const footer = tab.locator('footer.seo-navigation');
    await footer.scrollIntoViewIfNeeded();
    const layout = await footer.evaluate(el => ({ theme: document.documentElement.dataset.theme, right: el.getBoundingClientRect().right, width: innerWidth, scroll: document.documentElement.scrollWidth }));
    check(layout.theme === theme && layout.scroll <= width + 2 && layout.right <= width + 2, 'Footer overflow/theme ' + theme + ' ' + width);
    await footer.screenshot({ path: 'artifacts/seo/footer-' + theme + '-' + width + '.png' });
    layouts.push(layout);
    await context.close();
  }
  await page.goto(origin + '/contacts');
  await page.waitForFunction(() => document.documentElement.dataset.seoMode === 'app');
  await page.route('**/api/seo/page/**', route => route.abort());
  await page.locator('footer a[href="/terms"]').click();
  await page.waitForURL('**/terms');
  check(await page.locator('footer.seo-navigation a[href^="/"]').count() === expected.length, 'Footer depends on SEO API');
  check(errors.length === 0, 'JavaScript errors: ' + errors.join('; '));
  await page.unroute('**/api/seo/page/**');
  return { pages: results, layouts, checkedLinks: expected.length, errors, footerWithoutSeoApi: true };
}
