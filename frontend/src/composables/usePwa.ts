import { computed, ref } from 'vue'
import { registerSW } from 'virtual:pwa-register'

interface InstallEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const online = ref(navigator.onLine)
const installed = ref(window.matchMedia('(display-mode: standalone)').matches ||
  Boolean((navigator as Navigator & { standalone?: boolean }).standalone))
const installEvent = ref<InstallEvent | null>(null)
const needsRefresh = ref(false)
const offlineReady = ref(false)
const error = ref('')
const updating = ref(false)
let registration: ServiceWorkerRegistration | undefined
let applyUpdate: ((reloadPage?: boolean) => Promise<void>) | undefined
let started = false
let reloadRequested = false

function reloadApplication() {
  if (reloadRequested) return
  reloadRequested = true
  location.reload()
  window.setTimeout(() => { reloadRequested = false }, 1000)
}

function observeInstallation(reg: ServiceWorkerRegistration) {
  const observed = new WeakSet<ServiceWorker>()
  const failure = () => {
    offlineReady.value = Boolean(reg.active && reg.active.state !== 'redundant')
    error.value = reg.active
      ? 'Не удалось загрузить обновление. Проверьте соединение и повторите проверку.'
      : 'Не удалось сохранить файлы приложения. Проверьте соединение и свободное место на устройстве.'
  }
  const observe = () => {
    const worker = reg.installing
    if (!worker || observed.has(worker)) return
    observed.add(worker)
    let activated = worker.state === 'activated'
    const changed = () => {
      if (worker.state === 'activated') activated = true
      if (worker.state !== 'redundant' || activated) return
      if (reg.installing && reg.installing !== worker || reg.waiting && reg.waiting !== worker) return
      failure()
    }
    worker.addEventListener('statechange', changed)
    changed()
  }
  observe()
  reg.addEventListener('updatefound', observe)
  window.setTimeout(() => {
    if (!reg.active && !reg.waiting && !reg.installing) failure()
  }, 1000)
}

export function startPwa() {
  if (started) return
  started = true
  window.addEventListener('online', () => { online.value = true; void checkUpdate() })
  window.addEventListener('offline', () => { online.value = false })
  window.addEventListener('beforeinstallprompt', event => {
    event.preventDefault()
    installEvent.value = event as InstallEvent
  })
  window.addEventListener('appinstalled', () => { installed.value = true; installEvent.value = null })
  const mode = window.matchMedia('(display-mode: standalone)')
  mode.addEventListener('change', event => { installed.value = event.matches })
  if (!('serviceWorker' in navigator) || !window.isSecureContext) return
  applyUpdate = registerSW({
    immediate: true,
    onNeedReload: reloadApplication,
    onNeedRefresh: () => { needsRefresh.value = true; error.value = '' },
    onOfflineReady: () => { offlineReady.value = true; error.value = '' },
    onRegisteredSW: (_url, reg) => {
      registration = reg
      if (reg?.active) offlineReady.value = true
      if (reg) observeInstallation(reg)
      if (reg?.active) void checkUpdate()
    },
    onRegisterError: () => { error.value = 'Не удалось подготовить приложение. Проверьте соединение и перезагрузите страницу.' },
  })
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') void checkUpdate()
  })
  window.setInterval(() => {
    if (document.visibilityState === 'visible') void checkUpdate()
  }, 60 * 60 * 1000)
}

async function checkUpdate() {
  if (!online.value || !registration || registration.installing) return
  try {
    await registration.update()
    if (registration.active || registration.installing || registration.waiting) error.value = ''
  } catch {
    error.value = 'Не удалось проверить обновления. Проверьте соединение и попробуйте ещё раз.'
  }
}

function retryPreparation() {
  if (online.value) window.location.reload()
}

async function install() {
  error.value = ''
  const event = installEvent.value
  if (!event) return
  try {
    await event.prompt()
    await event.userChoice
    installEvent.value = null
  } catch { error.value = 'Браузер не смог открыть установку. Попробуйте через его меню.' }
}

async function update() {
  if (!online.value || updating.value || !applyUpdate) return
  updating.value = true
  error.value = ''
  let timer: ReturnType<typeof window.setTimeout> | undefined
  let changed: (() => void) | undefined
  try {
    if (needsRefresh.value && registration?.active && !registration.waiting && !registration.installing) {
      reloadApplication()
      return
    }
    const previous = navigator.serviceWorker.controller
    const activated = new Promise<void>((resolve, reject) => {
      changed = () => {
        if (!navigator.serviceWorker.controller || navigator.serviceWorker.controller === previous) return
        reloadApplication()
        resolve()
      }
      navigator.serviceWorker.addEventListener('controllerchange', changed)
      timer = window.setTimeout(() => reject(new Error('Activation timed out')), 15000)
    })
    void activated.catch(() => undefined)
    await applyUpdate(true)
    await activated
  }
  catch { error.value = 'Обновление не удалось. Попробуйте ещё раз.' }
  finally {
    if (timer !== undefined) clearTimeout(timer)
    if (changed) navigator.serviceWorker.removeEventListener('controllerchange', changed)
    updating.value = false
  }
}

export function usePwa() {
  return { online, installed, canInstall: computed(() => Boolean(installEvent.value) && !installed.value),
    needsRefresh, offlineReady, error, updating, install, update, checkUpdate, retryPreparation }
}
