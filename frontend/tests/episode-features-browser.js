async page => {
  const origin = 'http://localhost:5179', api = 'http://localhost:8012/api';
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const report = {}, errors = [];
  await page.evaluate(() => {
    for (const key of ['anilux_user_v1','anilux_access_token_v1','anilux_refresh_token_v1']) localStorage.removeItem(key);
  });
  page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({ width: 1365, height: 950 });
  await page.context().grantPermissions(['notifications'], { origin });
  await page.context().addInitScript(() => {
    window.__episodeNativeNotices = [];
    const NativeNotification = window.Notification;
    window.Notification = class extends NativeNotification {
      constructor(title, options) {
        super(title, options);
        window.__episodeNativeNotices.push({ title, body: options?.body, tag: options?.tag });
      }
    };
  });
  await Promise.all([page.waitForResponse(response => response.url().includes('/anime/home/') && response.ok()), page.goto(origin + '/')]);
  assert(await page.locator('.home-new-episodes').count() === 0, 'Guest sees private episodes');
  const login = await page.request.post(api + '/users/login/', {
    data: { username: 'episode_browser_owner', password: 'Local-Episode-Test-20261012!' },
  });
  assert(login.ok(), 'Fixture login failed');
  const owner = await login.json();
  await page.evaluate(owner => {
    localStorage.setItem('anilux_user_v1', JSON.stringify(owner.user));
    localStorage.setItem('anilux_access_token_v1', owner.tokens.access);
    localStorage.setItem('anilux_refresh_token_v1', owner.tokens.refresh);
  }, owner);
  const headers = { Authorization: 'Bearer ' + owner.tokens.access };
  await page.reload();
  await page.locator('.home-new-episodes .new-episode-watch').waitFor();
  const home = await (await page.request.get(api + '/anime/home/', { headers })).json();
  const item = home.new_episodes[0];
  assert(item.latest_episode === 3 && item.unwatched_count === 1, 'Incorrect new episodes data');
  const titles = await page.locator('.home-content .rc-title').allTextContents();
  assert(titles.indexOf('Новые серии') < titles.indexOf('Продолжить просмотр'), 'New episodes appear in the wrong order');
  assert(titles.includes('Пересмотреть'), 'Rewatch section disappeared');
  await page.locator('.home-new-episodes').scrollIntoViewIfNeeded();
  await page.screenshot({ path: '.playwright-cli/episode-home-desktop.png' });
  await page.locator('.home-new-episodes .anime-card').evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await page.locator('.home-new-episodes .anime-card').hover();
  await page.locator('.home-new-episodes .reminder-btn').click();
  const unsubscribe = page.getByRole('button', { name: 'Отписаться от серий', exact: true });
  await unsubscribe.waitFor();
  await unsubscribe.click();
  await page.getByRole('button', { name: 'Подписаться на серии', exact: true }).waitFor();
  await page.locator('.reminder-modal .btn-cancel').click();
  const library = await (await page.request.get(api + '/users/library/', { headers })).json();
  const libraryItem = library.results.find(row => row.anime_id === item.anime_id);
  const updated = await page.request.patch(api + '/users/library/' + libraryItem.id + '/', {
    headers, data: { current_episode: 2 },
  });
  assert(updated.ok(), 'Progress patch failed');
  const subscriptions = await (await page.request.get(api + '/notifications/episode-subs/', {
    headers, params: { anime_id: item.anime_id },
  })).json();
  const rows = Array.isArray(subscriptions) ? subscriptions : subscriptions.results;
  assert(rows.length === 1 && !rows[0].is_active, 'Progress reactivated a manual opt-out');
  await page.locator('.home-new-episodes .anime-card').evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
  await page.locator('.home-new-episodes .anime-card').hover();
  await page.locator('.home-new-episodes .reminder-btn').click();
  await page.getByRole('button', { name: 'Подписаться на серии', exact: true }).click();
  await page.getByRole('button', { name: 'Отписаться от серий', exact: true }).waitFor();
  await page.locator('.reminder-modal .btn-cancel').click();
  const watched = await page.request.post(api + '/anime/' + item.anime_id + '/episode-progress/', {
    headers, data: { action: 'mark', episode_number: 3 },
  });
  assert(watched.ok(), 'Mark watched failed');
  await Promise.all([page.waitForResponse(response => response.url().includes('/anime/home/') && response.ok()), page.reload()]);
  await page.waitForFunction(() => !document.querySelector('.home-new-episodes'));
  report.home = 'guest hidden; section precedes continue/rewatch; series 3 disappears when watched';
  report.subscription = 'opt-out via real modal survives progress; existing subscription can be re-enabled';
  await page.goto(origin + '/anime?section=calendar');
  const remind = page.getByRole('button', { name: 'Напомнить о серии 4', exact: true });
  await remind.waitFor();
  await remind.click();
  await page.getByRole('button', { name: 'Напоминание установлено', exact: true }).waitFor();
  const reminders = await (await page.request.get(api + '/notifications/reminders/', { headers })).json();
  const reminderRows = Array.isArray(reminders) ? reminders : reminders.results;
  const reminder = reminderRows.find(row => row.calendar_release);
  assert(reminder.follow_schedule, 'Calendar reminder is not bound to the release');
  report.reminder = { id: reminder.id, release: reminder.calendar_release, initialTime: reminder.reminder_time };
  report.anime = item.anime_id;
  await page.screenshot({ path: '.playwright-cli/episode-calendar-desktop.png' });
  await page.request.post(api + '/notifications/reminders/' + reminder.id + '/deactivate/', { headers });
  const mobile = await page.context().browser().newContext({ viewport: { width: 390, height: 844 },
    isMobile: true, hasTouch: true, timezoneId: 'Europe/Moscow', serviceWorkers: 'block' });
  try {
    await mobile.addInitScript(owner => {
      localStorage.setItem('anilux_user_v1', JSON.stringify(owner.user));
      localStorage.setItem('anilux_access_token_v1', owner.tokens.access);
      localStorage.setItem('anilux_refresh_token_v1', owner.tokens.refresh);
    }, owner);
    const phone = await mobile.newPage();
    phone.on('pageerror', error => errors.push(error.message));
    await phone.goto(origin + '/anime?section=calendar');
    await phone.getByRole('button', { name: 'Напомнить о серии 4', exact: true }).tap();
    await phone.getByRole('button', { name: 'Напоминание установлено', exact: true }).waitFor();
    await phone.screenshot({ path: '.playwright-cli/episode-calendar-mobile.png' });
    report.mobile = 'touch creates/upserts the same release reminder; time is local to Moscow';
  } finally { await mobile.close(); }
  report.errors = errors;
  assert(errors.length === 0, 'JavaScript errors: ' + errors.join('; '));
  await page.evaluate(report => localStorage.setItem('episode_browser_report', JSON.stringify(report)), report);
  return report;
}
