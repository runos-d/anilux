import { afterEach, describe, expect, it, vi } from 'vitest';
import { showBrowserNotification } from './browserNotifications';
describe('system notifications', () => {
  afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
  it('does not send notifications without browser permission', async () => {
    const create = vi.fn(); Object.assign(create, { permission: 'denied' }); vi.stubGlobal('Notification', create);
    await showBrowserNotification({ title: 'Новое сообщение' }); expect(create).not.toHaveBeenCalled();
  });
  it('shows a notification through the service worker and blocks external targets', async () => {
    const create = vi.fn(); Object.assign(create, { permission: 'granted' }); vi.stubGlobal('Notification', create);
    vi.spyOn(document, 'hasFocus').mockReturnValue(false);
    const showNotification = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: {
      getRegistration: vi.fn().mockResolvedValue({ showNotification }),
    } });
    await showBrowserNotification({ title: 'Чат', body: 'Привет', url: '/chats/123', tag: 'message:1' });
    expect(showNotification).toHaveBeenCalledWith('Чат', expect.objectContaining({ body: 'Привет', tag: 'message:1' }));
    await showBrowserNotification({ title: 'Чат', url: 'https://external.test/' });
    expect(showNotification).toHaveBeenCalledTimes(1);
    delete (navigator as unknown as Record<string, unknown>).serviceWorker;
  });
});
