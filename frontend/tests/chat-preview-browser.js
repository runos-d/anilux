async page => {
  const origin = new URL(page.url()).origin;
  const context = await page.context().browser().newContext({ serviceWorkers: 'block' });
  const tab = await context.newPage();
  const errors = [];
  tab.on('pageerror', error => errors.push(error.message));
  const user = { id: 10, username: 'preview', display_name: 'Preview' };
  const chat = { id: 42424242, type: 'private', other_user: { id: 11, username: 'friend' }, name: 'Preview chat' };
  const poster = 'https://shikimori.io/uploads/poster/animes/21/75a07947be55983ce14917f57e96555f.jpeg';
  const anime = { id: 21, title_ru: 'Ван-Пис', title_en: 'One Piece', year: 1999, kind: 'tv', poster_url: poster };
  const playlist = { id: 22, title: 'Любимые приключения', items_count: 1, posters: [poster] };
  const message = { created_at: '2026-10-10T12:32:00+03:00', version: 1, reactions: {}, sender_username: 'preview' };
  const messages = [
    { ...message, id: 101, seq: 1, sender_id: 10, text: '', attachments: [{ type: 'anime', object_id: 21, data: anime }] },
    { ...message, id: 102, seq: 2, sender_id: 11, text: '', shared_playlist_data: playlist, attachments: [] },
    { ...message, id: 103, seq: 3, sender_id: 10, text: 'История с ответом', attachments: [],
      reply_to_message: { id: 101, sender_id: 10, sender_username: 'preview', text: 'Аниме', created_at: message.created_at } },
    { ...message, id: 104, seq: 4, sender_id: 10, text: '', shared_playlist_data: playlist,
      attachments: [{ type: 'playlist', object_id: 22, data: playlist }] },
  ];
  await context.addInitScript(user => {
    localStorage.setItem('anilux_access_token_v1', 'preview-test');
    localStorage.setItem('anilux_user_v1', JSON.stringify(user));
  }, user);
  await tab.routeWebSocket('**/ws/**', socket => socket.close());
  await tab.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (!path.startsWith('/api/')) return route.continue();
    let data = {};
    if (path === '/api/users/profile/') data = user;
    else if (path === '/api/social/chats/42424242/') data = chat;
    else if (path.endsWith('/messages/')) data = { results: messages, has_more: false, next_cursor: null, event_cursor: 0, cleared_through_seq: 0 };
    else if (path.endsWith('/events/')) data = { events: [], latest_sequence: 0 };
    else if (path.endsWith('/all/')) data = { wallpaper: null, theme: null };
    else if (path.endsWith('/theme/')) data = { theme: null };
    else if (path.endsWith('/wallpaper/')) data = { wallpaper: null };
    else if (path.endsWith('/presets/')) data = { presets: [] };
    else if (path.endsWith('/settings/')) data = { notifications_enabled: true };
    else if (path.endsWith('/count/')) data = { count: 0, unread_count: 0 };
    else data = { results: [], count: 0 };
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify(data) });
  });
  let phase = 'HTTP history';
  try {
    await tab.goto(origin + '/chats/42424242?type=private');
    await tab.locator('[data-message-id="103"]').waitFor();
    if (await tab.locator('[data-message-id]').count() !== 4) throw new Error('HTTP history must load without WebSocket');
    if (await tab.locator('[data-message-id="104"] .shared-card').count() !== 1) throw new Error('Compatibility data rendered a duplicate card');
    await tab.reload();
    await tab.locator('[data-message-id="103"]').waitFor();
    if (await tab.locator('[data-message-id]').count() !== 4) throw new Error('History disappeared after reload');
    await tab.locator('[title="Настройки"]').click();
    phase = 'wallpaper posters';
    const modal = tab.locator('.chat-settings-modal');
    const preview = modal.locator('.wp-preview-wrapper');
    await preview.locator('.shared-card.is-anime').waitFor();
    if (await preview.locator('.shared-card').count() !== 2) throw new Error('Preview must include both actual card components');
    if (!(await preview.locator('.chat-card-anime-title').innerText()).includes('Ван-Пис')) throw new Error('Wrong anime example');
    const appearances = await tab.evaluate(() => {
      const styles = selector => {
        const card = document.querySelector(selector), title = card.querySelector('.chat-card-anime-title,.chat-card-playlist-title');
        const poster = card.querySelector('img'), style = getComputedStyle(title), image = getComputedStyle(poster);
        return { font: style.fontSize, weight: style.fontWeight, line: style.lineHeight, posterWidth: image.width, posterHeight: image.height };
      };
      const results = [];
      for (const theme of ['light', 'dark', 'polnochnaya', 'rozovaya', 'blue']) {
        document.documentElement.setAttribute('data-theme', theme);
        for (const type of ['anime', 'playlist']) {
          const live = styles('.messages-list .chat-content-card.is-' + type);
          const preview = styles('.wp-preview-wrapper .chat-content-card.is-' + type);
          if (live.font !== '13px' || JSON.stringify(live) !== JSON.stringify(preview)) throw new Error('Card appearance mismatch: ' + JSON.stringify({ theme, type, live, preview }));
          results.push({ theme, type, ...preview });
        }
      }
      return results;
    });
    await tab.waitForFunction(() => [...document.querySelectorAll('.wp-preview-wrapper .shared-card img')].every(img => img.complete && img.naturalWidth > 0), undefined, { timeout: 30000 });
    const wallpaper = await preview.evaluate(node => ({ cards: node.querySelectorAll('.shared-card').length, posters: [...node.querySelectorAll('img')].map(img => img.naturalWidth) }));
    phase = 'theme appearance';
    await modal.locator('.nav-item').filter({ hasText: 'Тема и стиль' }).click();
    await modal.getByRole('button', { name: 'Сохранить тему', exact: true }).waitFor();
    await modal.locator('input[type="color"]').first().fill('#345678');
    await modal.locator('input[type="range"]').nth(1).fill('24');
    await modal.locator('input[type="range"]').nth(2).fill('8');
    await tab.waitForFunction(() => {
      const anime = document.querySelector('.wp-preview-wrapper .is-anime');
      const playlist = document.querySelector('.wp-preview-wrapper .is-playlist');
      return getComputedStyle(anime).borderRadius === '24px' && getComputedStyle(playlist).borderRadius === '8px' &&
        getComputedStyle(anime).backgroundColor === 'rgb(52, 86, 120)';
    });
    const theme = await preview.evaluate(node => {
      const anime = node.querySelector('.is-anime'), playlist = node.querySelector('.is-playlist');
      return { animeRadius: getComputedStyle(anime).borderRadius, playlistRadius: getComputedStyle(playlist).borderRadius,
        mineBackground: getComputedStyle(anime).backgroundColor, posters: [...node.querySelectorAll('img')].map(img => img.naturalWidth) };
    });
    if (theme.animeRadius !== '24px' || theme.playlistRadius !== '8px' || theme.mineBackground !== 'rgb(52, 86, 120)') throw new Error(JSON.stringify(theme));
    await preview.scrollIntoViewIfNeeded();
    await preview.screenshot({ path: 'backend/data/local_release/ui-real-cards-desktop.png' });
    await tab.setViewportSize({ width: 390, height: 844 });
    await preview.scrollIntoViewIfNeeded();
    const mobile = await preview.evaluate(node => {
      const container = node.querySelector('.chat-detail').getBoundingClientRect();
      return [...node.querySelectorAll('.shared-card')].every(card => {
        const rect = card.getBoundingClientRect();
        return rect.width > 0 && rect.left >= container.left && rect.right <= container.right;
      });
    });
    if (!mobile || errors.length) throw new Error(JSON.stringify({ mobile, errors }));
    await preview.screenshot({ path: 'backend/data/local_release/ui-real-cards-mobile.png' });
    return { historyWithoutWebSocket: 4, historyAfterReload: 4, appearances, wallpaper, theme, mobile, errors };
  } catch (error) {
    const state = await tab.locator('.wp-preview-wrapper').count() ? await tab.locator('.wp-preview-wrapper').evaluate(node => [...node.querySelectorAll('.shared-card')].map(card => ({
      class: card.className, radius: getComputedStyle(card).borderRadius, background: getComputedStyle(card).backgroundColor,
      images: [...card.querySelectorAll('img')].map(img => ({ loaded: img.complete, width: img.naturalWidth })),
    }))) : { body: (await tab.locator('body').innerText()).slice(-600), errors };
    await tab.screenshot({ path: 'backend/data/local_release/ui-real-cards-desktop.png' });
    throw new Error(phase + ': ' + error.message + '; ' + JSON.stringify(state));
  } finally { await context.close(); }
}
