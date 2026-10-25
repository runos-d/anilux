async page => {
  const origin = 'http://localhost:8080';
  const prefix = 'catalog_feed_browser_20261012_';
  const report = {}, errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const login = async (suffix, headers = {}) => {
    const response = await page.request.post(origin + '/api/users/login/', {
      data: {username: prefix + suffix, password: 'Local-Catalog-Feed-20261012!'},
      headers,
    });
    if (!response.ok()) throw new Error('Fixture login failed ' + response.status());
    return response.json();
  };
  const cachedLogin = await page.evaluate(() => ({user: JSON.parse(localStorage.getItem('anilux_user_v1') || 'null'),
    tokens: {access: localStorage.getItem('anilux_access_token_v1'), refresh: localStorage.getItem('anilux_refresh_token_v1')}}));
  const owner = cachedLogin.user?.username === prefix + 'owner' && cachedLogin.tokens.access ? cachedLogin : await login('owner');
  const reader = await login('reader', {Authorization: 'Bearer ' + owner.tokens.access});
  await page.evaluate(owner => {
    localStorage.setItem('anilux_access_token_v1', owner.tokens.access);
    localStorage.setItem('anilux_refresh_token_v1', owner.tokens.refresh);
    localStorage.setItem('anilux_user_v1', JSON.stringify(owner.user));
  }, owner);
  const headers = {Authorization: 'Bearer ' + owner.tokens.access};
  const grouped = await (await page.request.get(origin + '/api/anime/', {
    params: {search: 'ДжоДжо', group_franchises: 'true', page_size: 50},
  })).json();
  if (grouped.count !== 1 || grouped.results[0].franchise_parts_count !== 12) throw new Error('Catalog did not group JoJo');
  report.catalog = {cards: grouped.count, parts: grouped.results[0].franchise_parts_count};
  const steel = await (await page.request.get(origin + '/api/anime/', {params: {search: 'Стальной шар'}})).json();
  if (steel.results[0].year !== 2026) throw new Error('Wrong release year');
  report.releaseYear = 2026;
  await page.goto(origin + '/');
  await page.evaluate(async ownerId => {
    await new Promise((resolve, reject) => {
      const request = indexedDB.open('anilux-post-drafts', 1);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction('drafts', 'readwrite');
        transaction.objectStore('drafts').delete(`${ownerId}:create`);
        transaction.oncomplete = () => { db.close(); resolve(); };
        transaction.onerror = reject;
      };
      request.onerror = reject;
    });
  }, owner.user.id);
  await page.goto(origin + '/feed');
  const text = prefix + 'post_' + Date.now();
  while (await page.locator('.composer-attachment-remove').count()) await page.locator('.composer-attachment-remove').first().click();
  await page.getByPlaceholder('Что у вас нового?').fill(text);
  await page.getByTitle('Фото или видео').click();
  const root = 'C:/Users/Serezhka/Documents/Projects/Kaiden/Web/Production/animecore/backend/data/local_release/catalog-feed-browser/';
  await page.locator('.attach-modal input[type=file]').setInputFiles([root + 'photo-1.png', root + 'photo-2.png']);
  await page.locator('.attach-modal-btn-confirm').click();
  await page.getByTitle('Прикрепить плейлист').click();
  await page.locator('.attach-modal .playlist-result').filter({hasText: prefix + '1'}).click();
  await page.locator('.attach-modal .playlist-result').filter({hasText: prefix + '2'}).click();
  await page.locator('.attach-modal-btn-confirm').click();
  let sends = 0;
  page.on('request', request => {
    if (request.method() === 'POST' && new URL(request.url()).pathname === '/api/social/posts/') sends++;
  });
  const created = page.waitForResponse(response => response.request().method() === 'POST' &&
    new URL(response.url()).pathname === '/api/social/posts/');
  const start = Date.now();
  await page.getByTitle('Опубликовать', {exact: true}).click({clickCount: 2});
  await page.getByRole('progressbar', {name: 'Прогресс загрузки'}).waitFor({timeout: 10000});
  report.uploadProgressBar = true;
  const response = await created;
  if (!response.ok()) throw new Error('Post creation failed ' + response.status());
  const post = await response.json();
  report.creationRequests = sends;
  report.postId = post.id;
  const card = page.locator('.post-card').filter({hasText: text}).first();
  await card.waitFor({timeout: 15000});
  await card.getByRole('button', {name: /Фотографии · 2/}).click();
  await card.getByRole('button', {name: /Плейлисты · 2/}).click();
  if (await card.locator('.playlist-card').count() !== 2) throw new Error('Duplicated playlists');
  if (await card.locator('.media-gallery img').count() !== 2) throw new Error('Missing or duplicated photos');
  await card.locator('.media-gallery img').first().evaluate(img => new Promise(resolve => {
    if (img.complete && img.naturalWidth) resolve(); else img.addEventListener('load', resolve, {once:true});
  }));
  report.photoPublicationMs = Date.now() - start;
  const detail = await (await page.request.get(origin + '/api/social/posts/' + post.id + '/', {headers})).json();
  report.status = detail.status;
  report.photos = detail.media_files.length;
  report.playlists = await card.locator('.playlist-card').count();
  if (sends !== 1 || detail.status !== 'published') throw new Error('Wrong publication lifecycle');
  await page.goto(origin + '/chats');
  await page.locator('.chat-list .search-input').fill('Стальной шар');
  await page.locator('.chat-list').getByText(prefix + 'discussion', {exact: true}).first().waitFor({timeout: 15000});
  report.discussionSearch = true;
  const readerHeaders = {Authorization: 'Bearer ' + reader.tokens.access};
  const chats = await (await page.request.get(origin + '/api/social/private-chats/', {headers: readerHeaders})).json();
  const chat = (chats.results || chats)[0];
  const messages = await (await page.request.get(origin + '/api/social/chats/' + chat.id + '/messages/', {
    params: {type: 'private'}, headers: readerHeaders,
  })).json();
  const video = messages.results.find(message => message.text === prefix + 'video').attachments[0];
  const url = video.file_url || video.url || video.file;
  const range = await page.request.get(url, {headers: {Range: 'bytes=0-99'}});
  if (range.status() !== 206) throw new Error('Video byte ranges unavailable');
  const cached = await page.request.get(url, {headers: {'If-None-Match': range.headers().etag}});
  if (cached.status() !== 304) throw new Error('Video cache revalidation unavailable');
  report.video = {range: range.status(), revalidation: cached.status(), cache: range.headers()['cache-control']};
  await page.request.delete(origin + '/api/social/posts/' + post.id + '/', {headers});
  if (errors.length) throw new Error(errors.join('; '));
  report.consoleErrors = errors.length;
  return report;
}
