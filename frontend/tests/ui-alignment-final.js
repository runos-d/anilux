async host => {
  const accounts=__ACCOUNTS__,ids=__IDS__,origin=__ORIGIN__,engine=__PHASE__;
  const rows=[],errors=[],failures=[],checks=[],contexts=[];let page,roleName;
  const role=async name=>{
    roleName=name;const context=await host.context().browser().newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,serviceWorkers:'block',reducedMotion:'reduce'});contexts.push(context);
    await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts[name],origin});
    page=await context.newPage();page.setDefaultTimeout(12000);page.on('pageerror',e=>errors.push({role:name,path:new URL(page.url()).pathname,error:e.message}));
  };
  const api=async(path,method='GET',body)=>page.evaluate(async({path,method,body,origin})=>{
    if(location.origin!==origin)throw Error('Wrong fixture origin');
    const base=origin.endsWith(':5186')?'http://localhost:8016/api':origin+'/api';
    const response=await fetch(base+path,{method,credentials:'include',headers:{Authorization:'Bearer '+localStorage.getItem('anilux_access_token_v1'),'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});
    if(!response.ok)throw Error(path+' '+response.status);return response.status===204?null:response.json();
  },{path,method,body,origin});
  const goto=async path=>{await page.setViewportSize({width:390,height:844});await page.goto(origin+path,{waitUntil:'domcontentloaded'});await page.waitForTimeout(1600);await page.addStyleTag({content:'.vue-devtools__anchor,.vue-devtools-frame{display:none!important}'});await page.evaluate(()=>document.querySelectorAll('.notification-toast-close').forEach(button=>button.click()));await page.waitForTimeout(350);};
  const capture=async(name,dialogSelector)=>{
    for(const[width,height]of[[320,780],[390,844],[844,390],[768,1024],[1280,960],[1920,1080]]){
      await page.setViewportSize({width,height});await page.waitForTimeout(550);
      const state=await page.evaluate(selector=>{
        const dialogs=selector?[...document.querySelectorAll(selector)].map(el=>{const r=el.getBoundingClientRect();return{x:r.x,y:r.y,w:r.width,h:r.height};}).filter(r=>r.w&&r.h):[];
        const clipped=[...document.querySelectorAll('button')].filter(el=>{const r=el.getBoundingClientRect();return r.width&&r.height&&el.scrollWidth>el.clientWidth+2&&getComputedStyle(el).textOverflow!=='ellipsis';}).map(el=>({cls:el.className,text:el.innerText.slice(0,70)}));
        return{width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,dialogs,clipped};
      },dialogSelector);
      rows.push({name,...state});
      if(name.startsWith('catalog-')&&await page.locator('.catalog-grid .anime-card').count()===0)throw Error('Catalog contains no rendered cards: '+name);
      if(width===320||width===390||width===1280)await page.screenshot({path:'backend/data/local_release/ui-review/final-'+engine+'-'+name+'-'+width+'.png',animations:'disabled'});
      if(state.scrollWidth>width+1||state.clipped.length||state.dialogs.some(r=>r.x<-.5||r.y<-.5||r.x+r.w>width+1||r.y+r.h>height+1))throw Error('Layout outside viewport: '+name+' '+width);
    }
    await page.setViewportSize({width:390,height:844});await page.waitForTimeout(400);
  };
  const step=async(name,fn)=>{try{await fn();checks.push({name,ok:true});}catch(e){failures.push({name,error:e.message});}};
  try{
    await role('owner');await goto('/profile');
    await step('authenticated-heartbeat',async()=>{await api('/users/heartbeat/','POST',{is_active:true});});
    await step('notifications-controls',async()=>{
      await goto('/notifications/settings');await page.locator('.toggle-input').first().focus();const before=await page.locator('.toggle-input').first().isChecked();await page.keyboard.press('Space');if(await page.locator('.toggle-input').first().isChecked()===before)throw Error('Keyboard toggle did not change');await page.keyboard.press('Space');
      if(await page.locator('.btn-save').innerText()!=='Сохранить'||await page.locator('.btn-save svg').count()!==1)throw Error('Save caption is not rendered');
      await capture('notifications');await page.evaluate(()=>window.scrollTo(0,document.documentElement.scrollHeight));await page.screenshot({path:'backend/data/local_release/ui-review/final-'+engine+'-notification-actions.png'});
    });
    await goto('/profile');
    for(let tab=1;tab<5;tab++)await step('profile-tab'+tab,async()=>{await page.locator('.profile-tabs button').nth(tab).tap();await page.waitForTimeout(650);await capture('profile-tab'+tab);});
    await step('profile-achievement-detail',async()=>{await page.locator('.user-achievements .achievement-card').first().tap();await page.getByRole('dialog').waitFor();await capture('achievement-dialog','[role=dialog]');await page.keyboard.press('Escape');});
    await step('calendar-month',async()=>{await goto('/anime?section=calendar');await page.getByRole('button',{name:'Месяц',exact:true}).tap();await capture('calendar-month');});
    await step('avatar-crop',async()=>{await goto('/settings');await page.locator('.account-settings input[type=file]').first().setInputFiles('frontend/public/pwa/icon-192.png');await page.locator('.ice-modal').waitFor();await capture('avatar-crop','.ice-modal');await page.locator('.ice-close').tap();});
    let postId;
    await step('post-edit-attachments',async()=>{
      const post=await api('/social/posts/','POST',{text:'Проверка вложений из страницы поста '+Date.now(),client_post_id:crypto.randomUUID()});postId=post.id;
      await goto('/post/'+postId);await page.getByRole('button',{name:'Действия с постом',exact:true}).tap();await page.getByRole('button',{name:'Редактировать',exact:true}).tap();await page.locator('.edit-post-modal').waitFor();
      await page.locator('.toolbar-chip').filter({hasText:'Аниме'}).tap();await page.locator('.attach-modal-content').waitFor();await page.getByPlaceholder('Поиск аниме...',{exact:true}).fill('Новые');await page.locator('.anime-result').first().waitFor();await page.locator('.anime-result').first().tap();await capture('post-attachment-picker','.attach-modal-content');
      await page.locator('.attach-modal-btn-confirm').tap();await page.locator('.attach-modal-content').waitFor({state:'hidden'});await page.locator('.edit-post-modal .attach-chip').waitFor();await capture('post-editor-selected','.edit-post-modal');
      await page.locator('.edit-post-modal .submit-btn').tap();await page.locator('.edit-post-modal').waitFor({state:'hidden'});const saved=await api('/social/posts/'+postId+'/');if(!saved.attachments_data?.some(row=>row.content_type==='anime'))throw Error('Selected anime was not persisted');
    });
    if(postId)await api('/social/posts/'+postId+'/','DELETE');
    for(const [name,id] of [['private-chat',ids.chat],['group-chat',ids.group]])await step(name,async()=>{
      await goto('/chats/'+id);await page.locator('.message-textarea').waitFor();await page.waitForTimeout(700);await capture(name);await page.locator('.chat-header button[title="Настройки"]').tap();await page.locator('.chat-settings-modal').waitFor();await capture(name+'-settings','.chat-settings-modal');
    });
    await step('chat-context-reply',async()=>{await goto('/chats/'+ids.chat);await page.locator('.message-textarea').waitFor();await page.locator('.message-body').first().click({button:'right'});await page.locator('.context-popup').waitFor();await capture('message-menu','.context-popup');await page.getByRole('button',{name:'Ответить',exact:true}).tap();await page.locator('.message-reply-preview').waitFor();await capture('message-reply');});
    await step('chat-invite',async()=>{await goto('/chats/'+ids.group);await page.locator('.chat-header button[title="Пригласить"]').tap();await page.getByText('Приглашение в чат',{exact:true}).waitFor();await capture('chat-invite','.modal-content');});
    await step('episode-controls',async()=>{await goto('/anime/kovboy-bibop/watch');await page.locator('.episodes-card').waitFor();await capture('watch-episodes');});
    await goto('/settings');const originalTheme=await api('/users/theme-settings/');
    for(const[name,label]of[['light','Белая'],['dark','Чёрная'],['midnight','Полночная']])await step('theme-'+name,async()=>{
      await goto('/settings');await page.locator('.settings-tabs button').nth(1).tap();await page.getByText(label,{exact:true}).tap();
      if(await page.locator('.save-btn').isEnabled()){const saved=page.waitForResponse(r=>r.request().method()==='PUT'&&r.url().includes('/users/theme-settings/'));await page.locator('.save-btn').tap();if(!(await saved).ok())throw Error('Theme save failed');}
      await page.getByRole('button',{name:'Меню',exact:true}).tap();await page.locator('.menu-items a[href="/anime"]').tap();await page.getByRole('button',{name:'Каталог',exact:true}).tap();await page.locator('.catalog-grid .anime-card').first().waitFor();
      if(await page.evaluate(()=>document.documentElement.dataset.theme)!==(name==='midnight'?'polnochnaya':name))throw Error('Selected theme was not applied: '+name);
      await capture('catalog-'+name);
    });
    await api('/users/theme-settings/','PUT',originalTheme);
    await role('admin');
    await step('franchise-dialog',async()=>{await goto('/admin/franchises');await page.getByRole('button',{name:'Новая франшиза',exact:true}).tap();await page.getByRole('dialog',{name:'Новая франшиза',exact:true}).waitFor();await capture('franchise-modal','[role=dialog]');await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});});
    await step('achievement-editor',async()=>{await goto('/admin');await page.locator('.admin-tabs > button').nth(4).tap();await page.locator('.am-item').first().tap();await page.locator('.am-editor').waitFor();await capture('achievement-editor');});
    return{rows,checks,failures,errors};
  } finally {for(const context of contexts)await context.close();}
}
