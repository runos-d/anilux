import { afterEach, beforeEach, expect, it, vi } from 'vitest'
const { api } = vi.hoisted(() => ({ api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() } }))
vi.mock('@/api/client', () => ({ default: api }))
import { enableDevicePush, disableDevicePush, devicePushEnabled, syncDevicePush } from './devicePush'
const subscription = { endpoint: 'https://fcm.googleapis.com/test', toJSON: () => ({ endpoint: 'https://fcm.googleapis.com/test', keys: {} }), unsubscribe: vi.fn(async () => true) }
const manager = { getSubscription: vi.fn(), subscribe: vi.fn() }
const permission = vi.fn()
beforeEach(() => {
  vi.clearAllMocks(); localStorage.clear()
  localStorage.setItem('anilux_user_v1', JSON.stringify({ id: 1 }))
  Object.defineProperty(window, 'isSecureContext', { configurable: true, value: true })
  Object.defineProperty(window, 'Notification', { configurable: true, value: { permission: 'granted', requestPermission: permission } })
  Object.defineProperty(window, 'PushManager', { configurable: true, value: class {} })
  Object.defineProperty(navigator, 'onLine', { configurable: true, value: true })
  Object.defineProperty(navigator, 'serviceWorker', { configurable: true, value: { getRegistration: vi.fn(async () => ({ active: {}, pushManager: manager })) } })
  permission.mockResolvedValue('granted'); manager.getSubscription.mockResolvedValue(null); manager.subscribe.mockResolvedValue(subscription)
  api.get.mockResolvedValue({ data: { enabled: true, public_key: btoa('valid-test-key') } }); api.post.mockResolvedValue({}); api.delete.mockResolvedValue({})
})
afterEach(() => { vi.useRealTimers() })
it('asks permission from the action, stores subscription, and isolates its owner', async () => {
  await enableDevicePush(); expect(permission).toHaveBeenCalledOnce(); expect(api.post).toHaveBeenCalledOnce()
  manager.getSubscription.mockResolvedValue(subscription)
  expect(await devicePushEnabled()).toBe(true)
  localStorage.setItem('anilux_user_v1', JSON.stringify({ id: 2 }))
  expect(await devicePushEnabled()).toBe(false)
  await syncDevicePush(); expect(api.post).toHaveBeenCalledTimes(1)
})
it('unsubscribes locally even if the server is offline', async () => {
  localStorage.setItem('anilux_push_owner_v1', '1'); manager.getSubscription.mockResolvedValue(subscription)
  api.delete.mockRejectedValue(new Error('offline'))
  await expect(disableDevicePush()).rejects.toThrow('offline')
  expect(subscription.unsubscribe).toHaveBeenCalledOnce(); expect(localStorage.getItem('anilux_push_owner_v1')).toBeNull()
})
it('repairs an opted-in subscription without another permission prompt', async () => {
  localStorage.setItem('anilux_push_owner_v1', '1')
  await syncDevicePush(); expect(api.post).toHaveBeenCalledOnce(); expect(permission).not.toHaveBeenCalled()
})
it('does not subscribe when permission is denied or the server is unconfigured', async () => {
  permission.mockResolvedValue('denied'); await expect(enableDevicePush()).rejects.toThrow('Разрешите')
  expect(manager.subscribe).not.toHaveBeenCalled()
  permission.mockResolvedValue('granted'); api.get.mockResolvedValue({ data: { enabled: false } })
  await expect(enableDevicePush()).rejects.toThrow('ещё не настроен'); expect(manager.subscribe).not.toHaveBeenCalled()
})
it('times out a stalled provider and removes a subscription that arrives too late', async () => {
  vi.useFakeTimers(); let complete!: (value: typeof subscription) => void
  manager.subscribe.mockReturnValue(new Promise(resolve => { complete = resolve }))
  const failure = expect(enableDevicePush()).rejects.toThrow('не отвечает')
  await vi.advanceTimersByTimeAsync(20000); await failure
  complete(subscription); await Promise.resolve()
  expect(subscription.unsubscribe).toHaveBeenCalledOnce(); expect(api.post).not.toHaveBeenCalled()
})
