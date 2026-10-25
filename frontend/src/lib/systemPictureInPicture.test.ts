import { afterEach, expect, it, vi } from 'vitest'
import { createSystemPictureInPicture } from './systemPictureInPicture'
afterEach(() => { vi.useRealTimers(); delete (document as unknown as Record<string, unknown>).pictureInPictureEnabled })
it('uses the existing player and confirms OS events without pausing or replacing it', () => {
  const player = { enterPip: vi.fn(), exitPip: vi.fn(), pause: vi.fn() }
  const pip = createSystemPictureInPicture(() => player)
  pip.toggle(); expect(player.enterPip).toHaveBeenCalledOnce()
  expect(pip.active.value).toBe(false); expect(pip.pending.value).toBe(true)
  pip.entered(); expect(pip.active.value).toBe(true)
  pip.toggle(); expect(player.exitPip).toHaveBeenCalledOnce(); pip.exited()
  expect(pip.active.value).toBe(false); expect(player.pause).not.toHaveBeenCalled()
  pip.dispose()
})
it('reports a rejected/unsupported transition instead of opening a website overlay', () => {
  vi.useFakeTimers()
  const pip = createSystemPictureInPicture(() => ({ enterPip() {}, exitPip() {} }))
  pip.toggle(); vi.advanceTimersByTime(3000)
  expect(pip.pending.value).toBe(false); expect(pip.active.value).toBe(false); expect(pip.error.value).toContain('внутри самого видео')
  Object.defineProperty(document, 'pictureInPictureEnabled', { configurable: true, value: false })
  pip.toggle(); expect(pip.error.value).toContain('не поддерживает')
  pip.dispose()
})
it('clears the timeout even when the player confirms synchronously, for repeated cycles', () => {
  vi.useFakeTimers()
  const pip = createSystemPictureInPicture(() => ({ enterPip: () => pip.entered(), exitPip: () => pip.exited() }))
  for (let i=0;i<3;i++) {
    pip.toggle(); expect(pip.active.value).toBe(true)
    vi.advanceTimersByTime(6000); expect(pip.error.value).toBe('')
    pip.toggle(); expect(pip.active.value).toBe(false)
    vi.advanceTimersByTime(6000); expect(pip.error.value).toBe('')
  }
  pip.dispose()
})
it('tracks native host confirmations and the Android system close button', async () => {
  const pip = createSystemPictureInPicture(() => ({ enterPip: () => Promise.resolve(), exitPip: () => Promise.resolve() }))
  pip.toggle(); await Promise.resolve(); expect(pip.active.value).toBe(true)
  window.dispatchEvent(new CustomEvent('anilux-native-pip', {detail:false}))
  expect(pip.active.value).toBe(false)
  pip.toggle(); await Promise.resolve(); expect(pip.active.value).toBe(true)
  pip.dispose()
  window.dispatchEvent(new CustomEvent('anilux-native-pip', {detail:true}))
  expect(pip.active.value).toBe(false)
})
it('closes a pending native transition and ignores its late confirmation on navigation', async () => {
  let confirm!: () => void
  const player = { enterPip: () => new Promise<void>(resolve => {confirm=resolve}), exitPip: vi.fn() }
  const pip = createSystemPictureInPicture(() => player)
  pip.toggle(); pip.dispose(); confirm(); await Promise.resolve()
  expect(player.exitPip).toHaveBeenCalledOnce()
  expect(pip.active.value).toBe(false)
  expect(pip.error.value).toBe('')
})
it('closes native PiP on disposal and cancels pending timers', () => {
  vi.useFakeTimers(); const player = { enterPip: vi.fn(), exitPip: vi.fn() }
  const pip = createSystemPictureInPicture(() => player)
  pip.toggle(); pip.entered(); pip.dispose(); vi.advanceTimersByTime(5000)
  expect(player.exitPip).toHaveBeenCalledOnce(); expect(pip.error.value).toBe('')
})
