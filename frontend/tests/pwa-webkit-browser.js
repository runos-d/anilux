async page => {
  const origin='http://localhost:8080', ctx=page.context(), errors=[], samples=[];
  page.on('pageerror', error=>errors.push(error.message));
  const check=async name=>{
    const sizes=[[320,844],[390,844],[402,874],[768,1024],[844,390]];
    for(const [width,height] of sizes){
      await page.setViewportSize({width,height});await page.waitForTimeout(350);
      await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth+1,{},{timeout:3000});
      const state=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,touch:matchMedia('(pointer: coarse)').matches}));
      if(state.overflow||!state.touch)throw Error('Mobile layout '+name+' '+width);
      samples.push({name,width,height,...state});
    }
  };
  try {
    await ctx.setOffline(false);await page.goto(origin+'/app');
    await page.waitForFunction(()=>!!navigator.serviceWorker.controller);
    if(!await page.getByText('iPhone и iPad: Safari', {exact:false}).count())throw Error('Safari installation instructions missing');
    await check('application');
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('button',{name:'Меню',exact:true}).tap();
    await page.locator('.mobile-menu').waitFor();
    await page.locator('.mobile-menu').getByRole('link',{name:'Приложение',exact:true}).tap();
    await page.locator('.mobile-menu').waitFor({state:'hidden'});
    await page.goto(origin+'/anime?section=catalog');
    const cards=page.locator('.catalog-grid .anime-card, .catalog-grid .franchise-card');
    await cards.first().waitFor();await page.waitForTimeout(500);
    const before=await cards.count();await check('catalog');
    await ctx.setOffline(true);await page.goto(origin+'/app?webkit-offline=1');
    await page.getByRole('heading',{name:'Приложение AniLux',exact:true}).waitFor();
    await page.locator('.offline-banner').waitFor();await check('offline-application');
    await page.goto(origin+'/anime?section=catalog');await cards.first().waitFor();
    if(await cards.count()!==before)throw Error('Offline catalog differs');
    await check('offline-catalog');
    await ctx.setOffline(false);
    return {passed:errors.length===0,engine:'WebKit',mobileEmulation:true,samples:samples.length,rows:samples,catalogCards:before,touchMenu:true,offline:true,errors};
  } finally {await ctx.setOffline(false);}
}
