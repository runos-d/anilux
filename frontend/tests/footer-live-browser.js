async page => {
  const origin = 'http://localhost:8080';
  const expected = await (await page.request.get(origin + '/site-navigation.json')).json();
  const count = expected.groups.flatMap(group => group.links).length;
  const catalog = await (await page.request.get(origin + '/api/seo/page/', { params: { path: '/anime' } })).json();
  const result = [];
  for (const path of ['/contacts', '/terms', '/privacy', '/license', '/anime', catalog.items[0].path]) {
    const data = await (await page.request.get(origin + '/api/seo/page/', { params: { path } })).json();
    await page.goto(origin + path);
    await page.waitForFunction(() => document.documentElement.dataset.seoMode === 'app');
    await page.waitForFunction(title => document.title === title, data.title);
    const links = await page.locator('footer.seo-navigation a[href^="/"]').count();
    if (links !== count || await page.locator('head link[rel=canonical]').count() !== 1) throw new Error('Live footer/head ' + path);
    result.push({ path, title: await page.title(), links });
  }
  await page.locator('footer a[href="/privacy"]').click();
  await page.waitForURL('**/privacy');
  await page.getByRole('heading', { name: 'Политика конфиденциальности', exact: true }).waitFor();
  return { origin, pages: result, legalNavigation: true };
}
