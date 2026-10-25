async entryPage => {
  const origin = 'http://127.0.0.1:5174';
  const context = await entryPage.context().browser().newContext();
  const page = await context.newPage();
  try {
  const peer = await context.newPage();
  const errors = [];
  for (const tab of [page, peer]) {
    tab.on('pageerror', error => errors.push(error.message));
    await tab.route('**/__outbox_test', route => route.fulfill({ contentType: 'text/html', body: '<html><body>Outbox acceptance</body></html>' }));
    await tab.goto(origin + '/__outbox_test');
  }
  await page.evaluate(() => {
    localStorage.setItem('anilux_access_token_v1', 'isolated-outbox-token');
    localStorage.setItem('anilux_user_v1', JSON.stringify({ id: 771 }));
  });
  for (const tab of [page, peer]) await tab.evaluate(async () => { window.outbox = await import('/src/lib/chatOutbox.ts'); });
  const send = async id => {
    const formData = new FormData();
    formData.append('client_message_id', 'shared-file-command');
    formData.append('media', new File(['durable file bytes'], 'two-tabs.txt', { type: 'text/plain' }));
    await window.outbox.storePendingSend(id, { chatId: 80000001, chatType: 'private', formData, urls: [],
      message: { id, sender_id: 771, client_message_id: 'shared-file-command', text: 'Two tabs', send_status: 'failed' } });
  };
  const rows = () => new Promise((resolve, reject) => {
    const open = indexedDB.open('anilux-chat-outbox', 1);
    open.onerror = () => reject(open.error);
    open.onsuccess = () => {
      const db = open.result, request = db.transaction('sends').objectStore('sends').index('accountId').getAll(771);
      request.onsuccess = () => { resolve(request.result); db.close(); };
      request.onerror = () => { reject(request.error); db.close(); };
    };
  });
  await Promise.all([page.evaluate(send, -771), peer.evaluate(send, -772)]);
  if ((await page.evaluate(rows)).length !== 1) throw new Error('Concurrent same-key writes created duplicate durable rows');
  await page.evaluate(() => window.outbox.finishPendingSend(-771));
  await peer.waitForFunction(() => window.outbox.pendingChatSends.size === 0);
  await page.waitForFunction(async () => {
    const db = await new Promise(resolve => { const r = indexedDB.open('anilux-chat-outbox', 1); r.onsuccess = () => resolve(r.result); });
    const count = await new Promise(resolve => { const r = db.transaction('sends').objectStore('sends').count(); r.onsuccess = () => resolve(r.result); });
    db.close(); return count === 0;
  });
  const background = await context.newPage();
  await background.route('**/__outbox_test', route => route.fulfill({ contentType: 'text/html', body: '<html><body>Delayed IndexedDB</body></html>' }));
  await background.goto(origin + '/__outbox_test');
  await background.evaluate(async () => {
    window.BroadcastChannel = undefined;
    const add = window.addEventListener.bind(window);
    window.addEventListener = (type, ...args) => { if (type !== 'storage') add(type, ...args); };
    const open = indexedDB.open.bind(indexedDB);
    indexedDB.open = (...args) => {
      const request = open(...args);
      request.addEventListener('success', event => {
        event.stopImmediatePropagation();
        window.resumeDatabase = () => request.onsuccess.call(request, event);
      });
      return request;
    };
    window.outbox = await import('/src/lib/chatOutbox.ts');
    const formData = new FormData(); formData.append('client_message_id', 'late-logout');
    window.storeResult = 'pending';
    window.outbox.storePendingSend(-773, { chatId: 80000001, chatType: 'private', formData, urls: [],
      message: { id: -773, sender_id: 771, client_message_id: 'late-logout', text: 'Must not return' } })
      .then(() => { window.storeResult = 'stored'; }, () => { window.storeResult = 'cancelled'; });
  });
  await background.waitForFunction(() => !!window.resumeDatabase);
  await peer.evaluate(() => window.outbox.clearChatOutbox(771));
  await background.evaluate(() => window.resumeDatabase());
  await background.waitForFunction(() => window.storeResult !== 'pending');
  if (await background.evaluate(() => window.storeResult) !== 'cancelled') throw new Error('Logout allowed a late IndexedDB write');
  if (await background.evaluate(() => window.outbox.pendingChatSends.size) !== 0) throw new Error('Cancelled send retained in memory');
  if ((await page.evaluate(rows)).length) throw new Error('Logout resurrected durable queue');
  await peer.evaluate(send, -774);
  const reloaded = await context.newPage();
  await reloaded.route('**/__outbox_test', route => route.fulfill({ contentType: 'text/html', body: '<html><body>Reload</body></html>' }));
  await reloaded.goto(origin + '/__outbox_test');
  const recovered = await reloaded.evaluate(async () => {
    const outbox = await import('/src/lib/chatOutbox.ts'); await outbox.hydrateChatOutbox(771);
    const pending = [...outbox.pendingChatSends.values()][0];
    const file = pending.formData.get('media');
    return { key: pending.message.client_message_id, file: file.name, bytes: await file.text() };
  });
  if (recovered.key !== 'shared-file-command' || recovered.file !== 'two-tabs.txt' || recovered.bytes !== 'durable file bytes') throw new Error('File/key changed after reload');
  await reloaded.evaluate(() => import('/src/lib/chatOutbox.ts').then(outbox => outbox.clearChatOutbox(771)));
  await Promise.all([peer.close(), background.close(), reloaded.close()]);
  if (errors.length) throw new Error(errors.join('; '));
  return { concurrentTabs: true, lateWriteAfterLogoutRejected: true, missedNotificationsCovered: true, fileAndKeyAfterReload: recovered, runtimeErrors: errors };
  } finally { await context.close(); }
}
