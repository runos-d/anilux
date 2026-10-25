async page => {
  const token = await page.evaluate(() => localStorage.getItem('anilux_access_token_v1'));
  const origin = 'http://localhost:8080';
  const ids = await page.evaluate(() => JSON.parse(localStorage.getItem('site_browser_fixture_ids')));
  if (!ids?.video_post) throw new Error('Prepare owned browser fixture metadata first');
  const response = await page.context().request.get(origin+'/api/social/posts/'+ids.video_post+'/', { headers:{ Authorization:'Bearer '+token } });
  if (!response.ok()) throw new Error('Prepared video post is unavailable');
  const post = await response.json();
  const media = post.media_files.find(item => item.media_type === 'video');
  if (!media || media.processing_state !== 'ready') throw new Error('Video is not ready');
  const head = await page.context().request.head(media.url);
  const range = await page.context().request.get(media.url, { headers:{ Range:'bytes=0-1023' } });
  await page.goto(origin+'/post/'+ids.video_post);
  await page.locator('.post-card video').waitFor({ state:'visible' });
  const playback = await page.locator('.post-card video').evaluate(async video => {
    video.muted = true;
    const start = performance.now();
    const frame = new Promise((resolve,reject) => {
      const timeout = setTimeout(() => reject(new Error('Video start timeout')),10000);
      video.requestVideoFrameCallback(() => { clearTimeout(timeout); resolve(performance.now()-start); });
    });
    await video.play();
    const startMs = await frame;
    video.pause();
    const seekStart = performance.now();
    const seek = new Promise(resolve => video.addEventListener('seeked', () => resolve(performance.now()-seekStart), { once:true }));
    video.currentTime = 3;
    const seekMs = await seek;
    return { startMs:Math.round(startMs), seekMs:Math.round(seekMs), position:video.currentTime,
      width:video.videoWidth, height:video.videoHeight, duration:video.duration };
  });
  const report = { head:head.status(), range:range.status(), contentRange:range.headers()['content-range'],
    length:head.headers()['content-length'], cache:head.headers()['cache-control'], playback };
  await page.evaluate(report => localStorage.setItem('site_media_report',JSON.stringify(report)),report);
  return report;
}
