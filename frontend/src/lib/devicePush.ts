import api from '@/api/client'
const OWNER = 'anilux_push_owner_v1'
const owner = () => {
  try { return String(JSON.parse(localStorage.getItem('anilux_user_v1') || '{}').id || '') }
  catch { return '' }
}
async function currentSubscription() {
  if (!('serviceWorker' in navigator)) return null
  const reg = await navigator.serviceWorker.getRegistration()
  return reg?.pushManager?.getSubscription().catch(() => null) ?? null
}
export async function devicePushEnabled() {
  return Boolean(owner() && localStorage.getItem(OWNER) === owner() && await currentSubscription())
}
export async function enableDevicePush() {
  if (!window.isSecureContext || !('Notification' in window) || !('PushManager' in window))
    throw new Error('Этот браузер не поддерживает уведомления. На iPhone откройте установленное приложение.')
  if (!owner()) throw new Error('Войдите в аккаунт.')
  const permission = await Notification.requestPermission()
  if (permission !== 'granted') throw new Error('Разрешите уведомления в настройках браузера или устройства.')
  await registerDevicePush()
}
async function registerDevicePush() {
  const account = owner()
  const { data } = await api.get('/notifications/push/config/', { timeout: 10000 })
  if (!data.enabled || !data.public_key) throw new Error('Сервер уведомлений ещё не настроен.')
  const reg = await navigator.serviceWorker.getRegistration()
  if (!reg?.active) throw new Error('Приложение ещё загружается. Попробуйте через несколько секунд.')
  const raw = atob(data.public_key.replace(/-/g, '+').replace(/_/g, '/'))
  const key = Uint8Array.from(raw, character => character.charCodeAt(0))
  const subscription = await reg.pushManager.getSubscription() || await subscribeWithTimeout(reg.pushManager, key)
  try {
    if (!account || owner() !== account) throw new Error('Аккаунт изменился.')
    await api.post('/notifications/push/subscription/', subscription.toJSON(), { timeout: 10000 })
    if (owner() !== account) throw new Error('Аккаунт изменился.')
    localStorage.setItem(OWNER, account)
  } catch {
    await subscription.unsubscribe().catch(() => false)
    throw new Error('Не удалось сохранить подписку. Проверьте сеть и попробуйте ещё раз.')
  }
}
function subscribeWithTimeout(manager: PushManager, key: Uint8Array<ArrayBuffer>): Promise<PushSubscription> {
  return new Promise((resolve, reject) => {
    let expired = false
    const timer = window.setTimeout(() => {
      expired = true
      reject(new Error('Сервер браузерных уведомлений не отвечает. Попробуйте позже.'))
    }, 20000)
    manager.subscribe({ userVisibleOnly: true, applicationServerKey: key }).then(subscription => {
      clearTimeout(timer)
      if (expired) void subscription.unsubscribe().catch(() => false)
      else resolve(subscription)
    }, () => {
      clearTimeout(timer)
      reject(new Error('Браузер не смог создать подписку. Проверьте разрешение и подключение.'))
    })
  })
}
export async function disableDevicePush() {
  const subscription = await currentSubscription()
  if (subscription) {
    try { await api.delete('/notifications/push/subscription/', {
      data: { endpoint: subscription.endpoint }, timeout: 5000, _keepOnNavigation: true,
    }) } finally {
      await subscription.unsubscribe()
      localStorage.removeItem(OWNER)
    }
  } else localStorage.removeItem(OWNER)
}
export async function detachDevicePushOnLogout() {
  if (!localStorage.getItem(OWNER)) return
  try { await disableDevicePush() } catch { /* Local unsubscribe still runs on network failure. */ }
}
/** Restore opted-in/rotated subscriptions on foreground without asking for permission. */
export async function syncDevicePush() {
  if (!navigator.onLine || !owner() || localStorage.getItem(OWNER) !== owner() ||
      !('Notification' in window) || Notification.permission !== 'granted') return
  try { await registerDevicePush() } catch { /* The application page offers a manual retry. */ }
}
