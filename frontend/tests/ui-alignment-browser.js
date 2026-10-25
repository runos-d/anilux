async host => {
  const accounts=__ACCOUNTS__,ids=__IDS__,engine=__PHASE__,origin='http://localhost:5186';
  const rows=[],errors=[],failures=[],apiFailures=[];
  const targets={
    guest:['/','/login','/register','/app','/anime?section=catalog','/anime?section=ongoings','/anime?section=recommendations','/anime?section=calendar','/anime?section=currently_watching','/anime/'+ids.animeSlug,'/franchise/'+ids.franchiseSlug,'/people','/add-anime','/donate','/playlist/shared/invalid-test-token','/chats/invite/invalidtesttoken'],
    owner:['/','/app','/profile','/profile/@ui-reader','/library','/stats','/feed','/post/'+ids.post,'/chats','/chats/'+ids.chat,'/chats/'+ids.group,'/playlists','/playlist/'+ids.playlist,'/playlists/create','/playlists/'+ids.playlist+'/edit','/notifications','/notifications/settings','/settings','/achievements','/people','/add-anime','/anime/kovboy-bibop/watch','/excerpts'],
    reader:['/post/'+ids.post,'/profile/@ui-owner','/playlist/'+ids.playlist],
    admin:['/admin','/admin/complaints','/admin/franchises'],
  };
  const inspect=()=>{
    const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&s.opacity!=='0'&&!el.closest('[aria-hidden=true]');};
    const interactive=[...document.querySelectorAll('button,a,input,select,textarea,[role=button]')].filter(visible);
    const small=interactive.filter(el=>{const r=el.getBoundingClientRect();return r.width<30||r.height<30;}).map(el=>({tag:el.tagName,cls:typeof el.className==='string'?el.className:'',label:(el.getAttribute('aria-label')||el.getAttribute('title')||el.innerText||'').trim().slice(0,65),w:Math.round(el.getBoundingClientRect().width),h:Math.round(el.getBoundingClientRect().height)}));
    const clipped=interactive.filter(el=>el.tagName==='BUTTON'&&el.scrollWidth>el.clientWidth+2&&getComputedStyle(el).textOverflow!=='ellipsis').map(el=>({cls:el.className,text:el.innerText.trim().slice(0,70)}));
    const components=new Set(),seen=new Set();
    const visit=v=>{if(!v||seen.has(v))return false;seen.add(v);let shown=v.el instanceof Element&&visible(v.el);if(v.component){const child=visit(v.component.subTree);if(child&&v.component.type?.__file)components.add(v.component.type.__file.replace(/^.*\/src\//,'src/'));shown=shown||child;}if(Array.isArray(v.children))for(const child of v.children)shown=visit(child)||shown;return shown;};
    const root=document.querySelector('#app')?.__vue_app__?._instance;if(root)visit(root.subTree);
    return {width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,small,clipped,components:[...components],heading:document.querySelector('main h1, main h2')?.textContent?.trim()};
  };
  for(const [role,paths] of Object.entries(targets)){
    for(const device of (engine==='webkit'?['phone']:['phone','desktop'])){
      const context=await host.context().browser().newContext({viewport:{width:device==='phone'?390:1440,height:900},isMobile:device==='phone',hasTouch:device==='phone',serviceWorkers:'block',reducedMotion:'reduce',timezoneId:'Europe/Moscow'});
      if(accounts[role])await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts[role],origin});
      const page=await context.newPage();page.setDefaultTimeout(15000);
      page.on('pageerror',error=>errors.push({role,path:new URL(page.url()).pathname,error:error.message}));
      page.on('response',r=>{if(r.status()>=400&&r.url().includes('localhost:8016/api/'))apiFailures.push({role,path:new URL(r.url()).pathname,status:r.status()});});
      try{
        for(const [index,path] of paths.entries()){
          try{
            await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.locator('main').first().waitFor();await page.waitForTimeout(1100);
            await page.addStyleTag({content:'.vue-devtools__anchor,.vue-devtools-frame {display:none!important}'});
            await page.evaluate(()=>document.querySelectorAll('.notification-toast-close').forEach(button=>button.click()));
            await page.waitForTimeout(350);
            const variants=path==='/admin'?Array.from({length:7},(_,i)=>i):[null];
            for(const variant of variants){
              if(variant!==null){await page.locator('.admin-tabs > button').nth(variant).click();await page.waitForTimeout(450);}
              for(const [width,height] of (device==='phone'?[[320,780],[390,844],[844,390]]:[[768,1024],[1280,960],[1440,960],[1920,1080]])){
                await page.setViewportSize({width,height});await page.waitForTimeout(400);
                for(let retry=0;retry<8&&await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);retry++)await page.waitForTimeout(200);
                const state=await page.evaluate(inspect),name=role+'-'+index+(variant===null?'':'-tab'+variant)+'-'+width;
                rows.push({role,device,path,variant,url:page.url().replace(origin,''),...state});
                await host.evaluate(({key,value})=>sessionStorage.setItem(key,JSON.stringify(value)),{key:'alignment-'+engine,value:{rows,errors,failures,apiFailures}});
                if(width===390||width===1440||state.scrollWidth>state.width+1||state.clipped.length){
                  await page.screenshot({path:'backend/data/local_release/ui-review/alignment-'+engine+'-'+name+'.png',animations:'disabled',timeout:15000});
                  if(width===390) {
                    await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));await page.waitForTimeout(250);
                    await page.screenshot({path:'backend/data/local_release/ui-review/alignment-'+engine+'-'+name+'-bottom.png',animations:'disabled',timeout:15000});
                    await page.evaluate(()=>window.scrollTo(0,0));
                  }
                }
              }
            }
          }catch(error){failures.push({role,path,device,error:error.message});}
        }
      }finally{await context.close();}
    }
  }
  return {rows,errors,failures,apiFailures};
}
