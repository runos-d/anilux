async page => {
  const origin = 'http://localhost:8080';
  const report = {}, errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const ownerLogin = await page.request.post(origin+'/api/users/login/', { data:{ username:'site_browser_20261011_owner',password:'Site-Rebuild-Local-123!' } });
  const owner = await ownerLogin.json();
  await page.evaluate(owner => {
    localStorage.setItem('anilux_access_token_v1',owner.tokens.access);
    localStorage.setItem('anilux_refresh_token_v1',owner.tokens.refresh);
    localStorage.setItem('anilux_user_v1',JSON.stringify(owner.user));
  },owner);
  const ownerToken = await page.evaluate(() => localStorage.getItem('anilux_access_token_v1'));
  const readerLogin = await page.request.post(origin+'/api/users/login/', { data:{ username:'site_browser_20261011_reader',password:'Site-Rebuild-Local-123!' } });
  const reader = await readerLogin.json();
  const auth = { Authorization:'Bearer '+ownerToken };
  const browserFixtures = await page.evaluate(() => JSON.parse(localStorage.getItem('site_browser_fixture_ids')));
  if (!browserFixtures?.private_post) throw new Error('Prepare owned browser fixture metadata first');
  const text = 'site_browser_20261011_UI_'+Date.now();
  await page.goto(origin+'/feed');
  await page.waitForLoadState('networkidle',{timeout:15000}).catch(() => {});
  while (await page.locator('.composer-attachment-remove').count()) await page.locator('.composer-attachment-remove').first().click();
  const input = page.getByPlaceholder('Что у вас нового?');
  await input.fill(text);
  await page.waitForTimeout(400);
  await page.reload();
  await input.waitFor();
  if (await input.inputValue() !== text) throw new Error('Draft was not restored');
  report.draftRestored = true;
  await page.getByTitle('Фото или видео').click();
  await page.locator('.attach-modal input[type=file]').setInputFiles('C:/Users/Serezhka/Documents/Projects/Kaiden/Web/Production/animecore/backend/data/local_release/site-ui-photo.png');
  await page.locator('.attach-modal-btn-confirm').click();
  let sends = 0;
  const countSend = request => { if (request.method()==='POST' && new URL(request.url()).pathname==='/api/social/posts/') sends++; };
  page.on('request',countSend);
  const published = page.waitForResponse(response => response.request().method()==='POST' && new URL(response.url()).pathname==='/api/social/posts/');
  await page.getByTitle('Опубликовать', { exact:true }).click({ clickCount:2 });
  const created = await (await published).json();
  const post = created.post || created;
  report.postId = post.id;
  const card = page.locator('.post-card').filter({ hasText:text }).first();
  const started = Date.now();
  await card.waitFor({ timeout:15000 });
  const image = card.locator('img[src*="/api/social/post-media/"]').first();
  await image.waitFor({ timeout:15000 });
  await image.evaluate(img => new Promise(resolve => { if (img.complete && img.naturalWidth) resolve(); else img.addEventListener('load',resolve,{once:true}); }));
  report.photoVisibleWithoutReloadMs = Date.now()-started;
  report.publicationRequests = sends;
  if (sends !== 1) throw new Error('Duplicate post submission');
  page.off('request',countSend);
  await card.locator('.action-btn').nth(2).click();
  const comment = page.locator('.comment-section__textarea').first();
  await comment.fill(text+'_comment'); await comment.press('Enter');
  await page.getByText(text+'_comment',{ exact:true }).waitFor();
  if (await page.locator('.comments-modal__close').count()) await page.locator('.comments-modal__close').click();
  await card.locator('.menu-btn').click();
  await page.locator('.post-menu').getByRole('button',{ name:'Редактировать',exact:true }).click();
  await page.getByPlaceholder('Текст поста...').fill(text+'_edited');
  const edited = page.waitForResponse(response => response.request().method()==='PUT' && response.url().includes('/posts/'+post.id+'/edit/'));
  await page.locator('.edit-post-modal').getByRole('button',{ name:'Сохранить',exact:true }).click();
  if (!(await edited).ok()) throw new Error('UI edit failed');
  await page.locator('.post-card').filter({ hasText:text+'_edited' }).first().waitFor();
  const fresh = await (await page.request.get(origin+'/api/social/posts/'+post.id+'/', {headers:auth})).json();
  report.edited = fresh.text === text+'_edited';
  report.likes = fresh.likes_count; report.comments = fresh.comments_count;
  report.retainedImage = fresh.media_files.length === 1;
  const peerContext = await page.context().browser().newContext({viewport:{width:1365,height:950}});
  try {
    await peerContext.addInitScript(reader => {
      localStorage.setItem('anilux_access_token_v1',reader.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1',reader.tokens.refresh);
      localStorage.setItem('anilux_user_v1',JSON.stringify(reader.user));
    },reader);
    const peer = await peerContext.newPage();
    const revoked = [];
    peer.on('websocket', ws => ws.on('framereceived', frame => {
      try { const data = JSON.parse(frame.payload.toString()); if (String(data.data?.post_id)===String(post.id) && (data.action||data.type)==='post_updated') revoked.push('post_updated'); } catch {}
    }));
    await peer.goto(origin+'/post/'+post.id);
    await peer.locator('.post-card').filter({hasText:text+'_edited'}).waitFor();
    const liked = peer.waitForResponse(response => response.url().includes('/posts/'+post.id+'/like/') && response.request().method()==='POST');
    await peer.locator('.post-card .action-btn').nth(0).click();
    if (!(await liked).ok()) throw new Error('Reader reaction failed');
    report.likes = (await (await page.request.get(origin+'/api/social/posts/'+post.id+'/',{headers:auth})).json()).likes_count;
    const peerAuth = { Authorization:'Bearer '+reader.tokens.access };
    const peerPost = await (await peer.request.get(origin+'/api/social/posts/'+post.id+'/',{headers:peerAuth})).json();
    const signedUrl = peerPost.media_files[0].url;
    report.peerMediaBefore = (await peer.request.get(signedUrl)).status();
    report.privatePostDenied = (await peer.request.get(origin+'/api/social/posts/'+browserFixtures.private_post+'/',{headers:peerAuth})).status();
    await peer.waitForTimeout(2000);
    const change = await page.request.patch(origin+'/api/social/posts/'+post.id+'/',{headers:auth,data:{visibility:'private',version:fresh.version,client_edit_id:text+'_privacy'}});
    if (!change.ok()) throw new Error('Privacy edit failed: '+change.status());
    await peer.locator('.post-card').filter({hasText:text+'_edited'}).waitFor({state:'detached',timeout:15000});
    report.revokedCardRemoved = true; report.revocationEvents = revoked.length;
    report.peerMediaAfter = (await peer.request.get(signedUrl)).status();
    report.peerPostAfter = (await peer.request.get(origin+'/api/social/posts/'+post.id+'/',{headers:peerAuth})).status();
    report.privateMediaInPWACache = await page.evaluate(async () => {
      for(const name of await caches.keys()) for(const request of await (await caches.open(name)).keys())
        if (new URL(request.url).pathname.includes('/social/post-media/')) return true;
      return false;
    });
  } finally { await peerContext.close(); }
  await input.fill(text+'_owner_draft'); await page.waitForTimeout(400);
  await page.evaluate(async () => {
    const auth = document.getElementById('app').__vue_app__.config.globalProperties.$pinia._s.get('auth');
    const login = await auth.login('site_browser_20261011_reader','Site-Rebuild-Local-123!');
    if (login.success===false) throw new Error('Account switch failed');
  });
  await page.goto(origin+'/feed');
  await input.waitFor();
  report.draftIsolatedAfterSwitch = (await input.inputValue())==='';
  report.privatePostAbsentAfterSwitch = (await page.locator('.post-card').filter({hasText:text+'_edited'}).count())===0;
  await page.evaluate(async () => {
    const auth = document.getElementById('app').__vue_app__.config.globalProperties.$pinia._s.get('auth');
    await auth.login('site_browser_20261011_owner','Site-Rebuild-Local-123!');
  });
  await page.goto(origin+'/feed');
  await input.waitFor();
  await page.waitForFunction(text => document.querySelector('.composer-field')?.value===text, text+'_owner_draft');
  report.ownerDraftRestoredAfterDirectSwitch = true;
  report.errors = errors;
  await page.evaluate(report => localStorage.setItem('site_post_ui_report',JSON.stringify(report)),report);
  return report;
}
