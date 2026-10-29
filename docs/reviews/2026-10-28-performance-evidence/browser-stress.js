const stressPage = await page.context().newPage();
try {
await installVisualSession(stressPage,'dark');
await stressPage.setViewportSize({width:390,height:844});
const cdp=await stressPage.context().newCDPSession(stressPage);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
await stressPage.addInitScript(()=>{window.__longTasks=[];new PerformanceObserver(list=>window.__longTasks.push(...list.getEntries().map(e=>Math.round(e.duration)))).observe({type:'longtask',buffered:true});});
let requests=[];const errors=[];stressPage.on('request',r=>{if(r.url().includes('/api/'))requests.push(r.method()+' '+new URL(r.url()).pathname+new URL(r.url()).search)});stressPage.on('pageerror',e=>errors.push(e.message));
const routes=[];
for(const path of ['/','/anime?section=catalog','/anime?section=calendar','/feed','/chats','/settings','/anime/1-fioletovyy-sad/watch?episode=5']){
 requests=[];await stressPage.goto('http://127.0.0.1:4398'+path);await stressPage.waitForTimeout(2200);
 routes.push({path,requests:[...requests],...await stressPage.evaluate(()=>({dom:document.querySelectorAll('*').length,overflow:document.documentElement.scrollWidth>innerWidth+1,longTasks:window.__longTasks,paint:performance.getEntriesByType('paint').map(e=>({name:e.name,ms:Math.round(e.startTime)}))}))});
}
await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});
await stressPage.setViewportSize({width:1440,height:1000});
let batches=0;
await stressPage.route('**/api/social/feed/extended/**',route=>{const url=new URL(route.request().url());const n=Number(url.searchParams.get('cursor')||0);batches++;return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({results:Array.from({length:20},(_,i)=>({...post,id:n*20+i+10000,text:`Публикация ${n*20+i}: `+post.text})),next_cursor:String(n+1)})});});
await stressPage.goto('http://127.0.0.1:4398/feed');await stressPage.waitForTimeout(1200);
const feed=[];
for(let i=0;i<16;i++){
 await stressPage.evaluate(()=>{window.scrollTo(0,document.documentElement.scrollHeight);window.dispatchEvent(new Event('scroll'));});await stressPage.waitForTimeout(450);
 if([0,4,9,15].includes(i))feed.push({step:i,batches,...await stressPage.evaluate(()=>({cards:document.querySelectorAll('[data-post-id]').length,dom:document.querySelectorAll('*').length,longTasks:window.__longTasks.slice(-8),heap:performance.memory?.usedJSHeapSize}))});
}
return {errors,routes,feed};

} finally { await stressPage.close(); }
