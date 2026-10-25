async page => {
  const account = await page.evaluate(() => ({user:JSON.parse(localStorage.getItem('anilux_user_v1')),
    access:localStorage.getItem('anilux_access_token_v1'),refresh:localStorage.getItem('anilux_refresh_token_v1')}));
  if (!account.user?.id) throw new Error('Fixture session required');
  const context = await page.context().browser().newContext({viewport:{width:1365,height:950},serviceWorkers:'block'});
  const targets = [
    ['/anime?section=catalog','.catalog-grid .anime-card,.catalog-grid .franchise-card'],
    ['/anime?section=calendar','.crc'], ['/anime?section=recommendations','.reason-btn'],
    ['/','.home-page .anime-card'], ['/feed','.post-card'], ['/profile/'+account.user.id,'.profile-header h1'],
    ['/library','.lib-card'], ['/playlists','.playlist-card'], ['/notifications','.notif-row'], ['/chats','.chat-list-item'],
  ];
  const errors=[];
  try {
    await context.addInitScript(account => {
      localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));
      localStorage.setItem('anilux_access_token_v1',account.access);
      localStorage.setItem('anilux_refresh_token_v1',account.refresh);
      const sockets=new Set(),intervals=new Set(),NativeSocket=window.WebSocket;
      window.WebSocket=class extends NativeSocket { constructor(...args) { super(...args); sockets.add(this); this.addEventListener('close',()=>sockets.delete(this),{once:true}); } };
      const start=window.setInterval,stop=window.clearInterval;
      window.setInterval=(...args)=>{ const id=start(...args);intervals.add(id);return id; };
      window.clearInterval=id=>{ intervals.delete(id);stop(id); };
      window.__routeResources=()=>({sockets:sockets.size,intervals:intervals.size});
    },account);
    const tab=await context.newPage();tab.on('pageerror',error=>errors.push(error.message));
    await tab.goto('http://localhost:8080/feed');
    const cdp=await context.newCDPSession(tab);
    const samples=[];
    for(let index=0;index<200;index++) {
      const [path,selector]=targets[index%targets.length];
      await tab.evaluate(path=>document.getElementById('app').__vue_app__.config.globalProperties.$router.push(path),path);
      await tab.locator(selector).first().waitFor({timeout:15000});
      if(index===19||index===199) {
        await cdp.send('HeapProfiler.collectGarbage');
        samples.push(await tab.evaluate(transitions=>({transitions,...window.__routeResources(),heapMB:Math.round(performance.memory.usedJSHeapSize/1048576)}),index+1));
      }
    }
    const hiddenReads=[];
    tab.on('request',request=> {
      const url=new URL(request.url());
      if(url.pathname==='/api/anime/' && url.searchParams.get('search')==='site_hidden_section_probe') hiddenReads.push(url.pathname);
    });
    await tab.evaluate(()=>document.getElementById('app').__vue_app__.config.globalProperties.$router.push('/feed?search=site_hidden_section_probe'));
    await tab.locator('.post-card').first().waitFor();
    await tab.waitForTimeout(500);
    if(hiddenReads.length) throw new Error('Invisible catalog fetched a foreign route query');
    const report={samples,hiddenCatalogReads:hiddenReads.length,errors};
    await page.evaluate(report=>localStorage.setItem('site_navigation_report',JSON.stringify(report)),report);
    return report;
  } finally { await context.close(); }
}
