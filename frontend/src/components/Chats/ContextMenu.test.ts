import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ContextMenu from './ContextMenu.vue';
import ChatListItem from './ChatListItem.vue';

afterEach(() => vi.restoreAllMocks());

describe('chat list actions', () => {
  it('opens actions by a button without selecting the chat', async () => {
    const wrapper = mount(ChatListItem, {
      props: { chat: { id: 1, type: 'private', name: 'Чат', unreadCount: 0, isPinned: false, isArchived: false, isMuted: false }, isActive: false },
      global: { stubs: { OptimizedImage: true } },
    });
    await wrapper.get('button[aria-label="Действия чата Чат"]').trigger('click');
    expect(wrapper.emitted('contextmenu')).toHaveLength(1);
    expect(wrapper.emitted('click')).toBeUndefined();
    wrapper.unmount();
  });

  it('bounds a menu near the viewport corner and closes on Escape', async () => {
    vi.spyOn(HTMLElement.prototype, 'getBoundingClientRect').mockReturnValue({ x: 0, y: 0, width: 280, height: 180, top: 0, right: 280, bottom: 180, left: 0, toJSON: () => ({}) });
    const wrapper = mount(ContextMenu, { props: { isOpen: false, x: 10000, y: 10000 }, attachTo: document.body });
    await wrapper.setProps({ isOpen: true });
    await flushPromises();
    const menu = document.querySelector<HTMLElement>('.context-menu')!;
    expect(Number.parseFloat(menu.style.left)).toBe(Math.max(12, window.innerWidth - 292));
    expect(Number.parseFloat(menu.style.top)).toBe(Math.max(12, window.innerHeight - 192));
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }));
    expect(wrapper.emitted('close')).toHaveLength(1);
    wrapper.unmount();
  });
});
