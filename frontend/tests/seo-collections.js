async page => {
  const origin = 'http://localhost:8096';
  const browser = page.context().browser(), results = [], errors = [];
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  for (const theme of ['dark', 'polnochnaya', 'light']) for (const width of [1365, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 900 }, serviceWorkers: 'block' });
    await context.addInitScript(theme => localStorage.setItem('appearance:v1', JSON.stringify({ s: { theme }, o: {} })), theme);
    const tab = await context.newPage();
    tab.on('pageerror', error => errors.push(error.message));
    const ready = async count => {
      await tab.locator('.seo-collection .afb').waitFor({ timeout: 45000 });
      await tab.waitForFunction(count => document.querySelectorAll('.seo-collection .anime-card').length === count, count, { timeout: 30000 });
      const metadata = await (await tab.request.get(origin + '/api/seo/page/', { params: { path: new URL(tab.url()).pathname + new URL(tab.url()).search } })).json();
      await tab.waitForFunction(titles => JSON.stringify([...document.querySelectorAll('.seo-collection .anime-title')].map(element => element.textContent.trim())) === JSON.stringify(titles), metadata.items.map(item => item.name), { timeout: 30000 });
    };
    try {
      for (const path of ['/anime/browse', '/anime/year/2025', '/anime/genre/romance', '/anime/type/tv', '/anime/status/finished', '/anime/season/2025/winter', '/anime/collection/romance-2025']) {
        await tab.goto(origin + path, { waitUntil: 'domcontentloaded' });
        await ready(24);
        await tab.locator('.seo-navigation-panel').waitFor();
        check(await tab.locator('.collection-header h1').count() === 1, 'Missing collection header ' + path);
        check(await tab.getByTitle('Перемешать', { exact: true }).count() === 1, 'Missing shuffle ' + path);
        check(!(await tab.evaluate(() => document.documentElement.scrollWidth > innerWidth + 2)), 'Overflow ' + path);
        results.push({ theme, width, path, catalogControls: true });
      }
      await tab.goto(origin + '/anime/year/2025', { waitUntil: 'domcontentloaded' });
      await ready(24);
      const original = await tab.locator('.seo-collection .anime-title').allTextContents();
      await tab.locator('.afb-genre-chip').filter({ hasText: /^Редкий$/ }).click();
      await ready(4);
      check(new URL(tab.url()).searchParams.get('genres') === 'Редкий', 'Genre absent from URL');
      const filteredTitles = await tab.locator('.seo-collection .anime-title').allTextContents();
      await tab.reload({ waitUntil: 'domcontentloaded' });
      await ready(4);
      check(JSON.stringify(filteredTitles) === JSON.stringify(await tab.locator('.seo-collection .anime-title').allTextContents()), 'Reload lost genre');
      await tab.locator('.seo-collection .anime-card').first().click();
      await tab.locator('.anime-detail-card').waitFor();
      await tab.goBack({ waitUntil: 'domcontentloaded' });
      await ready(4);
      await tab.locator('.afb-genre-chip.active').filter({ hasText: /^Редкий$/ }).waitFor();
      await tab.locator('.afb-genre-chip.active').filter({ hasText: /^Редкий$/ }).click();
      await ready(24);
      const input = tab.getByPlaceholder('Поиск аниме по названию...');
      await input.fill('несуществующее');
      await ready(0);
      check(await input.evaluate(element => document.activeElement === element), 'Search lost focus after response');
      check(await tab.getByText('Ничего не найдено', { exact: true }).count() === 1, 'Missing empty state');
      await input.fill('');
      await ready(24);
      await tab.locator('.afb-select').first().selectOption('title_ru');
      await tab.waitForURL(/ordering=title_ru/);
      await ready(24);
      await tab.getByTitle('Перемешать', { exact: true }).click();
      await tab.waitForURL(/shuffle=true/);
      await tab.waitForFunction(() => document.querySelector('[title="Перемешать"]')?.getAttribute('aria-pressed') === 'true');
      await tab.waitForFunction(previous => JSON.stringify([...document.querySelectorAll('.seo-collection .anime-title')].map(el => el.textContent)) !== JSON.stringify(previous), original);
      await ready(24);
      const shuffled = await tab.locator('.seo-collection .anime-title').allTextContents();
      await tab.reload({ waitUntil: 'domcontentloaded' });
      await ready(24);
      check(JSON.stringify(shuffled) === JSON.stringify(await tab.locator('.seo-collection .anime-title').allTextContents()), 'Shuffle seed lost on reload');
      await tab.getByRole('button', { name: 'Следующая страница', exact: true }).click();
      await ready(6);
      const second = await tab.locator('.seo-collection .anime-title').allTextContents();
      check(!second.some(title => shuffled.includes(title)), 'Shuffle pagination repeats titles');
      await tab.reload({ waitUntil: 'domcontentloaded' });
      await ready(6);
      check(JSON.stringify(second) === JSON.stringify(await tab.locator('.seo-collection .anime-title').allTextContents()), 'Page 2 changed after reload');
      await tab.getByTitle('Обновить', { exact: true }).click();
      await ready(24);
      check(!new URL(tab.url()).searchParams.has('shuffle'), 'Reset did not restore sorting');
      await tab.locator('.afb-select-sm').selectOption('20');
      await ready(20);
      await tab.getByRole('button', { name: 'Следующая страница', exact: true }).click();
      await ready(10);
      check(await tab.locator('.pagination-info').innerText().then(text => text.includes('Страница 2 из 2')), 'Wrong page size count');
      await tab.screenshot({ path: 'artifacts/seo/collection-' + theme + '-' + width + '.png', fullPage: false });
      results.push({ theme, width, searchFocus: true, genreReloadBack: true, sorting: true, stableShuffle: true, paginationReload: true, pageSize: true });
    } catch (error) {
      await tab.screenshot({ path: 'artifacts/seo/collection-failure.png', fullPage: false });
      throw new Error(JSON.stringify({ error: String(error), theme, width, url: tab.url(), body: (await tab.locator('main').innerText()).slice(0, 1500), errors }));
    } finally { await context.close(); }
  }
  check(!errors.length, errors.join('; '));
  return { origin, checks: results.length, results, errors };
}
