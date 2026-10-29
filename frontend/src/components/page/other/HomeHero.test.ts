import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, expect, it, vi } from 'vitest';
const get = vi.hoisted(() => vi.fn().mockResolvedValue({ description: 'Description' }));
const push = vi.hoisted(() => vi.fn());
vi.mock('@/api/anime', () => ({ animeApi: { get } }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));
vi.mock('@/api/client', () => ({ getMediaUrl: (url: string) => url }));
import HomeHero from './HomeHero.vue';
import type { RecommendationItem } from '@/types';
afterEach(() => vi.clearAllMocks());
it('loads only the visible slide and starts a new title at episode one', async () => {
  const wrapper = mount(HomeHero, { props: { animeList: [
    { anime_id: 1, slug: 'one', title: 'One', episodes: 12, genres: [] },
    { anime_id: 2, slug: 'two', title: 'Two', episodes: 24, genres: [] },
  ] as unknown as RecommendationItem[] }, global: { stubs: {
    AnimeCard: { template: '<button @click="$emit(\'watch\')">watch</button>' },
  } } });
  await flushPromises();
  expect(get).toHaveBeenCalledTimes(1);
  await wrapper.get('button').trigger('click');
  // The arrow changes the visible title; it does not preload the whole list.
  await flushPromises();
  expect(get.mock.calls.length).toBeLessThanOrEqual(2);
  await wrapper.findAll('button').find(button => button.text() === 'watch')!.trigger('click');
  expect(push).toHaveBeenCalledWith(expect.stringMatching(/episode=1$/));
  wrapper.unmount();
});
