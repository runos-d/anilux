export type BrowserAttention = { title: string; body?: string; url?: string; tag?: string };

export async function showBrowserNotification(item: BrowserAttention): Promise<void> {
  if (!('Notification' in window) || Notification.permission !== 'granted' || (!document.hidden && document.hasFocus())) return;
  const target = new URL(item.url || '/notifications', location.origin);
  if (target.origin !== location.origin) return;
  const options = { body: item.body, tag: item.tag, icon: '/favicon.ico', data: { url: target.href } };
  try {
    const registration = await navigator.serviceWorker?.getRegistration();
    if (registration) { await registration.showNotification(item.title, options); return; }
    const notification = new Notification(item.title, options);
    notification.onclick = () => { window.focus(); location.assign(target.href); notification.close(); };
  } catch { /* Unsupported or disabled system notification service. */ }
}
