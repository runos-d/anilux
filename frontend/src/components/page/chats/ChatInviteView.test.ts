import { mount, flushPromises } from '@vue/test-utils';
import { reactive } from 'vue';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ChatInviteView from './ChatInviteView.vue';

const auth = reactive({ isAuthenticated: false, checkAuth: vi.fn() });
const route = reactive({ params: { token: 'valid-invite-token' }, fullPath: '/chats/invite/valid-invite-token' });
const join = vi.fn(), push = vi.fn(), openAuthModal = vi.fn();
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }));
vi.mock('@/stores/chatExtras', () => ({ useChatExtrasStore: () => ({ joinByToken: join }) }));
vi.mock('@/stores/groupChat', () => ({ useGroupChatStore: () => ({ restoreGroupChatToList: vi.fn() }) }));
vi.mock('@/stores/modal', () => ({ useModalStore: () => ({ openAuthModal }) }));
vi.mock('vue-router', () => ({ useRoute: () => route, useRouter: () => ({ push }) }));
vi.mock('@/api/client', () => ({ default: {} }));

describe('direct chat invitations', () => {
  beforeEach(() => {
    vi.clearAllMocks(); localStorage.clear(); auth.isAuthenticated = false;
    auth.checkAuth.mockImplementation(async () => { auth.isAuthenticated = true; });
    join.mockResolvedValue({ status: 'joined', chat_id: 81234567, chat_name: 'Группа' });
  });

  it('restores authentication after the initial navigation and joins exactly once', async () => {
    localStorage.setItem('anilux_access_token_v1', 'test-access');
    const wrapper = mount(ChatInviteView, { global: { stubs: { SakuraIcon: true } } });
    await flushPromises();
    expect(auth.checkAuth).toHaveBeenCalledOnce();
    expect(join).toHaveBeenCalledExactlyOnceWith('valid-invite-token');
    await wrapper.find('.btn-go-chat').trigger('click');
    expect(push).toHaveBeenCalledWith({ path: '/chats/81234567', query: { type: 'group' } });
    wrapper.unmount();
  });

  it('keeps the invite while logging in and gives immediate access to the chat', async () => {
    const wrapper = mount(ChatInviteView, { global: { stubs: { SakuraIcon: true } } });
    await flushPromises();
    expect(join).not.toHaveBeenCalled();
    await wrapper.find('.btn-join').trigger('click');
    expect(push).toHaveBeenCalledWith({ path: '/login', query: { redirect: '/chats/invite/valid-invite-token' } });
    auth.isAuthenticated = true;
    await flushPromises();
    expect(join).toHaveBeenCalledExactlyOnceWith('valid-invite-token');
    expect(wrapper.text()).not.toContain('Заявка отправлена');
    expect(wrapper.find('.btn-go-chat').exists()).toBe(true);
    wrapper.unmount();
  });
});
