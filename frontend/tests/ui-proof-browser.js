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
        const components=new Set(),seenNodes=new Set();
        const visit=v=>{if(!v||seenNodes.has(v))return false;seenNodes.add(v);let shown=v.el instanceof Element&&visible(v.el);if(v.component){const child=visit(v.component.subTree);if(child&&v.component.type?.__file)components.add(v.component.type.__file);shown=shown||child;}if(Array.isArray(v.children))for(const child of v.children)shown=visit(child)||shown;return shown;};visit(document.querySelector('#app').__vue_app__._instance.subTree);
        const symbols=[...document.querySelectorAll('button,label,h1,h2,h3')].filter(visible).filter(el=>/[\p{Extended_Pictographic}★☆×✕✓✔▶←→⋯›‹▼▲]/u.test(el.textContent||'')).filter(el=>!el.closest('.emoji-picker,.reaction-row,.message-reactions')).map(el=>({class:el.className,text:el.textContent.trim().slice(0,80)}));
        return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,components:[...components],symbols};
      });rows.push({name,...state});await host.evaluate(report=>sessionStorage.setItem('ui-completion',JSON.stringify(report)),{rows,failures,errors,requests});
      await page.screenshot({path:`backend/data/local_release/ui-review/completion-${name}-${width}.png`,fullPage:true,animations:'disabled',timeout:15000});
    }await page.setViewportSize({width:390,height:844});
  };
  const step=async(name,fn)=>{try{await fn();await capture(name);}catch(e){failures.push({name,error:e.message});}};
  try{
    await role('owner');
    await step('reminder-open-final',async()=>{await goto('/anime');await page.locator('.franchise-card .reminder-btn').first().click();await page.locator('.reminder-modal').waitFor();});
    await step('library-edit-final',async()=>{await goto('/library');await page.locator('.menu-btn').first().click();await page.getByRole('button',{name:'Редактировать',exact:true}).click();await page.locator('.edit-modal').waitFor();});
    await step('photos-stack-final',async()=>{await goto('/post/'+ids.photoPost);await page.locator('.stack-preview').first().waitFor();});
    await step('photos-expanded-final',async()=>{await page.locator('.stack-preview').first().click();await page.locator('.media-item').first().waitFor();});
    await step('photos-error-fallback',async()=>{const src=await page.locator('.media-item img').first().getAttribute('src');await page.route(src,r=>r.fulfill({status:404,body:''}));await goto('/post/'+ids.photoPost);await page.locator('.stack-preview').first().click();await page.locator('.media-item .image-fallback').first().waitFor();});
    await step('account-settings-final',async()=>{await goto('/settings');});
    await step('donate-final',async()=>{await goto('/donate');});
    await step('ongoing-sort-final',async()=>{await goto('/anime?section=ongoings');});
    return {rows,failures,errors,requests};
  }finally{for(const context of contexts)await context.close();}
}
