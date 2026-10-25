import { ref } from 'vue'

type Player = { enterPip(): void | Promise<void>; exitPip(): void | Promise<void> }

/** Ask the existing video to enter OS PiP; never create or pause a second player. */
export function createSystemPictureInPicture(getPlayer: () => Player | null | undefined) {
  const active = ref(false), pending = ref(false), error = ref('')
  let timer: ReturnType<typeof setTimeout> | undefined
  let disposed = false
  const clearPending = () => { clearTimeout(timer); timer = undefined; pending.value = false }
  const entered = () => { if(disposed)return; clearPending(); active.value = true; error.value = ''; if(window.aniluxNative?.platform === 'android')document.documentElement.classList.add('anilux-native-pip') }
  const exited = () => { if(disposed)return; clearPending(); active.value = false; error.value = ''; document.documentElement.classList.remove('anilux-native-pip') }
  const nativeState = (event: Event) => {
    const enabled = (event as CustomEvent<unknown>).detail
    if (enabled === true) entered()
    else if (enabled === false) exited()
  }
  window.addEventListener('anilux-native-pip', nativeState)
  const toggle = () => {
    if (pending.value || disposed) return
    const player = getPlayer()
    error.value = ''
    if (!player) { error.value = 'Сначала запустите видео.'; return }
    if (!active.value && document.pictureInPictureEnabled === false && !window.aniluxNative) {
      error.value = 'Этот браузер не поддерживает управление отдельным окном с панели сайта. Используйте значок «Картинка в картинке» внутри видео, если он доступен.'
      return
    }
    pending.value = true
    const entering = !active.value
    timer = setTimeout(() => {
      pending.value = false
      error.value = window.aniluxNative ? 'Окно плеера не ответило. Попробуйте ещё раз.' : entering
        ? 'Нажмите значок «Картинка в картинке» внутри самого видео. Браузер требует нажатия в плеере и может отклонять повторную команду с панели сайта.'
        : 'Нажмите «Вернуть во вкладку» или закройте отдельное окно видео.'
    }, 3000)
    try {
      const result = entering ? player.enterPip() : player.exitPip()
      if(result)void result.then(entering ? entered : exited).catch(() => {
        if(disposed)return
        clearPending();error.value='Не удалось переключить окно плеера. Попробуйте ещё раз.'
      })
    } catch {
      clearPending()
      error.value = 'Не удалось переключить окно плеера. Попробуйте ещё раз.'
    }
  }
  const dispose = () => {
    disposed = true
    const shouldClose = active.value || pending.value
    clearPending()
    window.removeEventListener('anilux-native-pip', nativeState)
    document.documentElement.classList.remove('anilux-native-pip')
    if (shouldClose) {
      try { const result=getPlayer()?.exitPip(); if(result)void result.catch(()=>{}); } catch { /* The native window may already be closed. */ }
    }
    active.value = false
  }
  return { active, pending, error, toggle, entered, exited, dispose }
}
