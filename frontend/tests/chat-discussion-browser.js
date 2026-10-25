async page => {
  await page.unrouteAll();
  const errors = [], commands = [], requests = [], sockets = [];
  page.on('pageerror', e => errors.push(e.message));
  const me = { id: 1, username: 'qa_staff', is_staff: true };
  const chat = { id: 80000003, public_id: 80000003, type: 'group', name: 'Франшиза проверки', franchise_id: 91,
    discussion_type: 'franchise', user_role: { is_owner: false, is_admin: true }, user_permissions: { can_manage_chat: true },
    participants_usernames: ['qa_staff'], unread_count: 0 };
  const topics = [{ id: 601, title: 'Общая тема', anime_id: null, slug: 'general' },
    { id: 602, title: 'Первая часть', anime_id: 201, slug: 'part-one' }, { id: 603, title: 'Вторая часть', anime_id: 202, slug: 'part-two' }];
  const message = (id, topic, text, sender = 2) => ({ id, seq: id, version: 1, chat_id: chat.id, chat_type: 'group',
    topic_id: topic, text, sender_id: sender, sender_username: 'qa_peer', created_at: '2026-10-09T12:00:00Z', is_read: true, attachments: [] });
  const history = [message(1, null, 'Старая общая история'), message(2, 602, 'История первой части'), message(3, 603, 'История второй части')];
  history.push({ ...message(4, 603, 'Ответ из другой темы'), reply_to_message: {
    id: 50, text: 'Цитата первой части', sender_id: 2, sender_username: 'qa_peer', topic_id: 602, topic_slug: 'part-one',
  } });
  const backup = { id: 7, chat: chat.id, status: 'completed', status_display: 'Готова', messages_count: 3, members_count: 2,
    file_size_mb: .1, created_at: '2026-10-09T12:00:00Z' };
  let sends = 0, restored = false;
  await page.context().addInitScript(user => {
    localStorage.setItem('anilux_access_token_v1', 'qa-access'); localStorage.setItem('anilux_refresh_token_v1', 'qa-refresh');
    localStorage.setItem('anilux_user_v1', JSON.stringify(user));
  }, me);
  await page.route('**/api/**', async route => {
    const req = route.request(), url = new URL(req.url()), path = url.pathname;
    if (!path.startsWith('/api/')) return route.continue();
    let body = { results: [], count: 0 };
    if (path.includes('/users/profile/') || path.includes('/users/me/')) body = me;
    else if (path.endsWith('/private-chats/') || path.endsWith('/chat-folders/')) body = [];
    else if (path.endsWith('/group-chats/')) body = [chat];
    else if (path === '/api/anime/franchises/qa-franchise/') body = { id: 91, slug: 'qa-franchise' };
    else if (path === '/api/anime/franchises/qa-part/') return route.fulfill({ status: 404, json: {} });
    else if (path === '/api/anime/qa-part/') body = { id: 201, slug: 'qa-part' };
    else if (path === '/api/social/franchise/91/discussion/join/') body = chat;
    else if (path === '/api/social/anime/201/discussion-group/join/') body = { ...chat, topics, current_topic_id: 602 };
    else if (path.endsWith('/franchise-discussion/init/')) body = { group_id: chat.id, topics };
    else if (/\/chats\/\d+\/$/.test(path)) body = chat;
    else if (path.endsWith('/events/')) body = { events: [], cursor: 0, has_more: false };
    else if (path.endsWith('/messages/search/')) body = [message(50, 602, 'Давний результат поиска')];
    else if (path.endsWith('/messages/') && req.method() === 'GET') {
      const topic = Number(url.searchParams.get('topic_id')), around = Number(url.searchParams.get('around'));
      requests.push({ topic, around });
      body = { results: around ? [message(50, topic, 'Давний результат поиска')] : history.filter(m => m.topic_id === topic || topic === 601 && m.topic_id === null), next_cursor: null, event_cursor: 0 };
    } else if (path.endsWith('/messages/') && req.method() === 'POST') {
      const raw = req.postData() || '', key = raw.match(/name="client_message_id"\r\n\r\n([^\r]+)/)?.[1];
      const topic = Number(raw.match(/name="topic_id"\r\n\r\n([^\r]+)/)?.[1]);
      commands.push({ key, topic, file: raw.includes('discussion-file.txt') && raw.includes('discussion bytes') });
      if (++sends === 1) return route.fulfill({ status: 503, json: { detail: 'offline' } });
      body = { ...message(100, topic, 'Отправка в тему', 1), client_message_id: key }; history.push(body);
    } else if (path.endsWith('/chat-backups/')) body = [restored ? { ...backup, restored_at: '2026-10-09T12:30:00Z' } : backup];
    else if (path.endsWith('/chat-backups/7/restore/')) {
      const dry = req.postDataJSON().dry_run; requests.push({ restore: true, dry });
      if (!dry) restored = true; body = { messages_count: 3, members_count: 2, dry_run: dry };
    } else if (path.includes('/chat-settings/')) body = { theme: null, wallpaper: null };
    else if (path.includes('/settings/')) body = { has_hidden_members: false, can_invite_users: true };
    await route.fulfill({ json: body });
  });
  await page.routeWebSocket(/\/ws\/(chat|global|typing)\//, ws => {
    if (new URL(ws.url()).pathname.includes('/chat/')) { sockets.push(ws); ws.send(JSON.stringify({ action: 'init', messages: history, event_cursor: 0, next_cursor: null })); }
    ws.onMessage(raw => { if (JSON.parse(String(raw)).action === 'ping') ws.send('{"action":"pong"}'); });
  });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5174/chats/qa-part');
  await page.waitForURL('**/chats/80000003?type=group&topic=part-one');
  await page.getByText('История первой части', { exact: true }).waitFor();
  await page.goto('http://127.0.0.1:5174/chats/qa-franchise');
  await page.waitForURL('**/chats/80000003?type=group');
  await page.getByRole('tab', { name: 'Общая тема' }).waitFor();
  await page.getByText('Старая общая история', { exact: true }).waitFor();
  if (await page.getByText('История первой части', { exact: true }).count()) throw new Error('General topic mixed history');
  await page.getByRole('tab', { name: 'Первая часть' }).click();
  await page.getByText('История первой части', { exact: true }).waitFor();
  await page.getByPlaceholder('Сообщение...').fill('Черновик первой части');
  await page.getByRole('tab', { name: 'Вторая часть' }).click();
  await page.getByText('История второй части', { exact: true }).waitFor();
  await page.getByPlaceholder('Сообщение...').fill('Черновик второй части');
  sockets.at(-1).send(JSON.stringify({ action: 'new_message', message: message(40, 602, 'Чужая тема') }));
  if (await page.getByText('Чужая тема', { exact: true }).count()) throw new Error('Other topic event leaked');
  await page.locator('.reply-quote').click();
  await page.locator('.messages').getByText('Давний результат поиска', { exact: true }).waitFor();
  if (new URL(page.url()).searchParams.get('topic') !== 'part-one') throw new Error('Reply did not switch to its topic');
  await page.getByRole('tab', { name: 'Первая часть' }).click();
  await page.getByText('История первой части', { exact: true }).waitFor();
  if (await page.getByPlaceholder('Сообщение...').inputValue() !== 'Черновик первой части') throw new Error('Topic draft lost');
  await page.getByPlaceholder('Сообщение...').fill('Отправка в тему');
  await page.locator('input[type=file]').first().setInputFiles({ name: 'discussion-file.txt', mimeType: 'text/plain', buffer: Buffer.from('discussion bytes') });
  await page.getByPlaceholder('Сообщение...').press('Enter'); await page.locator('.retry-message').waitFor();
  await page.reload(); await page.locator('.retry-message').waitFor(); await page.locator('.retry-message').click();
  await page.locator('.retry-message').waitFor({ state: 'detached' });
  if (commands.length !== 2 || commands.some(c => c.topic !== 602 || !c.file) || commands[0].key !== commands[1].key) throw new Error('Topic/file/key not retained: ' + JSON.stringify(commands));
  await page.getByTitle('Поиск по сообщениям', { exact: true }).click();
  await page.getByPlaceholder('Введите текст для поиска...').fill('Давний');
  await page.getByRole('button', { name: 'Найти', exact: true }).click(); await page.locator('.result-item').click();
  await page.locator('.messages').getByText('Давний результат поиска', { exact: true }).waitFor();
  if (!requests.some(r => r.around === 50 && r.topic === 602)) throw new Error('Search did not load anchor');
  await page.locator('.chat-header button[title="Настройки"]').last().click();
  await page.getByRole('button', { name: /Резервные копии/ }).click();
  await page.getByRole('button', { name: 'Проверить восстановление', exact: true }).click();
  await page.getByRole('region', { name: 'Проверка восстановления' }).waitFor();
  if (restored) throw new Error('Dry run restored before confirmation');
  await page.getByRole('button', { name: 'Восстановить проверенную копию', exact: true }).click(); await page.getByText('Восстановлено', { exact: true }).waitFor();
  if (!restored || requests.filter(r => r.restore).length !== 2) throw new Error('Restore workflow failed');
  const runtimeErrors = errors.filter(e => !e.includes('WebSocket closed without opened'));
  if (runtimeErrors.length) throw new Error(runtimeErrors.join('; '));
  return { exactSlugNavigation: true, animeTopicPreserved: true, crossTopicReply: true, topicIsolation: true, independentDrafts: true, durableFileRetry: true, historySearchAnchor: true, backupPreviewAndRestore: true, runtimeErrors };
}
