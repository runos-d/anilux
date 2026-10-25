import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
const { reportPost, openAuthModal } = vi.hoisted(() => ({
  reportPost: vi.fn().mockResolvedValue({ data: { message: 'Жалоба отправлена' } }),
  openAuthModal: vi.fn(),
}));
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: { id:1,username:'admin' }, isAuthenticated: true }) }));
vi.mock('@/stores/modal', () => ({ useModalStore: () => ({ openAuthModal }) }));
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
vi.mock('@/api/client', () => ({ default: { get: vi.fn().mockResolvedValue({data:{}}) } }));
vi.mock('@/api/feed', () => ({ postsApi: { reportPost }, followsApi: {} }));
import PostMenu from './PostMenu.vue';

describe('post moderator menu', () => {
  it('retains non-owner actions when an administrator can delete somebody else’s post', () => {
    const wrapper = mount(PostMenu, { props: { post: {id:2,text:'Post',author:3,author_username:'reader',can_edit:false,can_delete:true,is_pinned:false,is_bookmarked:false} } });
    expect(wrapper.text()).toContain('Удалить');
    expect(wrapper.text()).toContain('Подписаться');
    expect(wrapper.text()).toContain('Пожаловаться'); wrapper.unmount();
  });

  it('submits a post complaint through the unified reports API', async () => {
    const wrapper = mount(PostMenu, { props: { post: {id:42,text:'Post',author:3,author_username:'reader',can_edit:false,can_delete:false,is_pinned:false,is_bookmarked:false} } });
    await wrapper.get('.menu-item.warn').trigger('click');
    await wrapper.get('.reason-btn').trigger('click');
    await wrapper.get('.btn-confirm-delete').trigger('click');
    expect(reportPost).toHaveBeenCalledWith(42, 'spam', '');
    wrapper.unmount();
  });
});
