import { mount, flushPromises } from '@vue/test-utils';
import { createMemoryHistory, createRouter } from 'vue-router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PlaylistsView from './PlaylistsView.vue';

const { getAllPlaylists } = vi.hoisted(() => ({ getAllPlaylists: vi.fn() }));
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: null, isAuthenticated: false }) }));
vi.mock('@/api/client', () => ({ default: { get: vi.fn() } }));
vi.mock('@/composables/useCachedReads', () => ({ useCachedReads: () => vi.fn() }));
vi.mock('@/api/playlists', () => ({ default: {
  getAllPlaylists,
} }));

beforeEach(() => { vi.clearAllMocks(); });
const result = (title: string) => ({ data: { count: 1, results: [{ id: title, title, items_count: 0, updated_at: '2026-10-15', visibility: 'public' }] } });
async function setup(url: string) {
  const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/playlists', component: PlaylistsView }, { path: '/playlist/:id', component: { template: '<div>detail</div>' } }] });
  await router.push(url);
  await router.isReady();
  const wrapper = mount(PlaylistsView, { global: { plugins: [router], stubs: { PlaylistCard: { props: ['playlist'], template: '<p class="test-card">{{ playlist.title }}</p>' }, SakuraIcon: true } } });
  await flushPromises();
  return { wrapper, router };
}

describe('public discovery state', () => {
  it('ignores a superseded response and no longer sends removed topic and genre filters', async () => {
    let oldResponse!: (value: unknown) => void;
    getAllPlaylists.mockImplementationOnce(() => new Promise(resolve => { oldResponse = resolve; })).mockResolvedValueOnce(result('Актуальный'));
    const { wrapper, router } = await setup('/playlists?tab=public');
    await router.replace('/playlists?tab=public&search=космос&topics=cozy&genres=Драма&publicSort=-likes_count&period=week&page=2');
    await flushPromises();
    expect(getAllPlaylists).toHaveBeenLastCalledWith(expect.objectContaining({ is_public: true, search: 'космос', ordering: '-likes_count', period: 'week', page: 2 }));
    expect(getAllPlaylists.mock.calls.at(-1)?.[0]).not.toHaveProperty('topics');
    expect(getAllPlaylists.mock.calls.at(-1)?.[0]).not.toHaveProperty('genre');
    expect(wrapper.get('.test-card').text()).toBe('Актуальный');
    oldResponse(result('Запоздавший'));
    await flushPromises();
    expect(wrapper.get('.test-card').text()).toBe('Актуальный');
    wrapper.unmount();
  });

  it('resets pagination when filters change, retains state on back, and hides public controls in my playlists', async () => {
    getAllPlaylists.mockResolvedValue(result('Подборка'));
    const { wrapper, router } = await setup('/playlists?tab=public&page=3&period=month');
    await wrapper.get('.public-controls select').setValue('title');
    await flushPromises();
    expect(router.currentRoute.value.query.page).toBe('1');
    expect(router.currentRoute.value.query.publicSort).toBe('title');
    const saved = router.currentRoute.value.fullPath;
    await router.push('/playlist/1');
    router.back();
    await flushPromises();
    expect(router.currentRoute.value.fullPath).toBe(saved);
    await wrapper.findAll('.tab-btn')[0]!.trigger('click');
    await flushPromises();
    expect(wrapper.find('.public-controls').exists()).toBe(false);
    expect(getAllPlaylists).toHaveBeenLastCalledWith(expect.objectContaining({ my: true, ordering: '-updated_at' }));
    wrapper.unmount();
  });
});
