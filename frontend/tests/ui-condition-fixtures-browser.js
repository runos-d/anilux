async host => {
  const accounts=__ACCOUNTS__,ids=__IDS__,origin='http://localhost:5186';
  const context=await host.context().browser().newContext({viewport:{width:390,height:844},hasTouch:true,serviceWorkers:'block',reducedMotion:'reduce'});
  await context.addInitScript(account=>{localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},accounts.owner);
  const page=await context.newPage(),rows=[],failures=[],errors=[],requests=[];page.setDefaultTimeout(12000);
  page.on('pageerror',e=>errors.push({url:page.url(),error:e.stack}));page.on('response',r=>{if(r.status()>=400&&r.url().includes('/api/'))requests.push({url:r.url(),status:r.status()});});
  const goto=async path=>{await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.waitForTimeout(800);};
  const capture=async name=>{
    for(const width of [320,390,768,1280,1920]){
      await page.setViewportSize({width,height:844});await page.waitForTimeout(120);
      const state=await page.evaluate(()=>{
        const visible=el=>{const r=el.getBoundingClientRect();return r.width&&r.height&&getComputedStyle(el).visibility!=='hidden';};const components=new Set();
        for(const el of document.querySelectorAll('*')){if(!visible(el))continue;for(let c=el.__vueParentComponent;c;c=c.parent)if(c.type?.__file)components.add(c.type.__file);}
        const symbols=[...document.querySelectorAll('button,label,h1,h2,h3')].filter(visible).filter(el=>/[\p{Extended_Pictographic}★☆×✕✓✔▶←→⋯›‹▼▲]/u.test(el.textContent||'')).filter(el=>!el.closest('.emoji-picker,.reaction-row,.message-reactions')).map(el=>({class:el.className,text:el.textContent.trim().slice(0,80)}));
        return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,components:[...components],symbols};
      });rows.push({name,...state});await host.evaluate(report=>sessionStorage.setItem('ui-fixtures',JSON.stringify(report)),{rows,failures,errors,requests});await page.screenshot({path:`backend/data/local_release/ui-review/fixtures-${name}-${width}.png`,fullPage:true,animations:'disabled',timeout:15000});
    }await page.setViewportSize({width:390,height:844});
  };
  const step=async(name,fn)=>{try{await fn();await capture(name);}catch(e){failures.push({name,error:e.message});}};
  const setComponentState=async(file,values)=>page.evaluate(({file,values})=>{
    const seen=new Set();let found;const visit=vnode=>{if(!vnode||seen.has(vnode))return;seen.add(vnode);const c=vnode.component;if(c){if(c.type?.__file?.replaceAll('\\','/').endsWith('/'+file))found=c;visit(c.subTree);}if(Array.isArray(vnode.children))vnode.children.forEach(visit);};
    const root=document.querySelector('#app').__vue_app__._instance;if(root.type.__file.endsWith(file))found=root;visit(root.subTree);
    if(!found)throw Error('Condition component missing: '+file);for(const[key,value]of Object.entries(values))found.setupState[key]=value;
  },{file,values});
  try{
    let catalogFixture;
    await page.route('**/api/anime/?*',async route=>{const response=await route.fetch();const data=await response.json();if(data.results?.length)catalogFixture=data;await route.fulfill({response,json:{...(catalogFixture||data),count:250,total_pages:5}});});
    await step('pagination',async()=>{await goto('/anime');await page.locator('.catalog-pagination').waitFor();});
    await step('pagination-next',async()=>{await page.getByRole('button',{name:'Следующая страница',exact:true}).click();await page.getByText('Страница 2 из 5',{exact:false}).waitFor();});
    await page.unroute('**/api/anime/?*');
    await step('playlist-select',async()=>{await goto('/anime/'+ids.animeSlug);await page.getByRole('button',{name:'В плейлист',exact:true}).click();await page.locator('.playlist-select-modal').waitFor();});
    await step('playlist-select-checked',async()=>{await page.locator('.playlist-item').first().click();});
    let release;const gate=new Promise(resolve=>release=resolve);
    await page.route('**/api/social/user-achievements/all/**',async route=>{await gate;await route.continue();});
    const loaded=page.waitForResponse(r=>r.url().includes('/social/user-achievements/all/'));
    await step('achievement-loading',async()=>{await goto('/achievements');await page.locator('.loading-spinner').waitFor();});release();await loaded;await page.unrouteAll({behavior:'wait'});
    await page.route('**/api/social/posts/'+ids.post+'/',async route=>{const response=await route.fetch();const original=await response.json();await route.fulfill({response,json:{...original,post_type:'repost',original_post:original}});});
    await step('quote-content',async()=>{await goto('/post/'+ids.post);await page.locator('.quote-card').waitFor();});await page.unroute('**/api/social/posts/'+ids.post+'/');
    await step('toast-long-action',async()=>{await goto('/anime');await page.evaluate(async()=>{const{useToast}=await import('/src/composables/useToast.ts');useToast().warning('Проверочная длинная системная подсказка. '.repeat(18),{title:'Проверочное уведомление',duration:60000,action:{label:'Закрыть подсказку',handler:()=>{}}});});await page.locator('.toast.warning').waitFor();});
    await step('pwa-update-condition',async()=>{await goto('/anime');await setComponentState('PwaUpdateNotification.vue',{needsRefresh:true});await page.locator('.pwa-update-toast').waitFor();});
    await step('pwa-update-close',async()=>{await page.locator('.pwa-update-close').click();await page.locator('.pwa-update-toast').waitFor({state:'hidden'});});
    await step('saved-parallax-condition',async()=>{await setComponentState('App.vue',{parallaxEffect:true,smoothAnimations:true});await page.locator('.parallax-backdrop').waitFor({state:'attached'});});
    return {rows,failures,errors,requests};
  }finally{await context.close();}
}
