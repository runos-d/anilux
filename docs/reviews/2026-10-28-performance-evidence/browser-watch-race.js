const p = await page.context().newPage();
await installVisualSession(p, 'dark');
const errors = []; p.on('pageerror', error => errors.push(error.message));
let started = false, left = false; const lateCalls = [];
p.on('request', request => { if (left && request.url().includes('/api/anime/1/')) lateCalls.push(request.url()); });
await p.route('**/api/anime/1/kodik_translations/', async route => {
  started = true; await new Promise(resolve => setTimeout(resolve, 1800));
  await route.fulfill({status:200, contentType:'application/json', body:JSON.stringify({translations:[]})}).catch(() => {});
});
await p.goto('http://127.0.0.1:4398/anime?section=catalog');
await p.waitForTimeout(1200);
await p.evaluate(() => document.querySelector('#app').__vue_app__.config.globalProperties.$router.push('/anime/1-fioletovyy-sad/watch?episode=5'));
for (let i=0; i<100 && !started; i++) await p.waitForTimeout(100);
if (!started) throw new Error('Delayed request was not reached');
await p.evaluate(() => document.querySelector('#app').__vue_app__.config.globalProperties.$router.push('/anime?section=catalog'));
left = true; await p.waitForTimeout(2300);
const result = { path: new URL(p.url()).pathname, stalePlayerFrames: await p.locator('iframe').count(), lateCalls, errors };
await p.close(); return result;
