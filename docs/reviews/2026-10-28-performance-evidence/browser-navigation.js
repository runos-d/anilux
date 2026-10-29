const p=await page.context().newPage();await installVisualSession(p,'dark');
const errors=[];p.on('pageerror',e=>errors.push(e.message));
let requests=[];p.on('request',r=>requests.push(new URL(r.url()).pathname));
await p.goto('http://localhost:5173/');
await p.locator('a[href="/feed"]').first().waitFor({state:'visible'});
const rows=[];
for(const [path,selector] of [['/feed','.feed-page'],['/anime?section=recommendations','.anime-view'],['/feed','.feed-page'],['/anime?section=recommendations','.anime-view']]) {
 requests=[];
 const row=await p.evaluate(async ({path,selector})=>{
  const started=performance.now();
  await document.querySelector('#app').__vue_app__.config.globalProperties.$router.push(path);
  for(let i=0;i<300&&!document.querySelector(selector);i++)await new Promise(r=>setTimeout(r,10));
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  const viewVisibleMs=Math.round(performance.now()-started);
  const content=path.startsWith('/feed')?'.feed-page .post-card':'.anime-view .rec-card-wrap';
  for(let i=0;i<500&&!document.querySelector(content);i++)await new Promise(r=>setTimeout(r,10));
  await new Promise(resolve=>requestAnimationFrame(resolve));
  return {path,viewVisibleMs,contentReadyMs:Math.round(performance.now()-started),found:!!document.querySelector(content)};
 },{path,selector});
 row.requests=requests;rows.push(row);await p.waitForTimeout(400);
}
await p.close();return {environment:'Vite development, fresh browser, fixture API, service workers blocked',rows,errors};
