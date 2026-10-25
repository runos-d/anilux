async page => {
  const origin = 'http://localhost:8080';
  const login = await page.context().request.post(origin+'/api/users/login/', {
    data:{ username:'site_browser_20261011_owner', password:'Site-Rebuild-Local-123!' },
  });
  if (!login.ok()) throw new Error('Fixture account is unavailable');
  const account = await login.json();
  const targets = [
    ['catalog','/anime?section=catalog','.catalog-grid .anime-card,.catalog-grid .franchise-card'],
    ['calendar','/anime?section=calendar','.crc'],
    ['recommendations','/anime?section=recommendations','.reason-btn'],
    ['home','/','.home-page .anime-card'], ['feed','/feed','.post-card'],
    ['profile','/profile','.profile-header h1'], ['library','/library','.lib-card'],
    ['playlists','/playlists','.playlist-card'], ['notifications','/notifications','.notif-row'],
    ['chats','/chats','.chat-list-item'],
  ];
  const samples = [], errors = [];
  const kinds = await page.evaluate(() => localStorage.getItem('site_cold_normal_only') ? [false] : [false,true]);
  for (const slow of kinds) for (const [label,path,selector] of targets) {
    const context = await page.context().browser().newContext({ viewport:{ width:1365,height:950 }, serviceWorkers:'block' });
    try {
      await context.addInitScript(({account,selector}) => {
        localStorage.setItem('anilux_access_token_v1', account.tokens.access);
        localStorage.setItem('anilux_refresh_token_v1', account.tokens.refresh);
        localStorage.setItem('anilux_user_v1', JSON.stringify(account.user));
        const check = () => {
          const card = document.querySelector(selector);
          if (card?.getClientRects().length && card.textContent.trim()) window.__siteContentMs = Math.round(performance.now());
          else requestAnimationFrame(check);
        };
        requestAnimationFrame(check);
      }, {account,selector});
      const cold = await context.newPage();
      cold.on('pageerror', error => errors.push({label,slow,message:error.message}));
      cold.on('console', message => { if (message.type()==='error') errors.push({label,slow,message:message.text().slice(0,240)}); });
      if (slow) {
        const cdp = await context.newCDPSession(cold);
        await cdp.send('Network.enable');
        await cdp.send('Network.emulateNetworkConditions', { offline:false,latency:200,downloadThroughput:200000,uploadThroughput:100000 });
      }
      await cold.goto(origin+path, { waitUntil:'domcontentloaded' });
      await cold.waitForFunction(() => Number.isFinite(window.__siteContentMs), null, { timeout:20000 });
      samples.push(await cold.evaluate(({label,slow}) => ({label,kind:slow?'cold_slow':'cold',ms:window.__siteContentMs,
        domReady:Math.round(performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd),
        resources:performance.getEntriesByType('resource').filter(row => row.initiatorType!=='img').map(row => ({path:new URL(row.name).pathname+(new URL(row.name).pathname.startsWith('/api/')?new URL(row.name).search:''), start:Math.round(row.startTime),ms:Math.round(row.duration)})).filter(row => row.path.includes('/api/') || row.ms>100),
      }),{label,slow}));
      await cold.waitForLoadState('networkidle', {timeout:5000}).catch(() => {});
    } catch (error) { samples.push({label,kind:slow?'cold_slow':'cold',error:error.message.slice(0,160)}); }
    finally { await context.close(); }
  }
  const report = {samples,errors};
  await page.evaluate(report => localStorage.setItem('site_cold_report',JSON.stringify(report)),report);
  return report;
}
