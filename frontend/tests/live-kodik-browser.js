async host => {
  const accounts=__ACCOUNTS__,context=await host.context().browser().newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
  await context.addInitScript(account=>{if(!['http://localhost:5186','http://localhost:5187'].includes(location.origin))return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);window.__kodikEvents=[];window.addEventListener('message',e=>{if(e.data?.key?.startsWith('kodik_'))window.__kodikEvents.push({key:e.data.key,value:typeof e.data.value==='number'?e.data.value:null});});},accounts.reader);
  const page=await context.newPage();page.setDefaultTimeout(20000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try {
    await page.goto('http://localhost:5187/add-anime');
    const posters=page.getByRole('switch',{name:'Скачивать постеры на сервер'});if(await posters.getAttribute('aria-checked')==='true')await posters.click();
    await page.getByPlaceholder('Например: Ван Пис, Наруто, Атака титанов...').fill('Cowboy Bebop');
    const [search]=await Promise.all([page.waitForResponse(r=>r.url().includes('/kodik/search-candidates/')),
      page.getByRole('button',{name:'Искать',exact:true}).click()]);
    const found=await search.json();if(search.status()!==200)throw Error('Provider search failed');
    const group=found.groups.find(g=>g.items.some(i=>i.shikimori_id===1));
    if(group.items[0].shikimori_id!==1)throw Error('Manga/order regression');
    if(group.items.some(i=>i.kodik_available===false)){const unavailable=page.getByRole('button',{name:'Нет в Kodik',exact:true});if(!(await unavailable.getAttribute('class')).includes('kind-chip-active'))await unavailable.click();}
    const bulk=page.locator('.group-block').filter({hasText:'Cowboy Bebop'}).getByRole('button',{name:/Добавить отсутствующее/});
    let added={results:[],reused:true};
    if(await bulk.count()&&await bulk.isEnabled()){
      const [response]=await Promise.all([page.waitForResponse(r=>r.url().includes('/kodik/user-add/')&&r.request().method()==='POST',{timeout:180000}),bulk.click()]);
      added=await response.json();if(response.status()!==200||added.results.some(i=>!i.ok))throw Error('Live import failed '+JSON.stringify(added.results));
    }
    const detail=await page.evaluate(async()=>{const r=await fetch('http://localhost:8016/api/anime/?search=Ковбой&group_franchises=false&page_size=50');return r.json();});
    const entries=detail.results.filter(i=>[1,5,4037].includes(i.shikimori_id));
    await page.screenshot({path:'backend/data/local_release/ui-review/live-kodik-import.png'});
    const first=added.results.find(i=>i.shikimori_id===1);
    const slug=first?.slug||detail.results.find(i=>i.title_ru===group.items.find(i=>i.shikimori_id===1).title_ru)?.slug;
    if(!slug)throw Error('Imported anime not present in catalogue');
    await page.goto('http://localhost:5187/anime/'+slug);
    await page.getByRole('button',{name:'Смотреть',exact:true}).click();await page.locator('.kodik-iframe').waitFor();
    await page.waitForTimeout(6000);
    const provider=page.frames().find(f=>f.url().includes('kodikplayer.com'));
    if(provider&&await provider.locator('a.play_button').count()){
      context.on('page',popup=>{if(popup!==page)void popup.close();});
      await provider.locator('a.play_button').click();await page.waitForTimeout(8000);
    }
    const playback=[];
    for(const frame of page.frames().filter(f=>f.url().includes('kodik'))){
      const videos=frame.locator('video');const count=await videos.count();
      if(count){
        const video=videos.first();
        const started=await video.evaluate(v=>{v.muted=true;return v.play().then(()=>({ok:true})).catch(e=>({ok:false,error:e.message}));}).catch(e=>({ok:false,error:e.message}));
        const initial=await video.evaluate(v=>({time:v.currentTime,ready:v.readyState,paused:v.paused,width:v.videoWidth,error:v.error?.code}));
        await page.waitForTimeout(3000);const after=await video.evaluate(v=>({time:v.currentTime,ready:v.readyState,paused:v.paused,width:v.videoWidth,error:v.error?.code}));
        playback.push({host:new URL(frame.url()).hostname,started,initial,after,verified:after.time>initial.time+1&&after.width>0});
      }else playback.push({host:new URL(frame.url()).hostname,videos:0,body:(await frame.locator('body').innerText()).slice(0,400),controls:await frame.locator('button,[role=button],[class*=play]').evaluateAll(es=>es.slice(0,12).map(e=>({tag:e.tagName,c:e.className,title:e.title,text:e.innerText?.slice(0,30)})))});
    }
    return {passed:true,providerIds:group.items.map(i=>i.shikimori_id),imported:added.results.map(i=>({id:i.shikimori_id,ok:i.ok,slug:i.slug})),
      reusedExistingTitles:added.reused||false,playback,playerFrames:page.frames().filter(f=>f.url().includes('kodik')).map(f=>({host:new URL(f.url()).hostname})),errors};
  } catch(e){return {passed:false,error:e.message,errors};}
}
