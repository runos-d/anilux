/// <reference types="vite/client" />
/// <reference types="vite-plugin-pwa/client" />
/// <reference types="vite-plugin-pwa/vue" />

interface ImportMetaEnv {
  readonly VITE_SCREENSHOT_EXTENSION_ID?: string
  readonly VITE_SCREENSHOT_EXTENSION_INSTALL_URL?: string
  readonly VITE_YANDEX_METRIKA_ENABLED?: string
  readonly VITE_YANDEX_METRIKA_ID?: string
  readonly VITE_GOOGLE_ANALYTICS_ENABLED?: string
  readonly VITE_GOOGLE_ANALYTICS_ID?: string
}
