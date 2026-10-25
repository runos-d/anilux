import { afterEach, expect, it, vi } from 'vitest';
import { flushPromises, shallowMount } from '@vue/test-utils';
const mocks = vi.hoisted(() => ({ get: vi.fn() }));
vi.mock('@/api/client', () => ({ default: { get: mocks.get }, getMediaUrl: (url: string) => url }));
vi.mock('@/api/anime', () => ({ default: { list: vi.fn() } }));
import AttachModal from './AttachModal.vue';
afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });
it('loads owned playlists when opened directly on the playlist tab', async () => {
  vi.useFakeTimers();
  mocks.get.mockResolvedValue({ data: [{ id: '00000021', title: 'Мой плейлист', anime_count: 0 }] });
  const wrapper = shallowMount(AttachModal, { props: {
    modelValue: 'playlist', selectedAnimes: [], selectedPlaylists: [], selectedMediaFiles: [],
  } });
  await vi.advanceTimersByTimeAsync(300);
  await flushPromises();
  expect(mocks.get).toHaveBeenCalledWith('/playlists/playlists/my/');
  expect(wrapper.findAll('.playlist-result')).toHaveLength(1);
  expect(wrapper.text()).toContain('Мой плейлист');
  await wrapper.find('.playlist-result').trigger('click');
  expect(wrapper.emitted('update:selectedPlaylists')?.[0]?.[0]).toEqual([
    { id: '00000021', title: 'Мой плейлист', anime_count: 0 },
  ]);
  wrapper.unmount();
});
