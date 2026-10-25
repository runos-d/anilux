import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { afterEach, expect, it, vi } from 'vitest'
import { useNativeReleases } from './useNativeReleases'

const { get } = vi.hoisted(() => ({get: vi.fn()}))
vi.mock('@/api/client', () => ({default: {get}}))
afterEach(() => { vi.useRealTimers(); vi.clearAllMocks() })
const component = defineComponent({setup: useNativeReleases, template: '<div>{{ release.status }} {{ error }}</div>'})
const settle = async () => { await Promise.resolve(); await Promise.resolve() }

it('polls during compilation and stops when the installers are ready', async () => {
  vi.useFakeTimers()
  get.mockResolvedValueOnce({data: {status:'building', artifacts:[]}})
    .mockResolvedValueOnce({data: {status:'ready', artifacts:[{platform:'windows',status:'ready',url:'/api/application/releases/one/app.exe'}]}})
  const wrapper=mount(component); await settle()
  expect(wrapper.text()).toContain('building')
  await vi.advanceTimersByTimeAsync(15000)
  expect(wrapper.text()).toContain('ready')
  await vi.advanceTimersByTimeAsync(45000)
  expect(get).toHaveBeenCalledTimes(2)
  wrapper.unmount()
})
it('cancels requests and timers when the visitor leaves the page', async () => {
  vi.useFakeTimers()
  get.mockResolvedValue({data:{status:'building',artifacts:[]}})
  const wrapper=mount(component); await settle()
  const signal=get.mock.calls[0]![1].signal as AbortSignal
  wrapper.unmount(); expect(signal.aborted).toBe(true)
  await vi.advanceTimersByTimeAsync(30000)
  expect(get).toHaveBeenCalledOnce()
})
it('shows a recoverable error when the release service is unavailable', async () => {
  get.mockRejectedValue(new Error('offline'))
  const wrapper=mount(component); await settle()
  expect(wrapper.text()).toContain('Не удалось загрузить')
  wrapper.unmount()
})
