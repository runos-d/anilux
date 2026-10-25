async page => {
  const savedAuth = await page.evaluate(() => JSON.parse(sessionStorage.getItem('chat_ui_auth') || 'null'));
  const ownContext = await page.context().browser().newContext({ serviceWorkers: 'block' });
  page = await ownContext.newPage();
  const origin = 'http://localhost:8080', api = origin + '/api';
  const errors = [], warnings = [], failures = [];
  const peerContext = await page.context().browser().newContext({ serviceWorkers: 'block' });
  const peer = await peerContext.newPage();
  const guestContext = await page.context().browser().newContext({ serviceWorkers: 'block' });
  const guest = await guestContext.newPage();
  guest.on('pageerror', error => errors.push(error.message));
  const json = async response => {
    if (!response.ok()) throw new Error(`API ${response.status()}: ${(await response.text()).slice(0, 250)}`);
    return response.status() === 204 ? null : response.json();
  };
  const assert = (condition, message) => { if (!condition) throw new Error(message); };
  const a = savedAuth?.a || await json(await page.request.post(api + '/users/login/', { data: { username: 'ui_browser_20261010_a', password: 'Chat-E2E-Local-123' } }));
  const b = savedAuth?.b || await json(await peer.request.post(api + '/users/login/', { data: { username: 'ui_browser_20261010_b', password: 'Chat-E2E-Local-123' } }));
  const auth = user => ({ Authorization: 'Bearer ' + user.tokens.access });
  for (const [tab, user] of [[page, a], [peer, b]]) {
    tab.on('pageerror', error => errors.push(error.message));
    tab.on('console', message => { if (message.type() === 'warning' && /No match found/.test(message.text())) warnings.push(message.text()); });
    tab.on('response', response => { if (response.status() >= 500 && response.url().includes('/api/social/')) failures.push(response.url()); });
    await tab.context().addInitScript(user => {
      localStorage.setItem('anilux_access_token_v1', user.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1', user.tokens.refresh);
      localStorage.setItem('anilux_user_v1', JSON.stringify(user.user));
    }, user);
  }
  let stage = 'private chat';
  try {
    const chat = await json(await page.request.post(api + '/social/private-chats/', { headers: auth(a), data: { user_id: b.user.id } }));
    await page.goto(`${origin}/chats/${chat.id}?type=private`);
    const composer = page.getByPlaceholder('Сообщение...');
    await composer.waitFor({ timeout: 60000 });
    await page.waitForFunction(() => !document.querySelector('.message-textarea')?.disabled);
    const detail = await json(await page.request.get(`${api}/social/chats/${chat.id}/?type=private`, { headers: auth(a) }));
    const expectedAvatar = detail.other_user.avatar_url;
    await page.waitForFunction(expected => document.querySelector('.chat-header .avatar')?.getAttribute('src') === expected, expectedAvatar);
    const row = page.locator('.chat-list-item').filter({ hasText: 'ui_browser_20261010_b' });
    await row.waitFor();
    assert((await row.locator('img').getAttribute('src')) === expectedAvatar, 'Sidebar lost installed avatar');
    const text = 'Stable bubble ' + Date.now();
    await page.evaluate(text => {
      window.__bubbleNode = null;
      window.__bubbleRemoved = false;
      const root = document.querySelector('.messages');
      window.__bubbleObserver = new MutationObserver(records => {
        if (!window.__bubbleNode) window.__bubbleNode = [...root.querySelectorAll('.message')].find(node => Number(node.dataset.messageId) < 0 && node.textContent.includes(text));
        if (window.__bubbleNode && !window.__bubbleNode.isConnected) window.__bubbleRemoved = true;
      });
      window.__bubbleObserver.observe(root, { childList: true, subtree: true });
    }, text);
    await page.route(`**/api/social/chats/${chat.id}/messages/`, async route => {
      if (route.request().method() !== 'POST') return route.continue();
      const response = await route.fetch();
      await new Promise(resolve => setTimeout(resolve, 600));
      await route.fulfill({ response });
    });
    const sentResponse = page.waitForResponse(response => response.url().endsWith(`/chats/${chat.id}/messages/`) && response.request().method() === 'POST');
    await composer.fill(text); await composer.press('Enter');
    await page.waitForFunction(text => [...document.querySelectorAll('.message')].some(node => Number(node.dataset.messageId) > 0 && node.textContent.includes(text)), text);
    await sentResponse;
    const continuity = await page.evaluate(() => ({ observed: !!window.__bubbleNode, removed: window.__bubbleRemoved, connected: window.__bubbleNode?.isConnected }));
    assert(continuity.observed && !continuity.removed && continuity.connected, 'Acknowledgement recreated message node: ' + JSON.stringify(continuity));
    assert(await page.locator('.messages').getByText(text, { exact: true }).count() === 1, 'Message duplicated');
    await page.unroute(`**/api/social/chats/${chat.id}/messages/`);
    await composer.fill('Second spaced message'); await composer.press('Enter');
    await page.waitForFunction(() => [...document.querySelectorAll('.message')].filter(node => Number(node.dataset.messageId) > 0).length >= 2);
    const spacing = await page.evaluate(() => {
      const rows = [...document.querySelectorAll('.timeline-item')];
      return parseFloat(getComputedStyle(rows[0]).paddingBottom);
    });
    assert(spacing >= 8, 'Message spacing was not increased');
    await page.locator('[title="Настройки"]').click();
    const modal = page.locator('.chat-settings-modal');
    await modal.locator('.wp-preview-wrapper').waitFor();
    assert(await modal.getByText('Ван-Пис', { exact: true }).count() === 1, 'Anime missing from wallpaper preview');
    assert(await modal.getByText('Любимые приключения', { exact: true }).count() === 1, 'Playlist missing from wallpaper preview');
    assert(await modal.locator('.nav-item').filter({ hasText: /Перенос настроек|Модерация|Резервные копии/ }).count() === 0, 'Advanced settings are visible');
    await modal.locator('input[type="color"]').first().fill('#234567');
    await Promise.all([
      page.waitForResponse(response => response.url().endsWith('/wallpaper/') && response.request().method() === 'GET'),
      modal.getByRole('button', { name: 'Сохранить обои', exact: true }).click(),
    ]);
    const wallpaper = await json(await page.request.get(`${api}/social/chat-settings/private/${chat.id}/wallpaper/`, { headers: auth(a) }));
    assert(wallpaper.wallpaper.wallpaper_color === '#234567', 'Wallpaper did not persist');
    await modal.locator('.nav-item').filter({ hasText: 'Тема и стиль' }).click();
    await modal.getByRole('button', { name: 'Сохранить тему', exact: true }).waitFor();
    await modal.locator('input[type="color"]').first().fill('#123456');
    await modal.locator('input[type="range"]').nth(1).fill('22');
    await modal.locator('input[type="range"]').nth(2).fill('25');
    await Promise.all([
      page.waitForResponse(response => response.url().endsWith('/theme/') && response.request().method() === 'GET'),
      modal.getByRole('button', { name: 'Сохранить тему', exact: true }).click(),
    ]);
    const theme = await json(await page.request.get(`${api}/social/chat-settings/private/${chat.id}/theme/`, { headers: auth(a) }));
    assert(theme.theme.message_color_mine === '#123456' && theme.theme.anime_card_border_radius === 22 && theme.theme.playlist_card_border_radius === 25, 'Theme fields were lost');
    await modal.locator('.nav-item').filter({ hasText: 'Уведомления' }).click();
    await modal.locator('input[type="checkbox"]').first().uncheck();
    assert(await modal.getByText(/Только упоминания|Вибрация|Тип вибрации/).count() === 0, 'Advanced notifications still visible');
    await Promise.all([
      page.waitForResponse(response => response.url().endsWith(`/private-chats/${chat.id}/settings/`) && response.request().method() === 'GET'),
      modal.getByRole('button', { name: 'Сохранить', exact: true }).click(),
    ]);
    const notifications = await json(await page.request.get(`${api}/social/private-chats/${chat.id}/settings/`, { headers: auth(a) }));
    assert(!notifications.notifications_enabled, 'Notification toggle did not persist');
    await modal.locator('.nav-item').filter({ hasText: 'Организация' }).click();
    assert(await modal.getByText(/Скрыть чат|Автоудаление/).count() === 0, 'Disabled organization controls still visible');
    await modal.locator('input[type="checkbox"]').nth(1).check();
    await modal.locator('.close-btn').click();
    await page.getByRole('button', { name: /^Архив \(/ }).click();
    await row.waitFor();
    await row.click({ button: 'right' });
    await page.locator('.context-menu-item').filter({ hasText: 'Вернуть из архива' }).click();
    await row.waitFor({ state: 'hidden' });
    await page.getByRole('button', { name: 'Все чаты', exact: true }).click();
    await row.waitFor();
    const anime = await json(await page.request.get(api + '/anime/8753/', { headers: auth(a) }));
    assert(!!anime, 'Local One Piece data missing');
    const attached = await json(await page.request.post(`${api}/social/chats/${chat.id}/messages/`, { headers: auth(a), data: { chat_type: 'private', 'anime_ids[]': [anime.id], client_message_id: crypto.randomUUID() } }));
    await page.locator('[title="Поиск по сообщениям"]').click();
    await page.getByPlaceholder('Введите текст для поиска...').fill('One Piece');
    await page.getByRole('button', { name: 'Найти', exact: true }).click();
    await page.locator('.result-item').filter({ hasText: anime.title_ru || anime.title_en }).first().waitFor();
    await page.locator('.modal-content .close-btn').click();
    const group = await json(await page.request.post(api + '/social/group-chats/', { headers: auth(a), data: { name: 'UI browser group', description: 'Initial description', is_public: true } }));
    const invite = await json(await page.request.post(api + '/social/chat-invite-links/', { headers: auth(a), data: { chat: group.id } }));
    const inviteToken = invite.invite_link.split('/').filter(Boolean).pop();
    assert(!!inviteToken && inviteToken !== 'undefined', 'Invite response has no link');
    stage = 'authenticated invitation';
    await peer.goto(`${origin}/chats/invite/${inviteToken}`);
    await peer.getByRole('button', { name: 'Перейти в чат', exact: true }).waitFor({ timeout: 30000 });
    await peer.getByRole('button', { name: 'Перейти в чат', exact: true }).click();
    await peer.getByPlaceholder('Сообщение...').waitFor();
    assert(peer.url().includes('/chats/' + group.id), 'Invitation did not navigate to joined chat');
    stage = 'guest invitation and login';
    await guest.goto(`${origin}/chats/invite/${inviteToken}`);
    await guest.locator('.invite-container').getByRole('button', { name: 'Войти', exact: true }).click();
    await guest.locator('#username').fill('ui_browser_20261010_b');
    await guest.locator('#password').fill('Chat-E2E-Local-123');
    await guest.locator('.auth-form button[type="submit"]').click();
    await guest.getByRole('button', { name: 'Перейти в чат', exact: true }).waitFor();
    await guest.getByRole('button', { name: 'Перейти в чат', exact: true }).click();
    await guest.getByPlaceholder('Сообщение...').waitFor();
    assert(guest.url().includes('/chats/' + group.id), 'Login lost the invitation');
    stage = 'group metadata';
    await page.goto(`${origin}/chats/${group.id}?type=group`);
    await composer.waitFor();
    await page.locator('[title="Настройки"]').click();
    await modal.locator('.nav-item').filter({ hasText: 'Название, описание и фото' }).click();
    await modal.locator('#chat-group-name').fill('Новое название группы');
    await modal.locator('#chat-group-description').fill('Новое описание группы');
    await Promise.all([
      page.waitForResponse(response => response.url().endsWith(`/group-chats/${group.id}/`) && response.request().method() === 'PATCH'),
      modal.getByRole('button', { name: 'Сохранить название и описание', exact: true }).click(),
    ]);
    const savedGroup = await json(await page.request.get(`${api}/social/group-chats/${group.id}/`, { headers: auth(a) }));
    assert(savedGroup.name === 'Новое название группы' && savedGroup.description === 'Новое описание группы', 'Group metadata did not persist');
    await modal.locator('.close-btn').click();
    await peer.waitForFunction(() => !document.querySelector('.message-textarea')?.disabled);
    await peer.getByPlaceholder('Сообщение...').fill('Delivery after group settings');
    await peer.getByPlaceholder('Сообщение...').press('Enter');
    await page.locator('.messages').getByText('Delivery after group settings', { exact: true }).waitFor();
    assert(errors.length === 0 && warnings.length === 0 && failures.length === 0, JSON.stringify({ errors, warnings, failures }));
    return { avatar: true, stableMessageNode: continuity, spacing, wallpaper: true, theme: true, cardRadii: true, notifications: true, archiveRoundTrip: true, animeSearch: attached.id, invite: true, guestLoginReturn: true, groupMetadata: true, errors, warnings, failures };
  } catch (error) {
    const tab = stage.startsWith('guest') ? guest : stage.startsWith('authenticated') ? peer : page;
    throw new Error(`${stage}: ${error.message}; ${tab.url()}; ${(await tab.locator('body').innerText()).slice(-2500)}`);
  } finally { await peerContext.close(); await guestContext.close(); await ownContext.close(); }
}
