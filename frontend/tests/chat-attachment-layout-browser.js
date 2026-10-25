async page => {
  const origin = new URL(page.url()).origin;
  const context = await page.context().browser().newContext({ serviceWorkers: 'block' });
  const tab = await context.newPage();
  const errors = [], report = [];
  tab.on('pageerror', error => errors.push(error.message));
  const user = { id: 10, username: 'layout-preview', display_name: 'Проверка размеров' };
  const poster = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="88" height="120"><rect width="88" height="120" fill="#408de8"/><rect x="10" y="15" width="68" height="90" fill="#ffb65c"/></svg>');
  const anime = Array.from({ length: 20 }, (_, index) => ({ id: index + 1, title_ru: `Ван-Пис ${index + 1}`, year: 1999, episodes: 1122, score: 9, poster_url: poster }));
  await context.addInitScript(({ user, origin }) => {
    if (location.origin !== origin) return;
    localStorage.setItem('anilux_access_token_v1', 'layout-preview');
    localStorage.setItem('anilux_user_v1', JSON.stringify(user));
  }, { user, origin });
  await tab.routeWebSocket('**/ws/**', socket => {
    socket.send(JSON.stringify({ action: 'init', messages: [], event_cursor: 0, cleared_through_seq: 0 }));
  });
  await tab.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (!path.startsWith('/api/')) return route.continue();
    let data = { results: [], count: 0 };
    if (path === '/api/users/profile/') data = user;
    else if (path === '/api/social/chats/42424242/') data = { id: 42424242, type: 'private', other_user: { id: 11, username: 'friend' }, user_settings: {} };
    else if (path === '/api/anime/attachment-search/') data = { count: 20, page: 1, has_more: false, results: anime };
    else if (path.endsWith('/messages/')) data = { results: [], has_more: false, next_cursor: null, event_cursor: 0, cleared_through_seq: 0 };
    else if (path.endsWith('/events/')) data = { events: [], cursor: 0, has_more: false };
    else if (path.endsWith('/all/')) data = { wallpaper: null, theme: null };
    else if (path.endsWith('/theme/')) data = { theme: null };
    else if (path.endsWith('/wallpaper/')) data = { wallpaper: null };
    else if (path.endsWith('/presets/')) data = { presets: [] };
    else if (path.endsWith('/settings/')) data = { notifications_enabled: true };
    else if (path.endsWith('/count/')) data = { count: 0, unread_count: 0 };
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
  });
  try {
    await tab.goto(origin + '/chats/42424242?type=private');
    await tab.waitForFunction(() => { const el = document.querySelector('.message-textarea'); return el && !el.disabled; });
    await tab.locator('.input-row > .input-action').first().click();
    await tab.getByRole('button', { name: 'Аниме', exact: true }).click();
    await tab.locator('.attach-picker-search input').fill('Ван-Пис');
    await tab.waitForFunction(() => [...document.querySelectorAll('.attach-poster')].length === 20 && [...document.querySelectorAll('.attach-poster')].every(image => image.complete && image.naturalWidth > 0));
    const compactButtons = await tab.addStyleTag({ content: '.attach-picker-modal button.attach-result-item { height: 44px !important; }' });
    for (const width of [1280, 390]) {
      await tab.setViewportSize({ width, height: 844 });
      for (const theme of ['light', 'dark', 'polnochnaya', 'rozovaya', 'blue']) {
        await tab.evaluate(theme => document.documentElement.setAttribute('data-theme', theme), theme);
        const geometry = await tab.locator('.attach-result-item').evaluateAll(items => items.map(item => {
          const card = item.getBoundingClientRect(), image = item.querySelector('img'), rect = image.getBoundingClientRect(), style = getComputedStyle(item);
          return { height: card.height, posterHeight: rect.height, topInset: rect.top - card.top, bottomInset: card.bottom - rect.bottom,
            leftInset: rect.left - card.left, rightInset: card.right - rect.right, naturalWidth: image.naturalWidth,
            cssHeight: style.height, minHeight: style.minHeight, maxHeight: style.maxHeight, overflow: style.overflow, flex: style.flex, padding: style.padding };
        }));
        report.push({ width, theme, first: geometry[0], posterWithinPadding: geometry.every(item => item.topInset >= 11 && item.bottomInset >= 11 && item.leftInset >= 11 && item.rightInset >= 11) });
      }
    }
    await compactButtons.evaluate(element => element.remove());
    const rules = await tab.locator('.attach-result-item').first().evaluate(item => {
      const results = [];
      const visit = rules => { for (const rule of rules) {
        if (rule.selectorText && rule.style && item.matches(rule.selectorText) && (rule.style.height || rule.style.minHeight || rule.style.maxHeight)) results.push({ selector: rule.selectorText, height: rule.style.height, minHeight: rule.style.minHeight, maxHeight: rule.style.maxHeight });
        if (rule.cssRules) visit(rule.cssRules);
      } };
      for (const sheet of document.styleSheets) { try { visit(sheet.cssRules); } catch {} }
      return results;
    });
    await tab.locator('.attach-picker-modal').screenshot({ path: 'backend/data/local_release/chat-attachment-layout.png' });
    const passed = report.every(item => item.posterWithinPadding) && errors.length === 0;
    if (!passed) throw new Error(JSON.stringify({ report, errors }));
    return { report, matchedHeightRules: rules, errors, passed };
  } finally { await context.close(); }
}
