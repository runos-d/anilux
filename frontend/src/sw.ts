/// <reference lib="webworker" />

import { CacheFirst, NetworkOnly } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { registerRoute } from 'workbox-routing'
import { isPrivateCachePath } from './lib/privateMediaCache'

const publicResponseOnly = {
  cacheWillUpdate: async ({ response }: { response: Response }) =>
    (response.status === 200 || response.type === 'opaque') &&
    !/no-store|private/i.test(response.headers.get('Cache-Control') || '') ? response : null,
}

declare const self: ServiceWorkerGlobalScope & {
    __WB_MANIFEST: Array<{ url: string; revision: string | null }>
  }

cleanupOutdatedCaches()
precacheAndRoute(self.__WB_MANIFEST.filter(entry => !(typeof entry === 'string' ? entry : entry.url).endsWith('.html')))

registerRoute(
  ({ request, url }) =>
    !request.headers.has('Authorization') && !isPrivateCachePath(url.pathname) && (
      request.destination === 'image' ||
      /\.(?:png|jpe?g|gif|webp|avif|svg|ico)$/i.test(url.pathname)
    ),
  new CacheFirst({
    cacheName: 'images-cache',
    plugins: [
      publicResponseOnly,
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 60 * 60 * 24 * 30,
        purgeOnQuotaError: true,
      }),
    ],
  }),
)

registerRoute(
  ({ request, url }) => !request.headers.has('Authorization') && !isPrivateCachePath(url.pathname) && /\.(?:woff2?|ttf|otf)$/i.test(url.pathname),
  new CacheFirst({
    cacheName: 'fonts-cache',
    plugins: [
      publicResponseOnly,
      new ExpirationPlugin({
        maxEntries: 30,
        maxAgeSeconds: 60 * 60 * 24 * 60,
        purgeOnQuotaError: true,
      }),
    ],
  }),
)

registerRoute(({ request }) => request.mode === 'navigate', new NetworkOnly())

self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') void self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const name of await caches.keys()) {
      if (name === 'api-cache' || name === 'pages-cache' || /^anilux-v\d+$/.test(name)) {
        await caches.delete(name)
        continue
      }
      const cache = await caches.open(name)
      for (const request of await cache.keys()) {
        if (isPrivateCachePath(new URL(request.url).pathname)) await cache.delete(request)
      }
    }
    await self.clients.claim()
  })())
})

self.addEventListener('push', (event) => {
  let data: { title?: string; content?: string; body?: string; tag?: string; link?: string } = {}
  try { data = event.data?.json() || {} } catch { data.body = event.data?.text() || '' }
  const title = data.title || 'AniLux'
  const options = {
    body: data.content || data.body || '',
    icon: '/pwa/icon-192.png',
    tag: data.tag || 'anilux',
    data: { url: data.link || '/' },
    requireInteraction: false,
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const target = new URL(event.notification.data?.url || '/', self.location.origin)
  const url = target.origin === self.location.origin ? target.href : self.location.origin + '/'
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (client.url === url) {
          return client.focus()
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(url)
    })
  )
})

self.addEventListener('pushsubscriptionchange', () => {
  console.warn('Push subscription changed -resubscribe needed')
})
