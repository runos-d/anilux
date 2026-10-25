async host => {
  const accounts=__ACCOUNTS__, origin='http://localhost:5186', rows=[], errors=[];
  for (const mobile of [false,true]) {
    const context=await host.context().browser().newContext({viewport:{width:mobile?390:1440,height:900},isMobile:mobile,hasTouch:mobile,serviceWorkers:'block'});
    await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts.admin,origin});
    const p=await context.newPage();p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.status()>=400&&r.url().includes('/api/'))errors.push(r.status()+' '+new URL(r.url()).pathname)});
    await p.goto(origin+'/admin');await p.locator('.admin-tabs > button').first().waitFor();await p.waitForTimeout(800);
    for(let i=0;i<7;i++) {
      const b=p.locator('.admin-tabs > button').nth(i);const label=await b.innerText();if(mobile)await b.tap();else await b.click();await p.waitForTimeout(800);
      rows.push({mobile,label,active:await b.getAttribute('class'),text:(await p.locator('main').innerText()).slice(-1800)});
    }
    await p.goto(origin+'/anime?section=catalog');await p.waitForTimeout(1400);
    rows.push({mobile,catalog:await p.locator('.franchise-card').count(),anime:await p.locator('.anime-card').count()});
    await context.close();
  }
  return {rows,errors};
}
