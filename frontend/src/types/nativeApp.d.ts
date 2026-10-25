export {}
declare global {
  interface Window {
    aniluxNative?: {platform: 'desktop'|'android'|'ios'; setPictureInPicture(enabled: boolean): Promise<void>}
  }
}
