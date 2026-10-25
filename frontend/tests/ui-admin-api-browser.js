async host => {
  const accounts=__ACCOUNTS__, browser=host.context().browser(), rows=[],errors=[];
  const ctx=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'block'});
  await ctx.addInitScript(account=>{if(!['http://localhost:5186','http://localhost:5187'].includes(location.origin))return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},accounts.admin);
  const page=await ctx.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push(e.message));page.on('dialog',d=>d.accept());
  const shot=async name=>{for(const width of [320,390,768,1280,1920]){await page.setViewportSize({width,height:844});await page.waitForTimeout(350);const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);if(overflow){await page.screenshot({path:'backend/data/local_release/ui-review/api-overflow.png'});throw Error('Overflow '+name+' '+width+' '+JSON.stringify(await page.evaluate(()=>[...document.querySelectorAll('body *')].map(e=>({tag:e.tagName,c:e.className,w:e.getBoundingClientRect().width,r:e.getBoundingClientRect().right,text:e.innerText?.slice(0,60)})).filter(e=>e.r>innerWidth+1).slice(-25))));}await page.screenshot({path:'backend/data/local_release/ui-review/api-'+name+'-'+width+'.png'});rows.push({name,width,overflow});}};
  const wait=async(path,method,action)=>{const [response]=await Promise.all([page.waitForResponse(r=>r.url().includes(path)&&r.request().method()===method),action()]);if(response.status()>=400)throw Error(path+' '+response.status());return response.status()===204?null:response.json();};
  try {
    await page.goto('http://localhost:5186/admin');
    await page.getByRole('button',{name:'Франшизы',exact:true}).click();
    await page.locator('.fm-count').waitFor();await page.getByRole('button',{name:'Новая франшиза',exact:true}).click();
    await page.getByPlaceholder('Например: Re:Zero').fill('Проверка API -франшиза');
    const created=await wait('/admin/franchises/','POST',()=>page.getByRole('button',{name:'Создать',exact:true}).click());
    await page.locator('.fm-editor').waitFor();await shot('franchise-empty');
    for(const name of ['Проверка API -первая часть','Проверка API -вторая часть']){
      await page.locator('.fm-add-search input').fill(name);
      const row=page.locator('.fm-add-result').filter({hasText:name});await row.waitFor();
      await wait('/add-anime/','POST',()=>row.getByTitle('Добавить в франшизу').click());
    }
    await page.locator('.fm-entry').nth(1).waitFor();
    const reordered=await wait('/reorder/','POST',()=>page.locator('.fm-entry').nth(1).getByTitle('Поднять выше').click());
    if(reordered.entries[0].id!==95400302)throw Error('Order not saved');await shot('franchise-parts');
    await page.locator('.fm-main-fields input').fill('Проверка API -изменено');
    await wait('/admin/franchises/'+created.id+'/','PATCH',()=>page.getByRole('button',{name:'Сохранить',exact:true}).click());
    await wait('/remove-anime/','POST',()=>page.locator('.fm-entry').nth(0).getByTitle('Убрать из франшизы').click());
    await page.locator('.fm-main-btns').getByRole('button',{name:'Удалить',exact:true}).click();
    await wait('/admin/franchises/'+created.id+'/','DELETE',()=>page.getByRole('dialog').getByRole('button',{name:'Удалить',exact:true}).click());
    await page.getByRole('button',{name:'Каталог',exact:true}).click();await page.locator('.cm-form').waitFor();await shot('catalog-ready');
    await page.locator('.cm-form select').first().selectOption('title');
    await page.getByPlaceholder('Значение (например: Токийский гуль, франшиза...)').fill('Проверка API');
    const rule=await wait('/catalog-rules/','POST',()=>page.getByRole('button',{name:'Добавить правило и скрыть найденные'}).click());
    if(rule.matched_count!==2||rule.hidden_count!==2)throw Error('Rule counts wrong');await page.locator('.cm-hidden-list .cm-hidden-item').nth(1).waitFor();await shot('catalog-hidden');
    await wait('/restore/','POST',()=>page.locator('.cm-hidden-list .cm-hidden-item').first().getByRole('button',{name:'Вернуть',exact:true}).click());
    await wait('/catalog-rules/'+rule.id+'/','POST',()=>page.locator('.cm-rule').filter({hasText:'Проверка API'}).getByRole('button',{name:'Применить',exact:true}).click());
    await wait('/catalog-rules/'+rule.id+'/','DELETE',()=>page.locator('.cm-rule').filter({hasText:'Проверка API'}).getByRole('button',{name:'Удалить',exact:true}).click());
    await page.locator('.cm-manual-list').count();
    await page.locator('.cm-card').filter({has:page.getByRole('heading',{name:'Скрыть конкретное аниме вручную'})}).getByPlaceholder('Поиск по названию...').fill('Проверка API');
    await page.locator('.cm-manual-list .cm-hidden-item').first().waitFor();
    await wait('/catalog-hidden/','POST',()=>page.locator('.cm-manual-list .cm-hidden-item').first().getByRole('button',{name:'Скрыть',exact:true}).click());
    await wait('/restore/','POST',()=>page.locator('.cm-hidden-list .cm-hidden-item').first().getByRole('button',{name:'Вернуть',exact:true}).click());
    if(errors.length)throw Error(errors.join('; '));return {passed:true,samples:rows.length,rows,errors};
  } catch(e) {return {passed:false,error:e.stack,rows,errors};}
  finally {await ctx.close();}
}
