import { mount, flushPromises } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import PlaylistCard from './PlaylistCard.vue';

const { push, setLike, auth } = vi.hoisted(() => ({ push: vi.fn(), setLike: vi.fn(), auth: { isAuthenticated: true, user: { id: 2 } } }));
vi.mock('vue-router', () => ({ useRouter: () => ({ push }), useRoute: () => ({ fullPath: '/playlists?tab=public&period=week' }) }));
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }));
vi.mock('@/api/playlists', () => ({ default: { setLike } }));
vi.mock('@/api/client', () => ({ getMediaUrl: (url: string) => url }));
const playlist = { id: '00000123', title: 'Длинное название', description: 'Описание', items_count: 4, likes_count: 2, favorites_count: 9, is_liked: false, updated_at: '2026-10-15', user_id: 1, visibility: 'public' as const };

beforeEach(() => { vi.clearAllMocks(); auth.isAuthenticated = true; });

describe('playlist likes', () => {
  it('reacts optimistically, prevents rapid duplicate requests, and keeps favorite totals distinct', async () => {
    let resolve!: (data: unknown) => void;
    setLike.mockImplementation(() => new Promise(done => { resolve = done; }));
    const wrapper = mount(PlaylistCard, { props: { playlist } });
    const button = wrapper.get('.playlist-like');
    await button.trigger('click');
    expect(button.attributes('aria-pressed')).toBe('true');
    expect(button.attributes('aria-busy')).toBe('true');
    expect(button.text()).toBe('3');
    await button.trigger('click');
    expect(setLike).toHaveBeenCalledTimes(1);
    expect(push).not.toHaveBeenCalled();
    expect(wrapper.get('.playlist-meta').text()).toContain('9');
    resolve({ data: { is_liked: true, likes_count: 3 } });
    await flushPromises();
    expect(button.text()).toBe('3');
    expect(button.attributes('disabled')).toBeUndefined();
    wrapper.unmount();
  });

  it('rolls back after failure and can retry a removal', async () => {
    setLike.mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: { is_liked: false, likes_count: 1 } });
    const wrapper = mount(PlaylistCard, { props: { playlist: { ...playlist, is_liked: true } } });
    await wrapper.get('.playlist-like').trigger('click');
    await flushPromises();
    expect(wrapper.get('.playlist-like').attributes('aria-pressed')).toBe('true');
    expect(wrapper.get('.playlist-like').text()).toBe('2');
    expect(wrapper.get('[role=alert]').text()).toContain('не сохранён');
    await wrapper.get('.playlist-like').trigger('click');
    await flushPromises();
    expect(setLike).toHaveBeenLastCalledWith('00000123', false);
    expect(wrapper.get('.playlist-like').text()).toBe('1');
    expect(wrapper.find('[role=alert]').exists()).toBe(false);
    wrapper.unmount();
  });

  it('offers guests login with the current discovery URL', async () => {
    auth.isAuthenticated = false;
    const wrapper = mount(PlaylistCard, { props: { playlist } });
    await wrapper.get('.playlist-like').trigger('click');
    expect(push).toHaveBeenCalledWith({ path: '/login', query: { redirect: '/playlists?tab=public&period=week' } });
    expect(setLike).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it('does not expose like actions on private or link-only cards', () => {
    for (const visibility of ['private', 'link'] as const) {
      const wrapper = mount(PlaylistCard, { props: { playlist: { ...playlist, visibility } } });
      expect(wrapper.find('.playlist-like').exists()).toBe(false);
      wrapper.unmount();
    }
  });
});
