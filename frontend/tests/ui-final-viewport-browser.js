async host=>{
  const account=__ACCOUNTS__.admin,ids=__IDS__,browser=host.context().browser();
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block',reducedMotion:'reduce'});
  await context.addInitScript(account=>{localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},account);
  const page=await context.newPage(),rows=[],failures=[],errors=[],requests=[];page.setDefaultTimeout(12000);page.on('pageerror',e=>errors.push({error:e.stack}));page.on('response',r=>{if(r.status()>=400&&r.url().includes('/api/'))requests.push({url:r.url(),status:r.status()});});
  const capture=async name=>{for(const width of [320,390,768,1280,1920]){await page.setViewportSize({width,height:844});await page.waitForTimeout(150);const state=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,symbols:[]}));rows.push({name,...state});await page.screenshot({path:`backend/data/local_release/ui-review/viewport-${name}-${width}.png`,fullPage:true,animations:'disabled',timeout:15000});}};
  try{
    await page.goto('http://localhost:5186/admin',{waitUntil:'domcontentloaded'});await page.locator('.admin-tabs > button').nth(4).click();await page.locator('.am-item').first().click();await page.locator('.am-editor').waitFor();await capture('achievement-editor');
    await page.goto('http://localhost:5186/anime',{waitUntil:'domcontentloaded'});await page.locator('.catalog-grid').waitFor();await capture('catalog-labels');
    await page.setViewportSize({width:1280,height:844});await page.locator('.franchise-card').first().hover();await page.locator('.franchise-card .play-btn').first().click();await page.locator('.franchise-page').waitFor();await capture('franchise-play-entry');
    const mobile=await browser.newContext({viewport:{width:320,height:844},serviceWorkers:'block',reducedMotion:'reduce'});
    await mobile.addInitScript(account=>{localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);
      class VisibleArea extends EventTarget {get width(){return innerWidth;}get height(){return window.__uiKeyboardHeight||innerHeight;}get offsetTop(){return window.__uiKeyboardTop||0;}get offsetLeft(){return 0;}}
      window.__uiVisibleArea=new VisibleArea();Object.defineProperty(window,'visualViewport',{configurable:true,value:window.__uiVisibleArea});
    },account);
    const phone=await mobile.newPage();phone.on('pageerror',e=>errors.push({error:e.stack}));
    await phone.route('**/anime/*/kodik_translations/**',r=>r.fulfill({json:{translations:[{id:1,name:'Проверочная озвучка',kodik_link:'https://kodik.test/serial/ui-review',type:'voice'}]}}));
    await phone.route('**/anime/*/kodik_player/**',r=>r.fulfill({json:{kodik_link:'https://kodik.test/serial/ui-review'}}));
    await phone.route('https://kodik.test/**',r=>r.fulfill({contentType:'text/html',body:'<html><head><meta charset="utf-8"></head><body style="margin:0;background:#171722;color:white">Изолированный плеер</body></html>'}));
    await phone.goto('http://localhost:5186/anime/'+ids.animeSlug+'/watch',{waitUntil:'domcontentloaded'});await phone.getByRole('button',{name:'Свернуть в мини-плеер',exact:true}).click();await phone.locator('.floating-player').waitFor();
    await phone.evaluate(()=>{window.__uiKeyboardHeight=360;window.__uiKeyboardTop=30;window.__uiVisibleArea.dispatchEvent(new Event('resize'));});await phone.waitForTimeout(150);
    const box=await phone.locator('.floating-player').boundingBox();if(box.y<30||box.y+box.height>390||box.x+box.width>320)throw Error('Player escapes visual viewport');
    rows.push({name:'player-keyboard',width:320,scrollWidth:await phone.evaluate(()=>document.documentElement.scrollWidth),symbols:[],box});await phone.screenshot({path:'backend/data/local_release/ui-review/viewport-player-keyboard-320.png',fullPage:true,animations:'disabled'});
    await phone.locator('.fp-header button[title="Закрыть"]').click();await phone.locator('.floating-player').waitFor({state:'hidden'});await mobile.close();
    return {rows,failures,errors,requests};
  }catch(e){failures.push({name:'final-viewport',error:e.message});return {rows,failures,errors,requests};}
  finally{await context.close();}
}
