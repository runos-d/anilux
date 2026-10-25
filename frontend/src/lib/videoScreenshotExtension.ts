export type ScreenshotExtensionResponse = {
  ok: boolean
  error?: string
  width?: number
  height?: number
}

type ChromeRuntime = {
  lastError?: { message?: string }
  sendMessage(
    extensionId: string,
    message: Record<string, unknown>,
    callback: (response?: ScreenshotExtensionResponse) => void,
  ): void
}

const extensionId = import.meta.env.VITE_SCREENSHOT_EXTENSION_ID?.trim() ?? ''
const configuredInstallUrl = import.meta.env.VITE_SCREENSHOT_EXTENSION_INSTALL_URL?.trim() ?? ''

export const screenshotExtensionInstallUrl = configuredInstallUrl
  || (extensionId ? `https://chromewebstore.google.com/detail/${extensionId}` : '')

export class ScreenshotExtensionUnavailableError extends Error {}

function getRuntime(): ChromeRuntime | undefined {
  return (window as typeof window & { chrome?: { runtime?: ChromeRuntime } }).chrome?.runtime
}

function sendMessage(message: Record<string, unknown>): Promise<ScreenshotExtensionResponse> {
  const runtime = getRuntime()
  if (!extensionId || !runtime?.sendMessage) {
    return Promise.reject(new ScreenshotExtensionUnavailableError('Расширение для скриншотов не установлено.'))
  }

  return new Promise((resolve, reject) => {
    try {
      runtime.sendMessage(extensionId, message, (response) => {
        const runtimeError = runtime.lastError
        if (runtimeError || !response) {
          reject(new ScreenshotExtensionUnavailableError(runtimeError?.message || 'Расширение не ответило.'))
          return
        }
        resolve(response)
      })
    } catch (error) {
      reject(new ScreenshotExtensionUnavailableError(error instanceof Error ? error.message : 'Расширение недоступно.'))
    }
  })
}

export async function captureVideoScreenshot(): Promise<ScreenshotExtensionResponse> {
  const ping = await sendMessage({ type: 'ANILUX_SCREENSHOT_PING' })
  if (!ping.ok) throw new ScreenshotExtensionUnavailableError(ping.error || 'Расширение не ответило.')

  const result = await sendMessage({ type: 'ANILUX_CAPTURE_VIDEO_FRAME' })
  if (!result.ok) throw new Error(result.error || 'Не удалось сделать скриншот.')
  return result
}
