async host => {
  const context=await host.context().browser().newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
  const page=await context.newPage(),rows=[],errors=[],origin='http://127.0.0.1:8080';page.on('pageerror',error=>errors.push(error.message));
  try {
    for(const path of ['/','/anime?section=catalog','/anime?section=ongoings','/register','/app']) {
      await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.waitForTimeout(1700);
      if(path.includes('catalog'))await page.locator('.catalog-grid .anime-card').first().waitFor();
      if(path==='/register')await page.getByRole('button',{name:'Продолжить с Google',exact:true}).waitFor();
      for(const width of[320,390,768,1280,1920]) {
        await page.setViewportSize({width,height:width<768?844:960});await page.waitForTimeout(450);
        const state=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,clipped:[...document.querySelectorAll('button')].filter(el=>{const r=el.getBoundingClientRect();return r.width&&r.height&&el.scrollWidth>el.clientWidth+2&&getComputedStyle(el).textOverflow!=='ellipsis';}).map(el=>el.className)}));
        if(state.scrollWidth>width+1||state.clipped.length)throw Error('Production layout: '+path+' '+width);
        rows.push({path,...state});
        if(width===390)await page.screenshot({path:'backend/data/local_release/ui-review/live-alignment-'+path.replace(/[^a-z]/g,'_')+'.png',animations:'disabled'});
      }
      await page.setViewportSize({width:390,height:844});
    }
    const pwa=await page.evaluate(async()=>{const reg=await navigator.serviceWorker.ready;return{active:reg.active?.state,script:new URL(reg.active.scriptURL).pathname,controlled:!!navigator.serviceWorker.controller};});
    return{rows,errors,pwa};
  } finally {await context.close();}
}
