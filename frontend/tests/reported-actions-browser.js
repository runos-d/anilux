async host => {
  const accounts=__ACCOUNTS__,origin=__ORIGIN__,checks=[],errors=[];
  for(const context of host.context().browser().contexts()) if(context!==host.context())await context.close();
  for (const mobile of [false,true]) {
    const context=await host.context().browser().newContext({viewport:{width:mobile?390:1440,height:900},isMobile:mobile,hasTouch:mobile,serviceWorkers:'block'});
    await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts.admin,origin});
    const p=await context.newPage();p.setDefaultTimeout(20000);
    p.on('pageerror',e=>errors.push(e.message));
    const hit=async loc=>{if(mobile)await loc.tap();else await loc.click();};
    const check=(name)=>checks.push({mobile,name,passed:true});
    await p.goto(origin+'/admin',{waitUntil:'domcontentloaded'});await p.locator('.admin-tabs > button').first().waitFor();
    const panels=['.overview-grid','.import-section','.franchises-manager','.catalog-manager','.achievements-manager','.complaints-list','.support-panel'];
    for(let i=0;i<7;i++) {
      await hit(p.locator('.admin-tabs > button').nth(i));
      await p.locator('.admin-tabs > button.active').nth(0).waitFor();
      await p.waitForTimeout(600);
      if(!((await p.locator('.admin-tabs > button').nth(i).getAttribute('class')).includes('active')))throw Error('Inactive admin tab '+i);
      if(await p.locator('.cm-card[role=alert], .fm-error').count())throw Error('Admin management unavailable');
      check('admin-tab-'+i);
    }
    await hit(p.locator('.admin-tabs > button').nth(3));
    const toggle=p.locator('.cm-switch');await toggle.waitFor();await p.waitForFunction(()=>!document.querySelector('.cm-switch')?.disabled);
    const original=await toggle.getAttribute('aria-pressed');
    const navigateTo=async path=>{if(mobile){await hit(p.locator('.burger-btn'));await hit(p.locator('#mobile-menu a[href="'+path+'"]'));}else await hit(p.locator('a[href="'+path+'"]').first());};
    const setGrouping=async enabled=>{if(await toggle.getAttribute('aria-pressed')!==String(enabled)){await hit(toggle);await p.waitForFunction(value=>document.querySelector('.cm-switch')?.getAttribute('aria-pressed')===String(value),enabled);} };
    await setGrouping(false);
    await navigateTo('/anime');await p.locator('.catalog-grid .anime-card').first().waitFor();
    await p.waitForFunction(()=>document.querySelectorAll('.catalog-grid .anime-card').length>0&&!document.querySelector('.catalog-grid .franchise-card'));
    check('ungrouped-catalog-after-settings');
    await navigateTo('/admin');await hit(p.locator('.admin-tabs > button').nth(3));await toggle.waitFor();await p.waitForFunction(()=>!document.querySelector('.cm-switch')?.disabled);
    await setGrouping(true);
    await navigateTo('/anime');
    await p.waitForFunction(()=>document.querySelectorAll('.catalog-grid .franchise-card').length>0);
    check('grouped-catalog-after-settings');
    const toggleFilters=p.locator('.afb-btn[title="Фильтры"],.afb-btn[title="Скрыть фильтры"]');
    await hit(toggleFilters);await p.waitForTimeout(150);await hit(toggleFilters);check('filter-toggle-on-first-click');
    for(const index of [1,3,0]){await hit(p.locator('.av-tab').nth(index));await p.waitForFunction(i=>document.querySelectorAll('.av-tab')[i]?.classList.contains('active'),index);check('section-first-click-'+index);}
    await p.locator('.catalog-grid .anime-card').first().waitFor();
    const card=p.locator('.catalog-grid .anime-card:not(.franchise-card)').first();await card.waitFor();
    if(!mobile)await card.hover();
    await hit(card.locator('.play-btn'));
    await p.waitForURL(/\/anime\/[^/]+\/watch/,{waitUntil:'domcontentloaded'}).catch(()=>{throw Error('play click failed at '+p.url()+' '+JSON.stringify(checks));});check('play-opens-on-first-click');
    await p.goto(origin+'/anime?section=catalog',{waitUntil:'domcontentloaded'});await p.locator('.catalog-grid .anime-card').first().waitFor();
    const plain=p.locator('.catalog-grid .anime-card:not(.franchise-card)').first();await plain.scrollIntoViewIfNeeded();const rect=await plain.locator('.anime-poster').boundingBox();
    const point={x:rect.x+rect.width/2,y:rect.y+60};
    const target=await p.evaluate(point=>document.elementFromPoint(point.x,point.y)?.outerHTML.slice(0,250),point);
    if(mobile)await p.touchscreen.tap(point.x,point.y);else await p.mouse.click(point.x,point.y);
    await p.waitForURL(/\/anime\/[^/?]+$/,{waitUntil:'domcontentloaded'}).catch(()=>{throw Error('poster click failed at '+p.url()+' '+JSON.stringify({mobile,rect,target,checks}));});check('poster-opens-on-first-click');
    await p.goto(origin+'/admin',{waitUntil:'domcontentloaded'});await hit(p.locator('.admin-tabs > button').nth(3));await toggle.waitFor();await p.waitForFunction(()=>!document.querySelector('.cm-switch')?.disabled);
    if(await toggle.getAttribute('aria-pressed')!==original)await hit(toggle);
    await context.close();
  }
  return {checks,errors};
}
