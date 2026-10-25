async page => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  const origin = 'http://localhost:8080';
  const response = await page.context().request.post(origin+'/api/users/login/', {
    data: { username: 'site_browser_20261011_owner', password: 'Site-Rebuild-Local-123!' },
  });
  if (!response.ok()) throw new Error('Fixture login failed: '+response.status());
  const account = await response.json();
  await page.context().addInitScript(account => {
    localStorage.setItem('anilux_access_token_v1', account.tokens.access);
    localStorage.setItem('anilux_refresh_token_v1', account.tokens.refresh);
    localStorage.setItem('anilux_user_v1', JSON.stringify(account.user));
  }, account);
  const samples = [];
  const targets = [
    { label: 'catalog', path: '/anime?section=catalog', selector: '.catalog-grid .anime-card,.catalog-grid .franchise-card' },
    { label: 'calendar', path: '/anime?section=calendar', selector: '.crc' },
    { label: 'recommendations', path: '/anime?section=recommendations', selector: '.rec-card-wrap' },
    { label: 'home', path: '/', selector: '.home-page .anime-card' },
    { label: 'feed', path: '/feed', selector: '.post-card' },
    { label: 'profile', path: '/profile', selector: '.profile-header h1' },
    { label: 'library', path: '/library', selector: '.lib-card' },
    { label: 'playlists', path: '/playlists', selector: '.playlist-card' },
    { label: 'notifications', path: '/notifications', selector: '.notif-row' },
    { label: 'chats', path: '/chats', selector: '.chat-list-item' },
  ];
  await page.context().addInitScript(targets => {
    const path = location.pathname + location.search;
    const target = targets.find(row => row.path === path);
    if (!target) return;
    const check = () => {
      const card = document.querySelector(target.selector);
      if (card?.getClientRects().length) window.__siteContentMs = Math.round(performance.now());
      else requestAnimationFrame(check);
    };
    requestAnimationFrame(check);
  }, targets);
  const measure = async (target, kind) => {
    const start = Date.now();
    await page.goto(origin+target.path, { waitUntil: 'domcontentloaded' });
    try {
      await page.locator(target.selector).first().waitFor({ state: 'visible', timeout: 15000 });
      const result = { label: target.label, kind, ms: await page.evaluate(() => window.__siteContentMs ?? null), orchestrationMs: Date.now()-start,
        cards: await page.locator(target.selector).count(),
        api: await page.evaluate(() => performance.getEntriesByType('resource').filter(row => row.name.includes('/api/')).map(row => ({ url: new URL(row.name).pathname, ms: Math.round(row.duration) }))) };
      samples.push(result);
    } catch {
      samples.push({ label: target.label, kind, error: 'No visible card found', url: page.url(), text: (await page.locator('main').first().innerText()).slice(0,350) });
    }
  };
  for (const target of targets) await measure(target, 'first_document');
  for (const target of targets) await measure(target, 'repeat_document');
  await page.goto(origin+'/anime?section=catalog');
  const repeatedSections = [];
  for (const [button, selector] of [['Календарь','.crc'], ['Для вас','.rec-card-wrap'], ['Каталог','.catalog-grid .anime-card,.catalog-grid .franchise-card']]) {
    const start = Date.now();
    await page.getByRole('button', { name: button, exact: true }).click();
    await page.locator(selector).first().waitFor({ state: 'visible', timeout: 10000 });
    repeatedSections.push({ button, ms: Date.now()-start });
  }
  await page.getByRole('button', { name:'Для вас', exact:true }).click();
  const reasonButtons = page.locator('.reason-btn');
  await reasonButtons.first().waitFor({ state:'visible' });
  const reasons = [];
  for (let index = 0; index < Math.min(3, await reasonButtons.count()); index++) {
    await reasonButtons.nth(index).hover();
    await page.getByRole('tooltip').waitFor();
    reasons.push(await page.getByRole('tooltip').textContent());
    await page.keyboard.press('Escape');
  }
  const report = { samples, repeatedSections, reasons: reasons.slice(0,3), errors };
  await page.evaluate(report => localStorage.setItem('site_read_report', JSON.stringify(report)), report);
  return { samples: samples.map(({api,...row}) => row), reasons:report.reasons, errors:report.errors };
}
