async page => {
  const context=page.context();context.on('page',p=>{if(p!==page)void p.close();});
  const messages=[];await page.evaluate(()=>{window.__pipMessages=[];window.addEventListener('message',e=>{if(e.data?.key?.includes('pip'))window.__pipMessages.push({key:e.data.key});});});
  await page.locator('.kodik-iframe').waitFor();await page.waitForTimeout(4000);
  const frame=page.frames().find(f=>f.url().includes('kodikplayer.com'));if(!frame)throw Error('Provider frame missing');
  if(await frame.locator('a.play_button').count())await frame.locator('a.play_button').click();
  for(let i=0;i<70;i++){
    const playing=await frame.evaluate(()=>[...document.querySelectorAll('video')].some(v=>!v.paused&&v.videoWidth>0&&v.readyState>=2));
    if(playing)break;await page.waitForTimeout(500);
  }
  const inspect=async()=>({provider:await frame.evaluate(()=>({active:navigator.userActivation.isActive,sticky:navigator.userActivation.hasBeenActive,pip:!!document.pictureInPictureElement,videos:[...document.querySelectorAll('video')].map(v=>({time:v.currentTime,width:v.videoWidth,ready:v.readyState,paused:v.paused}))})),button:await page.locator('.system-pip-btn').getAttribute('aria-pressed'),error:await page.locator('.player-window-error').allTextContents()});
  const rows=[{name:'playing',...await inspect()}];
  for(let i=0;i<3;i++){
    await page.locator('.system-pip-btn').click();await page.waitForTimeout(3400);rows.push({name:'enter-'+i,...await inspect()});
    if(await page.locator('.system-pip-btn').getAttribute('aria-pressed')==='true'){
      await page.locator('.system-pip-btn').click();await page.waitForTimeout(600);rows.push({name:'exit-'+i,...await inspect()});
    }
    await page.waitForTimeout(5500);
  }
  return {rows,messages:await page.evaluate(()=>window.__pipMessages)};
}
