async host => {
  const ctx=await host.context().browser().newContext({serviceWorkers:'allow'}),page=await ctx.newPage();
  try {
    await ctx.addInitScript(()=>{window.__controllerChanges=[];navigator.serviceWorker.addEventListener('controllerchange',()=>window.__controllerChanges.push({time:performance.now(),state:navigator.serviceWorker.controller?.state}));});
    await page.goto('http://localhost:8089/app');
    await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
    const before=await page.evaluate(()=>({time:performance.timeOrigin,build:document.querySelector('.app-build')?.textContent,navigation:performance.getEntriesByType('navigation')[0]?.type}));
    if(before.navigation!=='navigate')throw Error('Client was not started cold');
    await ctx.request.get('http://localhost:8089/__acceptance_update');
    await page.evaluate(async()=>{await Promise.race([(await navigator.serviceWorker.getRegistration()).update(),new Promise((_,reject)=>setTimeout(()=>reject(new Error('Worker update check timed out')),10000))]);});
    await page.locator('.pwa-update-toast').waitFor();
    await Promise.all([page.waitForEvent('load'),page.locator('.pwa-update-btn').click()]);
    await page.waitForFunction(()=>performance.getEntriesByType('navigation')[0]?.type==='reload');
    const after=await page.evaluate(async()=>({time:performance.timeOrigin,waiting:!!(await navigator.serviceWorker.getRegistration()).waiting,build:document.querySelector('.app-build')?.textContent}));
    if(after.time<=before.time||after.waiting)throw Error('Cold client failed to reload');
    await ctx.setOffline(true);await page.goto('http://localhost:8089/app?cold-update-offline=1');
    await page.getByRole('heading',{name:'Приложение AniLux',exact:true}).waitFor();
    await page.locator('.offline-banner').waitFor();
    return {passed:true,coldClient:true,controllerUpdateReloaded:true,offlineAfterUpdate:true,before,after};
  } catch(error){return {passed:false,error:error.message,state:await page.evaluate(async()=>{const reg=await navigator.serviceWorker.getRegistration();return {waiting:reg?.waiting?.state,active:reg?.active?.state,changes:window.__controllerChanges,error:document.querySelector('.app-error')?.textContent,toast:document.querySelector('.pwa-update-toast')?.textContent,build:document.querySelector('.app-build')?.textContent};})};}
  finally {await ctx.setOffline(false);await ctx.close();}
}
