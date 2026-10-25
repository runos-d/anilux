async page => {
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
  const userId = await page.evaluate(() => JSON.parse(localStorage.getItem('anilux_user_v1')).id);
  const targets = [
    ['catalog','/anime?section=catalog','.catalog-grid .anime-card,.catalog-grid .franchise-card'],
    ['calendar','/anime?section=calendar','.crc'],
    ['recommendations','/anime?section=recommendations','.reason-btn'],
    ['home','/','.home-page .anime-card'],
    ['feed','/feed','.post-card'],
    ['profile','/profile/'+userId,'.profile-header h1'],
    ['library','/library','.lib-card'],
    ['playlists','/playlists','.playlist-card'],
    ['notifications','/notifications','.notif-row'],
    ['chats','/chats','.chat-list-item'],
  ];
  const samples = [];
  const measure = async (target, kind) => {
    const result = await page.evaluate(async ([label,path,selector]) => {
      const router = document.getElementById('app').__vue_app__.config.globalProperties.$router;
      const start = performance.now();
      const ready = new Promise(resolve => {
        const check = () => {
          const element = document.querySelector(selector);
          if (router.currentRoute.value.fullPath === path && element?.getClientRects().length)
            resolve({ label, ms: Math.round((performance.now()-start)*10)/10, text: element.textContent.trim().slice(0,90) });
          else if (performance.now()-start > 15000) resolve({ label, error:'No actual content within 15 seconds' });
          else requestAnimationFrame(check);
        };
        requestAnimationFrame(check);
      });
      await router.push(path);
      return ready;
    }, target);
    samples.push({ ...result, kind });
  };
  for (const target of targets) await measure(target, 'first_spa');
  for (let round=0;round<5;round++) for (const target of targets) await measure(target, 'repeat_spa');
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', { offline:false, latency:200, downloadThroughput:200000, uploadThroughput:100000 });
  for (let round=0;round<5;round++) for (const target of targets) await measure(target, 'repeat_slow_spa');
  await cdp.send('Network.emulateNetworkConditions', { offline:false, latency:0, downloadThroughput:-1, uploadThroughput:-1 });
  await cdp.detach();
  const report = { samples, errors: [...new Set(errors)] };
  await page.evaluate(report => localStorage.setItem('site_spa_report', JSON.stringify(report)), report);
  return { samples, errors:report.errors };
}
