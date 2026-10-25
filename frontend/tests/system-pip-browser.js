async host => {
  const accounts=__ACCOUNTS__,browser=host.context().browser(),edge=__PHASE__==='edge',ctx=edge?await browser.browserType().launchPersistentContext('C:/Users/Serezhka/Documents/Projects/Kaiden/Web/Production/animecore/backend/data/local_release/ui-review/pwa-pip-edge-profile',{channel:'msedge',headless:true,viewport:{width:1280,height:900},serviceWorkers:'block'}):await browser.newContext({viewport:{width:1280,height:900},serviceWorkers:'block'});
  await ctx.addInitScript(account=>{if(location.origin!=='http://localhost:5187')return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},accounts.reader);
  const page=await ctx.newPage();page.setDefaultTimeout(20000);const errors=[];page.on('pageerror',e=>errors.push(e.message));ctx.on('page',p=>{if(p!==page)void p.close();});
  try {
    await page.goto('http://localhost:5187/anime/kovboy-bibop');await page.getByRole('button',{name:'Смотреть',exact:true}).click();
    await page.locator('.kodik-iframe').waitFor();await page.waitForTimeout(5000);
    const frame=page.frames().find(f=>f.url().includes('kodikplayer.com'));if(!frame)throw Error('Kodik frame absent');
    if(await frame.locator('a.play_button').count())await frame.locator('a.play_button').click();
    let state;const deadline=Date.now()+40000;
    while(Date.now()<deadline){state=await frame.evaluate(()=>{const v=[...document.querySelectorAll('video')].find(v=>v.duration>600&&!v.paused&&v.videoWidth>0)||document.querySelector('video');return v?{time:v.currentTime,width:v.videoWidth,ready:v.readyState,paused:v.paused}:null;});if(state?.time>1&&state?.width>0&&state?.paused===false)break;await page.waitForTimeout(500);}
    if(!state?.width)throw Error('Live video did not decode');
    await page.waitForFunction(()=>!document.querySelector('.system-pip-btn')?.disabled);
    const rows=[];
    for(const width of [320,390,768,1280,1920]){await page.setViewportSize({width,height:900});await page.waitForTimeout(350);const layout=await page.evaluate(()=>{const button=document.querySelector('.system-pip-btn'),video=document.querySelector('.player-container');return {overflow:document.documentElement.scrollWidth>innerWidth+1,below:button.getBoundingClientRect().top>=video.getBoundingClientRect().bottom-1,buttons:document.querySelectorAll('.system-pip-btn').length,legacy:document.querySelectorAll('.mini-btn-overlay').length};});if(layout.overflow||!layout.below||layout.buttons!==1||layout.legacy)throw Error('Toolbar layout '+width+' '+JSON.stringify(layout));await page.screenshot({path:'backend/data/local_release/ui-review/system-pip-toolbar-'+(edge?'edge-':'')+width+'.png'});rows.push({width,...layout});}
    await page.getByRole('button',{name:'Полноэкранный режим',exact:true}).click();await page.waitForFunction(()=>!!document.fullscreenElement);await page.getByRole('button',{name:'Выйти из полноэкранного режима',exact:true}).click();await page.waitForFunction(()=>!document.fullscreenElement);
    await page.evaluate(()=>{window.__pipIframe=document.querySelector('.kodik-iframe');window.__pipSource=window.__pipIframe.contentWindow;});
    const before=await frame.evaluate(()=>[...document.querySelectorAll('video')].find(v=>!v.paused&&v.videoWidth>0&&v.readyState>=2)?.currentTime||0);
    await page.getByRole('button',{name:'Поверх всех окон',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('.system-pip-btn')?.getAttribute('aria-pressed')==='true');
    const entered=await frame.evaluate(()=>{window.__nativeVideo=document.pictureInPictureElement;return !!window.__nativeVideo;});if(!entered)throw Error('OS PiP absent');
    const samePlayer=await page.evaluate(()=>document.querySelector('.kodik-iframe')===window.__pipIframe&&window.__pipIframe.contentWindow===window.__pipSource);
    ctx.removeAllListeners('page');const other=await ctx.newPage();await other.goto('about:blank');await other.bringToFront();await page.waitForTimeout(3000);
    const hidden=await page.evaluate(()=>document.visibilityState);const after=await frame.evaluate(()=>({time:(document.pictureInPictureElement||document.querySelector('video')).currentTime,pip:!!document.pictureInPictureElement,paused:(document.pictureInPictureElement||document.querySelector('video')).paused,ready:(document.pictureInPictureElement||document.querySelector('video')).readyState,videos:[...document.querySelectorAll('video')].map(v=>({id:v.id,c:v.className,time:v.currentTime,duration:v.duration,width:v.videoWidth,ready:v.readyState,paused:v.paused,pip:document.pictureInPictureElement===v}))}));
    if(!samePlayer||!after.pip||after.time<=before+1)throw Error('PiP restarted or stopped video '+JSON.stringify({samePlayer,before,after,hidden}));
    await other.close();await page.bringToFront();await page.getByRole('button',{name:'Вернуть в плеер',exact:true}).click();await page.waitForFunction(()=>document.querySelector('.system-pip-btn')?.getAttribute('aria-pressed')==='false');
    const returned=await frame.evaluate(()=>({time:window.__nativeVideo.currentTime,pip:!!document.pictureInPictureElement,paused:window.__nativeVideo.paused,ready:window.__nativeVideo.readyState,connected:document.contains(window.__nativeVideo)}));
    if(returned.pip||returned.time<after.time-1)throw Error('PiP return lost position '+JSON.stringify({after,returned}));
    return {passed:true,samples:rows.length,rows,entered,samePlayer,hidden,before,after,returned,errors};
  } catch(e){return {passed:false,error:e.message,errors};}
  finally {await ctx.close();}
}
