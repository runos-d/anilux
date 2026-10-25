async page => {
  const origin = 'http://localhost:8096';
  const catalog = await (await page.request.get(origin + '/api/seo/page/', { params: { path: '/anime/year/2020' } })).json();
  if (catalog.items?.length !== 24) throw new Error('Seed the public media sample first');
  let playable;
  for (const item of catalog.items) {
    const id = item.path.match(/\/anime\/(\d+)-/)[1];
    const detail = await (await page.request.get(origin + '/api/anime/' + id + '/')).json();
    if (detail.kodik_link) { playable = item.path; break; }
  }
  if (!playable) throw new Error('Public sample has no existing player');
  const browser = page.context().browser();
  const results = [];
  for (const scenario of [
    { name: 'collection-real-posters', path: '/anime/year/2020' },
    { name: 'anime-detail', path: playable },
    { name: 'watch-third-party-blocked', path: playable + '/watch', block: true },
    { name: 'watch-third-party-enabled', path: playable + '/watch' },
  ]) {
    const context = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, serviceWorkers: 'block' });
    const hosts = {}, responseBytesByHost = {}, pendingSizes = [], failures = [], errors = [];
    if (scenario.block) await context.route('**/*', route => {
      const request = route.request();
      return request.isNavigationRequest() && request.frame().parentFrame()
        ? route.abort('blockedbyclient') : route.continue();
    });
    await context.addInitScript(() => {
      window.__mediaLab = { lcpMs: 0, cls: 0, longTasks: 0, longTaskBlockingMs: 0, maxInteractionMs: null };
      for (const type of ['largest-contentful-paint', 'layout-shift', 'longtask', 'event']) {
        try { new PerformanceObserver(list => {
          for (const e of list.getEntries()) {
            const v = window.__mediaLab;
            if (type === 'largest-contentful-paint') v.lcpMs = e.startTime;
            if (type === 'layout-shift' && !e.hadRecentInput) v.cls += e.value;
            if (type === 'longtask') { v.longTasks++; v.longTaskBlockingMs += Math.max(0, e.duration - 50); }
            if (type === 'event' && e.interactionId) v.maxInteractionMs = Math.max(v.maxInteractionMs || 0, e.duration);
          }
        }).observe({ type, buffered: true, durationThreshold: 16 }); } catch { /* Browser support recorded by null. */ }
      }
    });
    const tab = await context.newPage();
    tab.on('pageerror', error => errors.push(error.message));
    tab.on('request', request => {
      const url = new URL(request.url());
      if (!['http:', 'https:'].includes(url.protocol)) return;
      hosts[url.host] = (hosts[url.host] || 0) + 1;
    });
    tab.on('requestfailed', request => failures.push({ host: new URL(request.url()).host, type: request.resourceType(), reason: request.failure()?.errorText }));
    tab.on('requestfinished', request => pendingSizes.push(request.sizes().then(sizes => {
      const host = new URL(request.url()).host;
      responseBytesByHost[host] = (responseBytesByHost[host] || 0) + sizes.responseBodySize;
    }).catch(() => undefined)));
    try {
      const response = await tab.goto(origin + scenario.path, { waitUntil: 'domcontentloaded' });
      await tab.waitForFunction(() => ['standalone', 'app'].includes(document.documentElement.dataset.seoMode), null, { timeout: 45000 });
      if (scenario.path.endsWith('/watch')) await tab.locator('.kodik-iframe').waitFor({ timeout: 45000 });
      await tab.waitForFunction(() => performance.now() >= 12000, null, { timeout: 20000 });
      const metrics = await tab.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        const summary = type => {
          const entries = resources.filter(r => r.initiatorType === type);
          return { count: entries.length, transferBytes: entries.reduce((sum, r) => sum + r.transferSize, 0) };
        };
        const nav = performance.getEntriesByType('navigation')[0];
        return { ...window.__mediaLab, ttfbMs: nav.responseStart, domContentLoadedMs: nav.domContentLoadedEventEnd,
          scripts: summary('script'), images: summary('img'),
          largestImages: resources.filter(r => r.initiatorType === 'img').sort((a, b) => b.transferSize - a.transferSize).slice(0, 3).map(r => ({ host: new URL(r.name).host, bytes: r.transferSize, durationMs: r.duration })),
          posters: [...document.querySelectorAll('.seo-grid img')].map(img => ({ loaded: img.complete && img.naturalWidth > 0, width: img.width, height: img.height })),
          iframeHosts: [...document.querySelectorAll('iframe')].map(frame => { try { return new URL(frame.src).host; } catch { return ''; } }),
          overflow: document.documentElement.scrollWidth > innerWidth + 2,
          robots: document.querySelector('meta[name=robots]')?.content };
      });
      await Promise.allSettled(pendingSizes);
      const observedHosts = { ...hosts }, observedBytes = { ...responseBytesByHost };
      if (scenario.name === 'collection-real-posters') {
        for (const poster of await tab.locator('.seo-grid img').all()) {
          await poster.scrollIntoViewIfNeeded();
          await poster.evaluate(img => img.complete && img.naturalWidth ? true : new Promise((resolve, reject) => {
            img.addEventListener('load', () => resolve(true), { once: true });
            img.addEventListener('error', () => reject(new Error('Public poster failed to load')), { once: true });
          }));
        }
        metrics.lazyPostersLoadedAfterScroll = await tab.locator('.seo-grid img').evaluateAll(images => images.filter(img => img.complete && img.naturalWidth > 0).length);
        await tab.evaluate(() => scrollTo(0, 0));
        await tab.screenshot({ path: 'artifacts/seo/mobile-real-posters.png', fullPage: true });
      }
      results.push({ scenario: scenario.name, path: scenario.path, status: response.status(), metrics, hosts: observedHosts, responseBytesByHost: observedBytes, failures, errors });
    } finally { await context.close(); }
  }
  return { conditions: { viewport: '390x844', serviceWorker: 'blocked', cache: 'fresh browser context per page', throttling: 'none', observationMs: 12000, playback: false, fieldData: null, iframeMetrics: 'Parent LCP/CLS excludes cross-origin iframe content; third-party hosts/requests recorded separately. Cross-origin transfer sizes may be zero without Timing-Allow-Origin.' }, results };
}
