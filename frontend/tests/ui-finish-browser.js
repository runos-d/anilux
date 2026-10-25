async host => {
  const accounts=__ACCOUNTS__,ids=__IDS__,origin='http://localhost:5186',browser=host.context().browser();
  const rows=[],failures=[],errors=[],requests=[],contexts=[];let page,photoPost;
  const role=async name=>{
    const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,serviceWorkers:'block',reducedMotion:'reduce',permissions:['clipboard-read','clipboard-write']});contexts.push(context);
    await context.addInitScript(account=>{localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},accounts[name]);
    page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push({role:name,error:e.stack}));page.on('response',r=>{if(r.status()>=400&&r.url().includes('/api/'))requests.push({status:r.status(),url:r.url()});});
  };
  const goto=async path=>{await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.waitForTimeout(800);for(const button of await page.locator('.notification-toast-close').all())await button.click().catch(()=>{});};
  const capture=async name=>{
    for(const width of [320,390,768,1280,1920]){
      await page.setViewportSize({width,height:844});await page.waitForTimeout(100);
      const state=await page.evaluate(()=>{
        const visible=el=>{const r=el.getBoundingClientRect();return r.width&&r.height&&getComputedStyle(el).visibility!=='hidden';};
        const components=new Set();for(const el of document.querySelectorAll('*')){if(!visible(el))continue;for(let c=el.__vueParentComponent;c;c=c.parent)if(c.type?.__file)components.add(c.type.__file);}
        const symbols=[...document.querySelectorAll('button,label,h1,h2,h3')].filter(visible).filter(el=>/[\p{Extended_Pictographic}★☆×✕✓✔▶←→⋯›‹▼▲]/u.test(el.textContent||'')).filter(el=>!el.closest('.emoji-picker,.reaction-row,.message-reactions')).map(el=>({class:el.className,text:el.textContent.trim().slice(0,80)}));
        return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,components:[...components],symbols};
      });rows.push({name,...state});await host.evaluate(report=>sessionStorage.setItem('ui-completion',JSON.stringify(report)),{rows,failures,errors,requests});
      await page.screenshot({path:`backend/data/local_release/ui-review/completion-${name}-${width}.png`,fullPage:true,animations:'disabled',timeout:15000});
    }await page.setViewportSize({width:390,height:844});
  };
  const step=async(name,fn)=>{try{await fn();await capture(name);}catch(e){failures.push({name,error:e.message});}};
  try{
    await role('owner');
    await step('blocked-chat-state',async()=>{await goto('/chats/'+ids.chat);await page.locator('.chat-header button[title="Настройки"]').click();await page.locator('.nav-item').filter({hasText:'Безопасность'}).click();await page.getByRole('button',{name:'Разблокировать',exact:true}).waitFor();});
    await step('chat-unblock-persisted',async()=>{await page.getByRole('button',{name:'Разблокировать',exact:true}).click();await goto('/chats/'+ids.chat);await page.locator('.message-textarea:not([disabled])').waitFor();await page.locator('.chat-system-message').first().waitFor();});
    await step('franchise-favorite-id',async()=>{await goto('/anime');const response=page.waitForResponse(r=>r.url().includes('/favorites/anime/')&&['POST','DELETE'].includes(r.request().method()));await page.locator('.franchise-card .favorite-btn').first().click();const r=await response;if(!r.ok())throw Error('Favorite '+r.status());const data=r.request().postDataJSON();if(Number(data.anime??data.anime_id)!==ids.anime)throw Error('Wrong anime favorite ID');});
    await step('mobile-search-dropdown',async()=>{await goto('/anime');await page.setViewportSize({width:320,height:844});await page.getByRole('button',{name:'Меню',exact:true}).click();await page.locator('.menu-items input.search-input').fill('Новые');await page.locator('.menu-items .search-suggestions').waitFor();});
    await page.route('**/anime/*/kodik_translations/**',r=>r.fulfill({json:{translations:[{id:1,name:'Проверочная озвучка',kodik_link:'https://kodik.test/serial/ui-review',type:'voice'}]}}));
    await page.route('**/anime/*/kodik_player/**',r=>r.fulfill({json:{kodik_link:'https://kodik.test/serial/ui-review'}}));
    await page.route('https://kodik.test/**',r=>r.fulfill({contentType:'text/html',body:'<html><body style="margin:0;background:#171722;color:white">Изолированный плеер</body></html>'}));
    await step('floating-player-final',async()=>{await goto('/anime/'+ids.animeSlug+'/watch');await page.getByRole('button',{name:'Свернуть в мини-плеер',exact:true}).click();await page.locator('.floating-player').waitFor();});
    await step('floating-player-minimized-final',async()=>{await page.locator('.floating-player button[title*="Свернуть"]').first().click();});
    await step('toast-action-final',async()=>{await goto('/anime');await page.evaluate(async()=>{const{useToast}=await import('/src/composables/useToast.ts');useToast().warning('Проверочная длинная подсказка. '.repeat(18),{title:'Проверочное уведомление',duration:60000,action:{label:'Закрыть подсказку',handler:()=>{sessionStorage.setItem('ui-toast-action','executed');}}});});await page.locator('.toast-action').waitFor();});
    await step('toast-action-click',async()=>{await page.locator('.toast-action').click();if(await page.evaluate(()=>sessionStorage.getItem('ui-toast-action'))!=='executed')throw Error('Toast action not run');});
    await role('admin');await page.route('**/api/anime/admin/franchises/**',r=>r.fulfill({json:{results:[],count:0}}));
    await step('base-modal-franchise-form',async()=>{await goto('/admin/franchises');await page.getByRole('button',{name:'Новая франшиза',exact:true}).click();await page.getByRole('dialog',{name:'Новая франшиза',exact:true}).waitFor();});
    await step('base-modal-close',async()=>{await page.keyboard.press('Escape');await page.getByRole('dialog',{name:'Новая франшиза',exact:true}).waitFor({state:'hidden'});});
    return {rows,failures,errors,requests};
  }finally{for(const context of contexts)await context.close();}
}
