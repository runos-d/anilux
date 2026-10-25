async page => {
  const browser = page.context().browser();
  const origin = 'http://localhost:5179';
  const api = 'http://localhost:8012/api';
  const report = {}, errors = [];
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const desktop = await browser.newContext({ viewport: { width: 1365, height: 950 },
    timezoneId: 'America/Los_Angeles', serviceWorkers: 'block' });
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 },
    isMobile: true, hasTouch: true, timezoneId: 'Europe/Moscow', serviceWorkers: 'block' });
  try {
    await desktop.addInitScript(() => localStorage.setItem('anime_calendar_view', 'month'));
    const tab = await desktop.newPage();
    tab.on('pageerror', error => errors.push(error.message));
    await tab.goto(origin + '/anime?section=calendar');
    await tab.locator('.cal-sub-month').waitFor();
    await tab.getByRole('button', { name: 'Назад', exact: true }).click();
    await tab.waitForFunction(() => document.querySelector('.cal-sub-month')?.textContent.includes('Сентябрь'));
    await tab.locator('.cal-cell').filter({ has: tab.locator('.cal-cell-num', { hasText: /^30$/ }) }).click();
    await tab.getByText('Сохранённая история', { exact: true }).waitFor();
    check(await tab.locator('.crc-time').textContent() === '16:30', 'Desktop device time did not cross the date boundary');
    const historical = await (await tab.request.get(api + '/anime/calendar/', {
      params: { month: '2026-09', timezone: 'America/Los_Angeles' } })).json();
    check(historical.days.some(day => day.date === '2026-09-10'), 'A disappeared past release was lost');
    report.history = { apiReleases: historical.total, displayedTime: '16:30', month: '2026-09' };
    await tab.getByRole('textbox', { name: 'Поиск по календарю' }).fill('Сохранённая история');
    await tab.locator('.cal-search-results .crc').waitFor();
    check((await tab.locator('.cal-search-results .crc-time').textContent()) === '16:30', 'History search lost device timezone');
    const pending = await (await tab.request.get(api + '/anime/calendar/', { params: { month: '2099-01' } })).json();
    check(pending.days.flatMap(day => day.items).some(item => item.schedule_uncertain), 'Disappeared future release is not marked');

    await tab.goto(origin + '/anime?section=recommendations');
    const button = tab.locator('.reason-btn').first();
    await button.waitFor();
    await button.hover();
    await tab.getByRole('tooltip').waitFor();
    report.desktopReason = await tab.getByRole('tooltip').textContent();
    check(report.desktopReason.includes('Проверочный фильм 0'), 'The explanation is not title-specific');
    await tab.screenshot({ path: '.playwright-cli/calendar-recommendations-desktop.png' });
    await tab.keyboard.press('Escape');
    await tab.getByRole('tooltip').waitFor({ state: 'hidden' });
    await button.focus();
    await tab.getByRole('tooltip').waitFor();
    await tab.keyboard.press('Tab');
    await tab.getByRole('tooltip').waitFor({ state: 'hidden' });
    const films = await (await tab.request.get(api + '/anime/home/personalized/', { params: { sections: 'movies' } })).json();
    check(films.movies.length === 1 && films.movies[0].kind === 'movie' && films.movies[0].episodes === 1,
      'Multi-episode or unknown films survived the real API');
    report.movies = films.movies.map(row => ({ title: row.title, episodes: row.episodes }));
    const filmBlock = tab.locator('.rec-block').filter({ has: tab.locator('.rc-title', { hasText: 'Полнометражные' }) });
    await filmBlock.scrollIntoViewIfNeeded();
    await filmBlock.locator('.rec-card-wrap').waitFor();
    check(await filmBlock.locator('.rec-card-wrap').count() === 1, 'The film UI contains an ineligible title');

    const phone = await mobile.newPage();
    phone.on('pageerror', error => errors.push(error.message));
    await phone.goto(origin + '/anime?section=calendar');
    await phone.getByText('Сохранённая история', { exact: true }).waitFor();
    check(await phone.locator('.crc-time').textContent() === '02:30', 'Phone timezone did not move release to October 1');
    report.mobileTime = '02:30';
    await phone.getByRole('textbox', { name: 'Поиск по календарю' }).fill('Будущий релиз');
    await phone.getByText('Расписание уточняется', { exact: true }).waitFor();
    report.uncertain = 'future release remains visible with a schedule warning';
    await phone.goto(origin + '/anime?section=recommendations');
    const touchButton = phone.locator('.reason-btn').first();
    await touchButton.waitFor();
    await touchButton.tap();
    await phone.getByRole('tooltip').waitFor();
    const box = await phone.getByRole('tooltip').boundingBox();
    check(box.x >= 0 && box.x + box.width <= 390, 'Tooltip extends outside the phone viewport');
    report.mobileReason = await phone.getByRole('tooltip').textContent();
    await phone.screenshot({ path: '.playwright-cli/calendar-recommendations-mobile.png' });
    await touchButton.tap();
    await phone.getByRole('tooltip').waitFor({ state: 'hidden' });
    await touchButton.tap();
    await phone.locator('.rc-title').first().tap();
    await phone.getByRole('tooltip').waitFor({ state: 'hidden' });
    check(phone.url().includes('recommendations'), 'Tapping the explanation navigated away from the card');
    report.keyboard = 'focus opens; Escape and Tab close';
    report.touch = 'tap opens; repeat tap and outside tap close';
    check(errors.length === 0, 'Browser JavaScript errors: ' + errors.join('; '));
    return { ...report, errors };
  } finally {
    await desktop.close();
    await mobile.close();
  }
}
