async page => {
  const origin = new URL(page.url()).origin;
  if (origin !== 'http://localhost:8080') throw new Error('Local release only');
  const legacyApi = origin + '/api/social/chats/cache-test/';
  const legacyMedia = origin + '/media/attachments/cache-test.jpg';
  await page.evaluate(async ({ legacyApi, legacyMedia }) => {
    for (const name of await caches.keys()) {
      for (const request of await (await caches.open(name)).keys()) {
        if ([legacyApi, legacyMedia].includes(request.url)) continue; // Left by an interrupted probe.
        const path = new URL(request.url).pathname;
        if (path.startsWith('/api/') || /^\/(?:data\/)?media\/(attachments|message_media|scheduled_messages|chat_backups)\//.test(path)) {
          throw new Error('Private response remained cached: ' + path);
        }
      }
    }
    await (await caches.open('api-cache')).put(legacyApi, new Response('old private API'));
    await (await caches.open('images-cache')).put(legacyMedia, new Response('old private image'));
    const previous = await navigator.serviceWorker.getRegistration();
    if (previous) await previous.unregister();
    await navigator.serviceWorker.register('/sw.js?cache-check=' + Date.now());
  }, { legacyApi, legacyMedia });
  await page.waitForFunction(async ({ legacyApi, legacyMedia }) =>
    !(await caches.keys()).includes('api-cache') && !(await caches.match(legacyMedia)) && !(await caches.match(legacyApi)),
  { legacyApi, legacyMedia }, { timeout: 30000 });
  const admin = 'http://localhost:8000/admin/login/';
  const login = await page.request.get(admin);
  const html = await login.text();
  const csrf = /name="csrfmiddlewaretoken" value="([^"]+)"/.exec(html)?.[1];
  if (!csrf) throw new Error('Admin CSRF token missing');
  const rejectedLogin = await page.request.post(admin, {
    headers: { Origin: origin, Referer: origin + '/admin/login/' },
    form: { username: 'nonexistent_local_csrf_check', password: 'invalid', csrfmiddlewaretoken: csrf, next: '/admin/' },
  });
  if (rejectedLogin.status() !== 200 || !(await rejectedLogin.text()).includes('errornote')) {
    throw new Error('Admin POST failed CSRF/origin instead of rejecting credentials');
  }
  return { privateResponsesNotCached: true, legacyPrivateCacheRemoved: true, backendAdminCsrfForFrontendOrigin: true };
}
