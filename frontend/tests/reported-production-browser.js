async host => {
  const origin='http://127.0.0.1:8080',rows=[];
  for(const width of [320,390,768,1280,1920]) {
    const mobile=width<768;
    const context=await host.context().browser().newContext({viewport:{width,height:900},isMobile:mobile,hasTouch:mobile});
    const p=await context.newPage();p.setDefaultTimeout(20000);
    await p.goto(origin+'/anime?section=catalog',{waitUntil:'domcontentloaded'});
    const cards=p.locator('.catalog-grid .franchise-card');await cards.first().waitFor();
    const geometry=await p.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    if(geometry.scroll>geometry.width+1)throw Error('Catalog overflow '+width);
    const groups=await cards.count();if(!groups)throw Error('No grouped cards '+width);
    const first=cards.first();if(mobile)await first.tap();else await first.click();
    await p.waitForURL(/\/franchise\//,{waitUntil:'domcontentloaded'});
    let sw;
    for(let attempt=0;attempt<30;attempt++){
      sw=await p.evaluate(async()=>{const r=await navigator.serviceWorker.ready;return {state:r.active?.state,controlled:!!navigator.serviceWorker.controller};});
      if(sw.state==='activated'&&sw.controlled)break;
      await p.waitForTimeout(300);
    }
    if(sw.state!=='activated'||!sw.controlled)throw Error('PWA activation incomplete '+JSON.stringify(sw));
    rows.push({width,groups,overflow:false,franchiseOpensOnFirstClick:true,sw});
    await context.close();
  }
  return {rows};
}
