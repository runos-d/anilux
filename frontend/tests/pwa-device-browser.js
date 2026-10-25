async host => {
  const accounts=__ACCOUNTS__,browser=host.context().browser(),edge=__PHASE__==='edge',title=edge?'PWA проверка доставки Edge':'PWA проверка доставки';
  const context=await browser.browserType().launchPersistentContext('C:/Users/Serezhka/Documents/Projects/Kaiden/Web/Production/animecore/backend/data/local_release/ui-review/'+(edge?'pwa-edge-profile':'pwa-device-profile'),{
    channel:edge?'msedge':'chrome',headless:true,ignoreDefaultArgs:['--disable-background-networking'],viewport:{width:390,height:844},permissions:['notifications'],
  });
  const result={errors:[]};
  try {
    await context.addInitScript(account=>{if(!['http://localhost:5186','http://localhost:5187'].includes(location.origin))return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},accounts.reader);
    const page=await context.newPage();page.on('pageerror',e=>result.errors.push(e.message));
    await page.goto('http://localhost:5187/app');await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
    const cdp=await context.newCDPSession(page);await cdp.send('Page.enable');
    const m=await cdp.send('Page.getAppManifest');result.manifestErrors=m.errors;result.installabilityErrors=(await cdp.send('Page.getInstallabilityErrors')).installabilityErrors;
    result.nativeInstallButton=await page.getByRole('button',{name:'Установить приложение',exact:true}).count();
    await page.waitForTimeout(500);if(await page.getByRole('button',{name:'Включить уведомления',exact:true}).count())await page.getByRole('button',{name:'Включить уведомления',exact:true}).click();
    await page.waitForFunction(()=>!!document.querySelector('.app-error')||[...document.querySelectorAll('button')].some(b=>b.textContent.includes('Выключить на этом устройстве')),{},{timeout:30000});
    result.pushError=await page.locator('.app-error').textContent().catch(()=>null);
    result.pushSubscribed=Boolean(await page.evaluate(async()=>!!(await navigator.serviceWorker.getRegistration())?.pushManager&&!!await (await navigator.serviceWorker.getRegistration()).pushManager.getSubscription()));
    if(result.pushSubscribed){
      await page.screenshot({path:'backend/data/local_release/ui-review/'+(edge?'pwa-push-ui-edge.png':'pwa-push-ui.png')});
      await page.close();
      const inspector=await context.newPage();await inspector.goto('http://localhost:5187/api/notifications/push/config/');
      result.applicationScriptsClosed=await inspector.evaluate(()=>!document.querySelector('#app')&&document.scripts.length===0);
      if(!result.applicationScriptsClosed)throw Error('Inspector unexpectedly loaded application scripts');
      await inspector.screenshot({path:'backend/data/local_release/ui-review/'+(edge?'pwa-push-live-ready-edge.png':'pwa-push-live-ready.png')});
      let received=false;
      const deadline=Date.now()+45000;
      while(Date.now()<deadline){
        received=await inspector.evaluate(async title=>{const reg=await navigator.serviceWorker.getRegistration();return (await reg.getNotifications()).some(n=>n.title===title);},title);
        if(received)break;
        await inspector.waitForTimeout(500);
      }
      if(!received)throw Error('Background push was not received in 45 seconds');
      result.backgroundPushReceived=true;
      await inspector.evaluate(async()=>{for(const n of await (await navigator.serviceWorker.getRegistration()).getNotifications())n.close();});
      await inspector.goto('http://localhost:5187/app');await inspector.getByRole('button',{name:'Выключить на этом устройстве',exact:true}).click();await inspector.getByRole('button',{name:'Включить уведомления',exact:true}).waitFor();result.subscriptionRemoved=true;
    }
    return result;
  } catch(e){return {...result,error:e.message};}
  finally {await context.close();}
}
