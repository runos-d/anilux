async page => {
  await page.unrouteAll();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const me = { id: 1, username: 'qa_user', display_name: 'Проверка', email: 'qa@test.local', is_online: true };
  const chats = {
    80000001: { id: 80000001, public_id: 80000001, code: '80000001', type: 'private', name: 'Собеседник', other_user: { id: 2, username: 'qa_peer', display_name: 'Собеседник' }, unread_count: 0, user_settings: {}, is_blocked: { blocked: false } },
    80000002: { id: 80000002, public_id: 80000002, code: '80000002', type: 'group', name: 'Группа проверки', participants_usernames: ['qa_user', 'qa_peer'], user_permissions: {}, unread_count: 0, is_blocked: { blocked: false } }
  };
  const message = (id, chatId, text) => ({ id, seq: id, version: 1, chat_id: chatId, chat_type: chats[chatId].type, text: text || `История ${id}`, sender_id: 2, sender_username: 'qa_peer', created_at: '2026-10-09T12:00:00Z', is_read: true, attachments: [] });
  const messages = Object.fromEntries(Object.keys(chats).map(id => [id, Array.from({ length: id === '80000001' ? 5000 : 30 }, (_, i) => message(i + 1, Number(id)))]));
  const image = { id: 901, type: 'image', file_url: '/api/social/chat-media/attachments/qa.png?ticket=expired', file_name: 'qa.png', mime_type: 'image/png' };
  messages[80000001].at(-1).attachments = [image];
  let mediaRenewals = 0;
  let sends = 0;
  const sockets = [];
  let connectedAgain;
  const keys = [];
  const fileParts = [];
  await page.context().addInitScript(user => {
    localStorage.setItem('anilux_access_token_v1', 'qa-access');
    localStorage.setItem('anilux_refresh_token_v1', 'qa-refresh');
    localStorage.setItem('anilux_user_v1', JSON.stringify(user));
  }, me);
  await page.route('**/api/**', async route => {
    const req = route.request(), url = new URL(req.url()), path = url.pathname;
    if (!path.startsWith('/api/')) return route.continue();
    if (path.startsWith('/api/social/chat-media/')) {
      if (url.searchParams.get('ticket') !== 'fresh') return route.fulfill({ status: 403, json: { detail: 'Expired link' } });
      return route.fulfill({ contentType: 'image/png', body: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5XsAAAAASUVORK5CYII=', 'base64') });
    }
    let body = { results: [], count: 0 };
    if (path.includes('/users/profile/') || path.includes('/users/me/')) body = me;
    else if (path.endsWith('/private-chats/')) body = [chats[80000001]];
    else if (path.endsWith('/group-chats/')) body = [chats[80000002]];
    else if (path.endsWith('/chat-folders/')) body = [];
    else if (/\/chats\/\d+\/$/.test(path)) body = chats[Number(path.match(/\/chats\/(\d+)/)[1])];
    else if (path.endsWith('/events/')) body = { events: [], cursor: 0, has_more: false };
    else if (path.endsWith('/messages/') && req.method() === 'GET') {
      const id = Number(path.match(/\/chats\/(\d+)/)[1]);
      if (id === 80000001 && url.searchParams.get('around') === '5000') {
        mediaRenewals++;
        image.file_url = '/api/social/chat-media/attachments/qa.png?ticket=fresh';
      }
      body = { results: messages[id].slice(-50), event_cursor: 12, next_cursor: null, cleared_through_seq: 0 };
    }
    else if (path.endsWith('/messages/') && req.method() === 'POST') {
      sends++;
      const raw = req.postData() || '';
      const key = raw.match(/name="client_message_id"\r\n\r\n([^\r]+)/)?.[1];
      keys.push(key);
      fileParts.push(raw.includes('reload-test.txt') && raw.includes('reload-safe-file'));
      if (sends === 1) return route.fulfill({ status: 503, json: { detail: 'Simulated offline delivery' } });
      const id = Number(path.match(/\/chats\/(\d+)/)[1]);
      body = { ...message(5001, id, 'Повтор отправки'), sender_id: 1, client_message_id: key };
      messages[id].push(body);
    }
    else if (path.endsWith('/mark_read/') || path.endsWith('/read/')) body = { success: true, message_ids: [], unread_count: 0 };
    else if (path.endsWith('/unread-chats/')) body = [];
    else if (path.endsWith('/reactions/') || path.endsWith('/pinned-messages/')) body = [];
    else if (path.includes('/chat-settings/')) body = { theme: null, wallpaper: null };
    else if (path.includes('settings') || path.includes('appearance')) body = {};
    await route.fulfill({ json: body });
  });
  await page.routeWebSocket(/\/ws\/(chat|global|typing)\//, ws => {
    const url = new URL(ws.url());
    const id = Number(url.pathname.match(/\/chat\/(\d+)/)?.[1]);
    if (id) { sockets.push(ws); connectedAgain?.(); }
    if (id) ws.send(JSON.stringify({ action: 'init', messages: messages[id], event_cursor: 0, has_more: false, next_cursor: null, cleared_through_seq: 0 }));
    ws.onMessage(raw => { const data = JSON.parse(String(raw)); if (data.action === 'ping') ws.send(JSON.stringify({ action: 'pong' })); });
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5174/chats/80000001');
  await page.getByPlaceholder('Сообщение...').waitFor();
  await page.locator('[data-timeline-id]').first().waitFor();
  await page.locator('img[src*="ticket=fresh"]').waitFor();
  await page.waitForFunction(() => [...document.querySelectorAll('img[src*="ticket=fresh"]')].some(image => image.naturalWidth === 1));
  if (mediaRenewals !== 1) throw new Error(`Unexpected media renewals: ${mediaRenewals}`);
  const rendered = await page.locator('[data-timeline-id]').count();
  if (rendered >= 50) throw new Error(`Virtual timeline rendered ${rendered} nodes`);
  await page.getByPlaceholder('Сообщение...').fill('Повтор отправки');
  await page.locator('input[type=file]').first().setInputFiles({ name: 'reload-test.txt', mimeType: 'text/plain', buffer: Buffer.from('reload-safe-file') });
  await page.getByPlaceholder('Сообщение...').press('Enter');
  await page.locator('.retry-message').waitFor();
  await page.reload();
  await page.locator('.retry-message').waitFor();
  await page.getByText('reload-test.txt', { exact: true }).waitFor();
  await page.getByText('Группа проверки', { exact: true }).first().click();
  await page.locator('.chat-name').filter({ hasText: 'Группа проверки' }).waitFor();
  await page.goBack();
  await page.locator('.chat-name').filter({ hasText: 'Собеседник' }).waitFor();
  await page.locator('.retry-message').waitFor();
  await page.locator('.retry-message').click();
  await page.locator('.retry-message').waitFor({ state: 'detached' });
  if (keys.length !== 2 || !keys[0] || keys[0] !== keys[1]) throw new Error(`Unstable command keys: ${keys}`);
  if (fileParts.some(found => !found)) throw new Error('Reload lost the queued file');
  await page.getByPlaceholder('Сообщение...').fill('Черновик');
  await page.getByText('Группа проверки', { exact: true }).first().click();
  await page.locator('.chat-name').filter({ hasText: 'Группа проверки' }).waitFor();
  await page.getByPlaceholder('Сообщение...').fill('Черновик группы');
  await page.goBack();
  await page.locator('.chat-name').filter({ hasText: 'Собеседник' }).waitFor();
  if (await page.getByPlaceholder('Сообщение...').inputValue() !== 'Черновик') throw new Error('Draft lost during navigation');
  const nextConnection = new Promise(resolve => { connectedAgain = resolve; });
  sockets.at(-1).close({ code: 1012, reason: 'Test reconnect' });
  await Promise.race([nextConnection, new Promise((_, reject) => setTimeout(() => reject(new Error('Reconnect timed out')), 10000))]);
  await page.getByText('Повтор отправки', { exact: true }).waitFor();
  if (await page.getByText('Повтор отправки', { exact: true }).count() !== 1) throw new Error('Reconnect duplicated a message');
  sockets.at(-1).send(JSON.stringify({ action: 'chat_cleared', cleared_through_seq: 5001 }));
  await page.getByText('Повтор отправки', { exact: true }).waitFor({ state: 'detached' });
  sockets.at(-1).send(JSON.stringify({ action: 'new_message', message: message(5000, 80000001, 'Запоздавшее сообщение') }));
  sockets.at(-1).send(JSON.stringify({ action: 'new_message', message: message(5002, 80000001, 'После очистки') }));
  await page.getByText('После очистки', { exact: true }).waitFor();
  if (await page.getByText('Запоздавшее сообщение', { exact: true }).count()) throw new Error('Cleared history resurrected');
  sockets.at(-1).send(JSON.stringify({ action: 'chat_restored', sequence: 12 }));
  await page.getByText('Повтор отправки', { exact: true }).waitFor();
  sockets.at(-1).send(JSON.stringify({ action: 'chat_cleared', sequence: 11, cleared_through_seq: 5001 }));
  if (await page.getByText('Повтор отправки', { exact: true }).count() !== 1) throw new Error('Late clear erased restored history');
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByPlaceholder('Сообщение...').waitFor();
  await page.getByRole('button', { name: 'К списку чатов' }).click();
  await page.waitForURL('**/chats');
  const privateEntry = page.getByText('Собеседник', { exact: true }).first();
  await privateEntry.click();
  await page.locator('.chat-name').filter({ hasText: 'Собеседник' }).waitFor();
  await page.getByPlaceholder('Сообщение...').waitFor();
  const failures = errors.filter(error => !error.includes('WebSocket closed without opened'));
  if (failures.length) throw new Error(`Runtime errors: ${failures.join('; ')}`);
  const peer = await page.context().newPage();
  await peer.route('**/api/**', route => route.fulfill({ json: {} }));
  await peer.goto('http://127.0.0.1:5174/');
  await peer.evaluate(() => {
    localStorage.removeItem('anilux_access_token_v1');
    localStorage.removeItem('anilux_refresh_token_v1');
    localStorage.removeItem('anilux_user_v1');
  });
  await page.waitForURL('**/login');
  if (await page.locator('.messages').count()) throw new Error('Chat remained visible after another tab logged out');
  await peer.close();
  return { expiredMediaRenewed: true, crossTabLogout: true, renderedMessages: rendered, retryPreservedKey: true, pendingSurvivesNavigation: true, queuedFileSurvivesReload: true, restoredHistoryIgnoresLateClear: true, draftsIndependent: true, reconnectPreservesTimeline: true, clearedHistoryStaysHidden: true, mobileComposerVisible: true, mobileBackAndSelectionWorks: true, runtimeErrors: failures };

}
