import { ref, onMounted, onBeforeUnmount } from 'vue'
import type { AxiosInstance } from 'axios'

export function useNotificationRead(id: number, api: AxiosInstance) {
  const visible = ref(false)
  let observer: IntersectionObserver | null = null
  let timer: ReturnType<typeof setTimeout> | undefined
  const el = ref<HTMLElement | null>(null)
  const markRead = async () => {
    if (!visible.value) return
    try {
      await api.post(`/notifications/notifications/${id}/mark_read/`)
    } catch {
      // A later visibility/intersection event will retry without breaking the page.
    }
  }
  const handleVisibilityChange = () => {
    if (!document.hidden) {
      visible.value = true
      void markRead()
    }
  }
  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange)
    observer = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting && e.intersectionRatio >= 0.5) {
          visible.value = true
          clearTimeout(timer)
          timer = window.setTimeout(() => void markRead(), 1000)
        } else {
          visible.value = false
          clearTimeout(timer)
        }
      }
    }, { threshold: 0.5 })
    if (el.value) observer.observe(el.value)
  })
  onBeforeUnmount(() => {
    observer?.disconnect()
    if (timer !== undefined) clearTimeout(timer)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  })
  return { el, visible }
}
