async host => {
  const accounts=__ACCOUNTS__,fixture=__FIXTURE__,origin='http://localhost:5186',checks=[];
  for(const mobile of [false,true]){
    const context=await host.context().browser().newContext({viewport:{width:mobile?390:1440,height:900},isMobile:mobile,hasTouch:mobile,serviceWorkers:'block'});
    await context.addInitScript(({account,origin})=>{if(location.origin!==origin)return;localStorage.setItem('anilux_user_v1',JSON.stringify(account.user));localStorage.setItem('anilux_access_token_v1',account.tokens.access);localStorage.setItem('anilux_refresh_token_v1',account.tokens.refresh);},{account:accounts.owner,origin});
    const p=await context.newPage();await p.goto(origin,{waitUntil:'domcontentloaded'});
    const card=p.locator('.home-new-episodes .new-episode-card').filter({hasText:'Home Date Proof'});await card.waitFor();
    const label=await card.locator('.new-episode-count').innerText();
    if(!label.includes('4')||!label.includes('2')||label.includes('7'))throw Error('Incorrect new episode counters: '+label);
    const watch=card.locator('.new-episode-watch');if(mobile)await watch.tap();else await watch.click();
    await p.waitForURL('**/anime/'+fixture.slug+'/watch?episode=3',{waitUntil:'domcontentloaded'});
    checks.push({mobile,filteredCount:2,latestEligibleEpisode:4,watchStartsAt:3});await context.close();
  }
  return {checks};
}
