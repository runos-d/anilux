import { onMounted, onUnmounted, ref } from 'vue'
import apiClient from '@/api/client'

export interface NativeArtifact {
  platform: string
  label: string
  status: string
  url: string | null
  size: number | null
  sha256: string | null
}
export interface NativeRelease { version?: string; status: string; artifacts: NativeArtifact[] }

export function useNativeReleases() {
  const release = ref<NativeRelease>({ status: 'loading', artifacts: [] })
  const error = ref('')
  let timer: ReturnType<typeof setTimeout> | undefined
  let disposed = false
  const controller = new AbortController()
  async function load() {
    clearTimeout(timer)
    error.value = ''
    try {
      const { data } = await apiClient.get<NativeRelease>('/application/releases/', { signal: controller.signal })
      if (disposed) return
      release.value = data
      if (['queued', 'building'].includes(data.status)) timer = setTimeout(() => void load(), 15000)
    } catch {
      if (!disposed) error.value = 'Не удалось загрузить установочные файлы. Попробуйте ещё раз.'
    }
  }
  onMounted(() => void load())
  onUnmounted(() => { disposed = true; controller.abort(); clearTimeout(timer) })
  return { release, error, load }
}

export function installerSize(bytes: number | null) {
  return bytes ? `${(bytes / 1024 / 1024).toLocaleString('ru-RU', { maximumFractionDigits: 1 })} МБ` : ''
}
