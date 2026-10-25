import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ref } from 'vue';
import HomeView from './HomeView.vue';

const auth = { user: { id: 1 } as { id: number } | null, isAuthenticated: true };
const push = vi.fn();
const data = ref<Record<string, unknown>>();
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }));
vi.mock('@tanstack/vue-query', () => ({ useQuery: () => ({ data, isError: ref(false), isPending: ref(false), refetch: vi.fn() }) }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));
vi.mock('@/api/anime', () => ({ animeApi: {} }));
vi.mock('@/api/client', () => ({ getMediaUrl: (url: string) => url }));
const item = { anime_id: 1, id: 1, slug: 'new-episode-test', title: 'Новые серии', poster: '', genres: [],
  year: 2026, rating: 8, status: 'ongoing', latest_episode: 3, unwatched_count: 1, next_episode: 3 };
const options = { global: { stubs: {
  AnimeCard: true, HomeHero: true,
  RecCarousel: { props: ['title', 'anime'], template: '<section :data-title="title"><slot name="card" v-for="item in anime" :item="item" /></section>' },
} } };
beforeEach(() => {
  auth.isAuthenticated = true; auth.user = { id: 1 }; push.mockClear();
  data.value = { new_episodes: [item], continue_watching: [item], rewatch: [item], recommendations: [], trending: [] };
});

describe('home newly available episodes', () => {
  it('precedes continue watching and shows an actual episode, unseen count and watch action', async () => {
    const wrapper = mount(HomeView, options);
    const sections = wrapper.findAll('section[data-title]').map(section => section.attributes('data-title'));
    expect(sections.indexOf('Новые серии')).toBeLessThan(sections.indexOf('Продолжить просмотр'));
    expect(sections).toContain('Пересмотреть');
    expect(wrapper.get('.new-episode-count').text()).toContain('серия 3');
    expect(wrapper.get('.new-episode-count').text()).toContain('Не просмотрено: 1');
    await wrapper.get('.new-episode-watch').trigger('click');
    expect(push).toHaveBeenCalledWith('/anime/new-episode-test/watch?episode=3');
    wrapper.unmount();
  });
  it('hides this private section for a guest even if an old cached payload contains episodes', () => {
    auth.isAuthenticated = false; auth.user = null;
    const wrapper = mount(HomeView, options);
    expect(wrapper.find('.home-new-episodes').exists()).toBe(false);
    wrapper.unmount();
  });
  it('removes the section after the API reports all available episodes watched', async () => {
    const wrapper = mount(HomeView, options);
    data.value = { ...data.value, new_episodes: [] };
    await wrapper.vm.$nextTick();
    expect(wrapper.find('.home-new-episodes').exists()).toBe(false);
    wrapper.unmount();
  });
});
