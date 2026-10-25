async page => {
  const assert = (value, message) => { if (!value) throw new Error(message); };
  await page.waitForFunction(() => window.__episodeWsEvents?.some(item => item.type === 'episode_available'));
  await page.waitForFunction(() => window.__episodeNativeNotices?.length >= 2);
  const delivery = await page.evaluate(() => ({ events: [...new Map(window.__episodeWsEvents.map(item => [item.id, item])).values()].map(item => ({ id: item.id, type: item.type, title: item.title, link: item.link })),
    native: window.__episodeNativeNotices }));
  assert(delivery.events.filter(item => item.type === 'episode_delayed').length === 1, 'Repeated delayed WS notices');
  assert(delivery.events.filter(item => item.type === 'episode_available').length === 1, 'Repeated available WS notices');
  assert(delivery.native.length === 2, 'Repeated native browser notifications');
  assert(delivery.events.find(item => item.type === 'episode_delayed').link.indexOf('/watch') === -1, 'Delay suggests an unavailable player');
  const headers = { Authorization: await page.evaluate(() => 'Bearer ' + localStorage.getItem('anilux_access_token_v1')) };
  const api = 'http://localhost:8012/api';
  const report = await page.evaluate(() => JSON.parse(localStorage.getItem('episode_browser_report')));
  const reminder = await (await page.request.get(api + '/notifications/reminders/' + report.reminder.id + '/', { headers })).json();
  assert(!reminder.is_active && reminder.available_notified_at, 'Available series reminder did not complete');
  report.delivery = delivery;
  await page.bringToFront();
  await page.goto('http://localhost:5179/');
  await page.locator('.home-new-episodes .new-episode-watch').waitFor();
  assert((await page.locator('.new-episode-count').textContent()).includes('серия 4'), 'Next hosted episode did not return to the home page');
  await page.evaluate(report => localStorage.setItem('episode_browser_report', JSON.stringify(report)), report);
  return report;
}
