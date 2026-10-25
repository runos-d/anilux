async page => {
  const origin='http://localhost:5187',cdp=await page.context().newCDPSession(page);await cdp.send('Network.enable');const offline=async value=>{await page.context().setOffline(value);await cdp.send('Network.emulateNetworkConditions',{offline:value,latency:0,downloadThroughput:-1,uploadThroughput:-1});};await offline(false);
  try {
  await page.evaluate(async()=>{const cache=await caches.open('api-cache');await cache.put('/api/private-fixture',new Response('legacy-private-fixture'));});
  const before=await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();await r.update();return {controller:navigator.serviceWorker.controller?.scriptURL};});
  await page.locator('.pwa-update-toast').waitFor({timeout:30000});
  const waiting=await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();return r.waiting?.state;});
  if(waiting!=='installed')throw Error('Worker did not wait for confirmation');
  await offline(true);await page.waitForTimeout(150);
  if(!await page.locator('.pwa-update-btn').isDisabled())throw Error('Update enabled offline');
  await offline(false);
  await Promise.all([page.waitForEvent('load'),page.locator('.pwa-update-btn').click()]);
  await page.goto(origin+'/app');await page.locator('.app-build').waitFor();
  const after=await page.evaluate(async()=>{const r=await navigator.serviceWorker.getRegistration();return {active:r.active?.state,waiting:r.waiting?.state,legacyCache:(await caches.keys()).includes('api-cache'),build:document.querySelector('.app-build')?.textContent};});
  if(after.waiting||after.legacyCache||after.active!=='activated')throw Error('Upgrade not completed');
  await offline(true);await page.goto(origin+'/app?after-update-offline=1');await page.locator('.app-build').waitFor();await page.locator('.offline-banner').waitFor();
  await page.screenshot({path:'backend/data/local_release/ui-review/pwa-after-update-offline.png'});await offline(false);
  return {passed:true,before,after,offlineAfterUpdate:true};
  } finally {await offline(false);await cdp.detach();}
}
