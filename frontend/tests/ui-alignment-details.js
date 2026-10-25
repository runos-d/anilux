async host => {
  const accounts=__ACCOUNTS__,ids=__IDS__,engine=__PHASE__,origin='http://localhost:5186';
  const rows=[],failures=[],errors=[],contexts=[];let page;
  const role=async name=>{
    const context=await host.context().browser().newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block',reducedMotion:'reduce'});contexts.push(context);
    await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts[name],origin});
    page=await context.newPage();page.setDefaultTimeout(9000);page.on('pageerror',e=>errors.push({role:name,path:new URL(page.url()).pathname,error:e.message}));
  };
  const goto=async path=>{await page.setViewportSize({width:390,height:844});await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.waitForTimeout(1300);await page.addStyleTag({content:'.vue-devtools__anchor,.vue-devtools-frame{display:none!important}'});await page.evaluate(()=>document.querySelectorAll('.notification-toast-close').forEach(button=>button.click()));await page.waitForTimeout(350);};
  const inspect=()=>{
    const visible=el=>{const r=el.getBoundingClientRect(),s=getComputedStyle(el);return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&s.opacity!=='0';};
    const clipped=[...document.querySelectorAll('button')].filter(visible).filter(el=>el.scrollWidth>el.clientWidth+2&&getComputedStyle(el).textOverflow!=='ellipsis').map(el=>({cls:el.className,text:el.innerText.trim().slice(0,60)}));
    const dialogs=[...document.querySelectorAll('[role=dialog],.reminder-modal,.edit-modal,.playlist-select-modal,.post-menu,.report-modal,.repost-modal,.chat-settings-modal,.attach-modal-content,.base-modal,.new-chat-modal,.global-chat-style-modal')].filter(visible).map(el=>{const r=el.getBoundingClientRect();return{cls:el.className,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};});
    const components=new Set(),seen=new Set();const visit=v=>{if(!v||seen.has(v))return false;seen.add(v);let shown=v.el instanceof Element&&visible(v.el);if(v.component){const child=visit(v.component.subTree);if(child&&v.component.type?.__file)components.add(v.component.type.__file.replace(/^.*\/src\//,'src/'));shown=shown||child;}if(Array.isArray(v.children))for(const child of v.children)shown=visit(child)||shown;return shown;};visit(document.querySelector('#app')?.__vue_app__?._instance?.subTree);
    return{width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,clipped,dialogs,components:[...components]};
  };
  const capture=async name=>{
    for(const [width,height] of (engine==='webkit'?[[320,780],[390,844],[844,390]]:[[320,780],[390,844],[844,390],[768,1024],[1440,960],[1920,1080]])) {
      await page.setViewportSize({width,height});await page.waitForTimeout(500);
      await page.evaluate(()=>document.querySelectorAll('.notification-toast-close').forEach(button=>button.click()));await page.waitForTimeout(350);
      for(let n=0;n<6&&await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);n++)await page.waitForTimeout(200);
      rows.push({name,...await page.evaluate(inspect)});await host.evaluate(({key,value})=>sessionStorage.setItem(key,JSON.stringify(value)),{key:'alignment-details-'+engine,value:{rows,errors,failures}});
      if(width===390||width===1440)await page.screenshot({path:'backend/data/local_release/ui-review/details-'+engine+'-'+name+'-'+width+'.png',animations:'disabled'});
    }
    await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
  };
  const step=async(name,fn)=>{try{await fn();await capture(name);}catch(e){failures.push({name,error:e.message});}};
  try {
    await role('owner');
    await step('mobile-menu',async()=>{await goto('/anime');await page.getByRole('button',{name:'Меню',exact:true}).tap();});
    await step('mobile-search',async()=>{await page.locator('.menu-items input.search-input').fill('Новые');await page.locator('.menu-items .search-suggestions').waitFor();});
    await step('profile-navigation',async()=>{await goto('/anime');await page.getByRole('link',{name:'Профиль',exact:true}).tap();await page.locator('.user-profile-view').first().waitFor();});
    await step('catalog-filters',async()=>{await goto('/anime');await page.locator('.afb-btn[title="Фильтры"]').tap();await page.locator('.afb-panel').waitFor();});
    await step('reminder',async()=>{await goto('/anime');await page.locator('.franchise-card .reminder-btn').first().tap();await page.locator('.reminder-modal').waitFor();});
    await step('library-menu',async()=>{await goto('/library');await page.locator('.menu-btn').first().tap();});
    await step('library-editor',async()=>{await page.getByRole('button',{name:'Редактировать',exact:true}).tap();await page.locator('.edit-modal').waitFor();});
    await step('playlist-selection',async()=>{await goto('/anime/'+ids.animeSlug);await page.getByRole('button',{name:'В плейлист',exact:true}).tap();await page.locator('.playlist-select-modal').waitFor();});
    await step('playlist-new-modal',async()=>{await page.locator('.create-playlist-btn').tap();});
    await goto('/playlists');for(let n=0;n<await page.locator('.tabs-row > button').count();n++)await step('playlists-tab'+n,async()=>{await page.locator('.tabs-row > button').nth(n).tap();});
    await step('notification-dnd',async()=>{await goto('/notifications/settings');await page.locator('.toggle-row').filter({hasText:'Включить по расписанию'}).tap();await page.locator('.dnd-times').waitFor();});
    await step('theme-settings',async()=>{await goto('/settings');await page.locator('.settings-tabs button').nth(1).tap();});
    await step('feed-filters',async()=>{await goto('/feed');await page.locator('.filter-toggle').tap();await page.locator('.filters-dropdown').waitFor();});
    await step('post-menu',async()=>{await goto('/post/'+ids.post);await page.getByRole('button',{name:'Действия с постом',exact:true}).first().tap();await page.locator('.post-menu').waitFor();});
    await step('post-editor',async()=>{
      const id=await page.evaluate(async()=>{const{default:api}=await import('/src/api/client.ts');return(await api.post('/social/posts/',{text:'Длинный проверочный текст '.repeat(25),client_post_id:crypto.randomUUID()})).data.id;});
      await goto('/post/'+id);await page.getByRole('button',{name:'Действия с постом',exact:true}).first().tap();await page.getByRole('button',{name:'Редактировать',exact:true}).tap();await page.locator('.edit-post-modal').waitFor();
    });
    await step('photo-expanded',async()=>{await goto('/post/'+ids.photoPost);await page.locator('.stack-preview').first().tap();await page.locator('.media-item').first().waitFor();});
    await step('photo-lightbox',async()=>{await page.locator('.media-item img').first().tap();await page.locator('.lightbox-overlay').waitFor();});
    await step('chat-search',async()=>{await goto('/chats/'+ids.chat);await page.locator('.chat-header button[title="Поиск по сообщениям"]').tap();});
    for(const [name,id] of [['private',ids.chat],['group',ids.group]]) {
      await goto('/chats/'+id);await page.locator('.chat-header button[title="Настройки"]').tap();await page.locator('.chat-settings-modal').waitFor();
      const count=await page.locator('.chat-settings-modal .sidebar-nav .nav-item').count();
      for(let n=0;n<count;n++)await step(name+'-settings'+n,async()=>{await page.locator('.chat-settings-modal .sidebar-nav .nav-item').nth(n).tap();await page.waitForTimeout(650);});
    }
    await step('new-chat',async()=>{await goto('/chats');await page.getByRole('button',{name:'Новый чат',exact:true}).tap();});
    await step('new-group',async()=>{await page.getByRole('button',{name:'Группа',exact:true}).tap();});
    const excerpt={id:987654,anime_id:ids.anime,anime_title:'Длинное название аниме '.repeat(8),poster_url:'',season:1,episode:12,translation_id:1,translation_title:'Очень длинная озвучка '.repeat(5),player_link:'',duration:1440,start:30,end:65,title:'Проверка заголовка '.repeat(9),description:'Описание отрывка '.repeat(30),shared:false};
    await page.route('**/api/anime/excerpts/**',r=>r.fulfill({json:new URL(r.request().url()).pathname.endsWith('/excerpts/')?{results:[excerpt],count:1,next:null}:excerpt}));
    await step('excerpt-long-card',async()=>{await goto('/excerpts');await page.locator('.excerpt-card:not(.unavailable)').waitFor();});
    await step('excerpt-editor',async()=>{await page.getByRole('button',{name:'Редактировать',exact:true}).tap();await page.locator('.excerpt-editor').waitFor();});
    await step('excerpt-validation',async()=>{await page.getByLabel('Конец отрывка вручную').fill('0');await page.getByRole('button',{name:'Сохранить отрывок',exact:true}).tap();await page.locator('.excerpt-editor [role=alert]').waitFor();});
    await role('reader');
    await step('reader-post-menu',async()=>{await goto('/post/'+ids.post);await page.getByRole('button',{name:'Действия с постом',exact:true}).first().tap();});
    await step('report-post',async()=>{await page.getByRole('button',{name:'Пожаловаться',exact:true}).tap();await page.locator('.report-dialog').waitFor();});
    await role('admin');
    await step('franchise-create',async()=>{await goto('/admin/franchises');await page.getByRole('button',{name:'Новая франшиза',exact:true}).tap();await page.getByRole('dialog',{name:'Новая франшиза',exact:true}).waitFor();});
    await step('achievement-editor',async()=>{await goto('/admin');await page.locator('.admin-tabs > button').nth(4).tap();await page.locator('.am-item').first().tap();await page.locator('.am-editor').waitFor();});
    return {rows,errors,failures};
  } finally {for(const context of contexts)await context.close();}
}
