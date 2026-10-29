const p=await page.context().newPage();await installVisualSession(p,'dark');
const reply=(route,data)=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
await p.route('**/api/anime/1/kodik_translations/',r=>reply(r,{translations:[{id:42,name:'Тестовая озвучка',type:'voice',episodes_done:12,kodik_link:'https://kodikplayer.com/serial/a/720p',seasons:{'1':{episodes:Array.from({length:12},(_,i)=>i+1)}}}],allow_flat:false}));
await p.route('**/api/anime/1/kodik_player/',r=>reply(r,{kodik_link:'https://kodikplayer.com/serial/a/720p',last_episode:12}));
await p.route('https://kodikplayer.com/**',r=>r.fulfill({status:200,contentType:'text/html',body:'<html><body>Player stub</body></html>'}));
let calls=[];p.on('request',r=>{if(r.url().includes('/api/anime/1/'))calls.push(new URL(r.url()).pathname+new URL(r.url()).search)});
await p.goto('http://127.0.0.1:4398/anime/1-fioletovyy-sad/watch?episode=5&season=1');await p.waitForTimeout(3200);
const result={calls,selected:await p.locator('.ep-row.is-current').allTextContents(),body:await p.locator('body').innerText()};await p.close();return result;
