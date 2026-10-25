async page => {
  const api = 'http://localhost:8012/api';
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const report = await page.evaluate(() => JSON.parse(localStorage.getItem('episode_browser_report')));
  const headers = { Authorization: await page.evaluate(() => 'Bearer ' + localStorage.getItem('anilux_access_token_v1')) };
  const response = await page.request.get(api + '/notifications/reminders/' + report.reminder.id + '/', { headers });
  const reminder = await response.json();
  assert(reminder.calendar_release === report.reminder.release && reminder.reminder_time !== report.reminder.initialTime,
    'Moved release did not update the same reminder');
  report.reminder.movedTime = reminder.reminder_time;
  await page.evaluate(() => {
    let Native = window.Notification;
    for (let index = 0; index < 10 && !Function.prototype.toString.call(Native).includes('[native code]'); index++) {
      const parent = Object.getPrototypeOf(Native);
      if (typeof parent !== 'function' || parent === Function.prototype) break;
      Native = parent;
    }
    window.__episodeNativeNotices = [];
    window.__episodeWsEvents = [];
    window.Notification = class extends Native {
      constructor(title, options) {
        super(title, options);
        window.__episodeNativeNotices.push({ title, body: options?.body, tag: options?.tag });
      }
    };
    if (window.__episodeWsObserver) window.removeEventListener('newNotification', window.__episodeWsObserver);
    window.__episodeWsObserver = event => window.__episodeWsEvents.push(event.detail);
    window.addEventListener('newNotification', window.__episodeWsObserver);
  });
  const focus = await page.context().newPage();
  await focus.goto('about:blank');
  await focus.bringToFront();
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: false });
  const background = await page.evaluate(() => ({ hidden: document.hidden, focus: document.hasFocus(), permission: Notification.permission }));
  assert(background.hidden || !background.focus, 'The notification page is still in focus');
  assert(background.permission === 'granted', 'Native browser notifications were not authorized in the test context');
  await page.evaluate(report => localStorage.setItem('episode_browser_report', JSON.stringify(report)), report);
  return { movedReminder: report.reminder, background, waitingFor: 'delay and available from real WS transport' };
}
