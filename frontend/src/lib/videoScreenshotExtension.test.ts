import { afterEach, describe, expect, it, vi } from 'vitest'

const originalChrome = (window as typeof window & { chrome?: unknown }).chrome

afterEach(() => {
  Object.defineProperty(window, 'chrome', { configurable: true, value: originalChrome })
  vi.unstubAllEnvs()
  vi.resetModules()
})

describe('video screenshot extension bridge', () => {
  it('reports an unavailable extension when the browser bridge is missing', async () => {
    vi.stubEnv('VITE_SCREENSHOT_EXTENSION_ID', 'test-extension-id')
    const { captureVideoScreenshot, ScreenshotExtensionUnavailableError } = await import('./videoScreenshotExtension')
    Object.defineProperty(window, 'chrome', { configurable: true, value: undefined })
    await expect(captureVideoScreenshot()).rejects.toBeInstanceOf(ScreenshotExtensionUnavailableError)
  })

  it('pings before requesting a captured frame', async () => {
    vi.stubEnv('VITE_SCREENSHOT_EXTENSION_ID', 'test-extension-id')
    const { captureVideoScreenshot } = await import('./videoScreenshotExtension')
    const messages: string[] = []
    const sendMessage = vi.fn((_id: string, message: { type: string }, callback: (response: { ok: boolean }) => void) => {
      messages.push(message.type)
      callback({ ok: true })
    })
    Object.defineProperty(window, 'chrome', {
      configurable: true,
      value: { runtime: { sendMessage } },
    })

    await expect(captureVideoScreenshot()).resolves.toMatchObject({ ok: true })
    expect(messages).toEqual(['ANILUX_SCREENSHOT_PING', 'ANILUX_CAPTURE_VIDEO_FRAME'])
  })
})
