async page => {
  const rows=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
  const ctx=page.context(),origin='http://localhost:5187',cdp=await ctx.newCDPSession(page);await cdp.send('Network.enable');const offline=async value=>{await ctx.setOffline(value);await cdp.send('Network.emulateNetworkConditions',{offline:value,latency:0,downloadThroughput:-1,uploadThroughput:-1});};
  try {
  const capture=async name=>{for(const width of [320,390,768,1280,1920]){await page.setViewportSize({width,height:844});await page.waitForTimeout(350);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow)throw Error('Overflow '+name+' '+width);await page.screenshot({path:'backend/data/local_release/ui-review/pwa-'+name+'-'+width+'.png'});rows.push({name,width,overflow});}};
  await offline(false);await page.goto(origin+'/app');await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
  await capture('online');
  const manifest=await page.evaluate(async()=>{const links=[...document.querySelectorAll('link[rel=manifest]')];const m=await fetch(links[0].href).then(r=>r.json());const icons=[];for(const icon of m.icons){const image=new Image();image.src=icon.src;await image.decode();icons.push({size:icon.sizes,actual:image.naturalWidth+'x'+image.naturalHeight,purpose:icon.purpose});}return {count:links.length,id:m.id,start:m.start_url,display:m.display,scope:m.scope,icons};});
  if(manifest.count!==1||manifest.icons.some(x=>x.size!==x.actual))throw Error('Invalid manifest/icons');
  await page.evaluate(()=>{const event=new Event('beforeinstallprompt',{cancelable:true});event.prompt=async()=>{window.__installPrompted=true;};event.userChoice=Promise.resolve({outcome:'accepted'});window.dispatchEvent(event);});
  await page.getByRole('button',{name:'Установить приложение',exact:true}).click();
  if(!await page.evaluate(()=>window.__installPrompted))throw Error('Install prompt not invoked');
  await page.evaluate(()=>window.dispatchEvent(new Event('appinstalled')));await page.getByRole('heading',{name:'Приложение установлено',exact:true}).waitFor();await capture('installed');
  await page.goto(origin+'/anime?section=catalog');await page.locator('.catalog-grid .anime-card, .catalog-grid .franchise-card').first().waitFor({timeout:20000});
  await page.waitForTimeout(500);
  const before=await page.locator('.catalog-grid .anime-card, .catalog-grid .franchise-card').count();
  await offline(true);await page.goto(origin+'/app?offline-unvisited=1');await page.getByRole('heading',{name:'Приложение AniLux',exact:true}).waitFor();await page.locator('.offline-banner').waitFor();await capture('offline-deep-link');
  await page.goto(origin+'/anime?section=catalog');await page.locator('.catalog-grid .anime-card, .catalog-grid .franchise-card').first().waitFor();
  const after=await page.locator('.catalog-grid .anime-card, .catalog-grid .franchise-card').count();if(before!==after)throw Error('Offline cache changed');await capture('offline-catalog');
  await offline(false);await page.goto(origin+'/app');
  const cachedPrivate=await page.evaluate(async()=>{const found=[];for(const name of await caches.keys()){for(const request of await (await caches.open(name)).keys()){const path=new URL(request.url).pathname;if(path.startsWith('/api/')||/media\/(posts|attachments|message_media)/.test(path))found.push({name,path});}}return found;});
  if(cachedPrivate.length)throw Error('Private responses cached');
  return {passed:!errors.length,samples:rows.length,rows,errors,manifest,catalogCards:after,cachedPrivate};
  } finally {await offline(false);await cdp.detach();}
}
