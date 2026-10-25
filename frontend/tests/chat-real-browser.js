async page => {
  const config = new URL(page.url()).searchParams;
  const options = await page.evaluate(() => {
    try { return JSON.parse(sessionStorage.getItem('chat_test_config') || '{}'); } catch { return {}; }
  });
  const api = options.api || config.get('test_api') || 'http://127.0.0.1:8001/api';
  const origin = options.origin || config.get('test_origin') || 'http://127.0.0.1:5174';
  const errors = [];
  const peerContext = await page.context().browser().newContext();
  const peer = await peerContext.newPage();
  try {
  const run = Date.now();
  const json = async response => {
    if (!response.ok()) throw new Error(`Real API ${response.status()}: ${(await response.text()).slice(0, 300)}`);
    return response.status() === 204 ? null : response.json();
  };
  const login = async (context, username) => json(await context.request.post(api + '/users/login/',
    { data: { username, password: 'Chat-E2E-Local-123' } }));
  const a = await login(page.context(), options.userA || config.get('test_user_a') || 'chat_e2e_a');
  const b = await login(peerContext, options.userB || config.get('test_user_b') || 'chat_e2e_b');
  const auth = user => ({ Authorization: 'Bearer ' + user.tokens.access });
  for (const [tab, user] of [[page, a], [peer, b]]) {
    tab.on('pageerror', error => errors.push(error.message));
    await tab.context().addInitScript(user => {
      localStorage.setItem('anilux_access_token_v1', user.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1', user.tokens.refresh);
      localStorage.setItem('anilux_user_v1', JSON.stringify(user.user));
    }, user);
    tab.on('dialog', dialog => dialog.accept());
  }
  const created = await json(await page.request.post(api + '/social/private-chats/', { headers: auth(a), data: { user_id: b.user.id } }));
  const repeated = await json(await peer.request.post(api + '/social/private-chats/', { headers: auth(b), data: { user_id: a.user.id } }));
  if (created.id !== repeated.id) throw new Error('Reverse pair created a duplicate chat');
  for (const tab of [page, peer]) {
    await tab.goto(`${origin}/chats/${created.id}?type=private`);
    await tab.getByPlaceholder('Сообщение...').waitFor({ timeout: 60000 });
    await tab.getByPlaceholder('Сообщение...').waitFor({ state: 'visible' });
    await tab.waitForFunction(() => !document.querySelector('.message-textarea')?.disabled, null, { timeout: 60000 });
  }
  const text = 'Real delivery ' + run;
  await page.getByPlaceholder('Сообщение...').fill(text);
  await page.getByPlaceholder('Сообщение...').press('Enter');
  await peer.locator('.messages').getByText(text, { exact: true }).waitFor({ timeout: 30000 });
  const history = async () => (await json(await page.request.get(`${api}/social/chats/${created.id}/messages/?type=private`, { headers: auth(a) }))).results;
  const message = (await history()).find(message => message.text === text);
  if (!message) throw new Error('HTTP send was not persisted');
  const own = page.locator(`[data-message-id="${message.id}"]`);
  await page.getByPlaceholder('Сообщение...').fill('Preserved normal draft');
  await own.click({ button: 'right' });
  await page.locator('.context-popup').getByRole('button', { name: 'Изменить', exact: true }).click();
  const edited = 'Edited live ' + run;
  await page.getByPlaceholder('Сообщение...').fill(edited);
  await page.getByRole('button', { name: 'Сохранить изменение', exact: true }).click();
  await peer.locator('.messages').getByText(edited, { exact: true }).waitFor();
  if (await page.getByPlaceholder('Сообщение...').inputValue() !== 'Preserved normal draft') throw new Error('Edit overwrote composer draft');
  await own.click({ button: 'right' });
  await page.locator('.context-popup').getByRole('button', { name: 'Изменить', exact: true }).click();
  const remote = 'Changed on device two ' + run, local = 'Deliberate conflict retry ' + run;
  await page.getByPlaceholder('Сообщение...').fill(local);
  const current = (await history()).find(row => row.id === message.id);
  await json(await peer.request.post(`${api}/social/messages/${message.id}/edit/`, { headers: auth(a), data: { text: remote, version: current.version } }));
  const conflict = page.waitForResponse(response => response.url().endsWith(`/messages/${message.id}/edit/`) && response.status() === 409);
  await page.getByRole('button', { name: 'Сохранить изменение', exact: true }).click(); await conflict;
  await page.locator('.edit-preview').getByText(remote, { exact: true }).waitFor();
  if (await page.getByPlaceholder('Сообщение...').inputValue() !== local) throw new Error('409 lost unsaved edit');
  await page.getByRole('button', { name: 'Сохранить изменение', exact: true }).click();
  await peer.locator('.messages').getByText(local, { exact: true }).waitFor();
  await page.getByPlaceholder('Сообщение...').fill('File after reload ' + run);
  await page.locator('input[type=file]').first().setInputFiles({ name: 'real-reload.txt', mimeType: 'text/plain', buffer: Buffer.from('real durable file bytes') });
  let failed = false;
  const sendPattern = `**/social/chats/${created.id}/messages/`;
  await page.route(sendPattern, async route => {
    if (!failed && route.request().method() === 'POST') { failed = true; return route.abort('connectionreset'); }
    return route.continue();
  });
  await page.getByPlaceholder('Сообщение...').press('Enter');
  await page.locator('.retry-message').waitFor();
  await page.unroute(sendPattern); await page.reload();
  await page.locator('.retry-message').waitFor({ timeout: 60000 });
  await page.locator('.retry-message').click();
  await peer.locator('.messages').getByText('File after reload ' + run, { exact: true }).waitFor();
  const files = (await history()).filter(row => row.text === 'File after reload ' + run);
  if (files.length !== 1) throw new Error('Retry created duplicate messages');
  const download = await page.request.get(files[0].attachments[0].file_url, { headers: auth(a) });
  if (!download.ok() || (await download.body()).toString() !== 'real durable file bytes') throw new Error('Private file bytes changed');
  await own.click({ button: 'right' });
  await page.locator('.context-popup').getByRole('button', { name: 'Удалить', exact: true }).click();
  await peer.locator(`[data-message-id="${message.id}"]`).waitFor({ state: 'detached' });
  const group = await json(await page.request.post(api + '/social/group-chats/', { headers: auth(a), data: { name: 'Real group ' + run, participants: [b.user.id] } }));
  for (const tab of [page, peer]) {
    await tab.goto(`${origin}/chats/${group.id}?type=group`);
    await tab.getByPlaceholder('Сообщение...').waitFor({ timeout: 60000 });
    await tab.waitForFunction(() => !document.querySelector('.message-textarea')?.disabled, null, { timeout: 60000 });
  }
  const groupText = 'Group archive ' + run;
  await page.getByPlaceholder('Сообщение...').fill(groupText);
  await page.getByPlaceholder('Сообщение...').press('Enter');
  await peer.locator('.messages').getByText(groupText, { exact: true }).waitFor();
  await page.locator('.chat-header button[title="Настройки"]').last().click();
  await page.getByRole('button', { name: /Резервные копии/ }).click();
  await page.getByRole('button', { name: 'Создать копию', exact: true }).click();
  await page.getByRole('button', { name: 'Проверить восстановление', exact: true }).waitFor({ timeout: 45000 });
  const groupHistory = await json(await page.request.get(`${api}/social/chats/${group.id}/messages/?type=group`, { headers: auth(a) }));
  const archived = groupHistory.results.find(row => row.text === groupText);
  await json(await page.request.delete(`${api}/social/messages/${archived.id}/`, { headers: auth(a) }));
  await peer.locator(`[data-message-id="${archived.id}"]`).waitFor({ state: 'detached' });
  await page.getByRole('button', { name: 'Проверить восстановление', exact: true }).click();
  await page.getByRole('region', { name: 'Проверка восстановления' }).waitFor();
  await page.getByRole('button', { name: 'Восстановить проверенную копию', exact: true }).click();
  await peer.locator('.messages').getByText(groupText, { exact: true }).waitFor();
  await peer.reload();
  await peer.locator('.messages').getByText(groupText, { exact: true }).waitFor({ timeout: 60000 });
  await json(await page.request.delete(`${api}/social/group-chats/${group.id}/`, { headers: auth(a) }));
  await peer.waitForFunction(() => {
    const composer = document.querySelector('.message-textarea');
    return !composer || composer.disabled;
  }, null, { timeout: 30000 });
  const revoked = await peer.request.get(`${api}/social/chats/${group.id}/messages/?type=group`, { headers: auth(b) });
  if (revoked.status() !== 404) throw new Error('Deleted group history remained accessible');
  const runtimeErrors = errors;
  if (runtimeErrors.length) throw new Error(runtimeErrors.join('; '));
  return { transport: 'real MySQL/Redis/Celery/HTTP/WS', twoUsers: true, samePrivatePair: true,
    sendEditDeleteLive: true, versionConflictAndDraft: true, durableFileRetry: true,
    workerBackupPreviewRestore: true, reloadHistory: true, groupDeletionRevokesAccess: true, runtimeErrors };
  } finally { await peerContext.close(); }
}
