import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import ChatSystemMessage from './ChatSystemMessage.vue';
import type { Message } from '@/types/chat';
const message = { id: 1, sender_id: 5, sender_username: 'Runos', system_target_user: 6,
  message_type: 'system', system_action: 'block', text: '', created_at: '2026-10-11T00:00:00Z' } as unknown as Message;
describe('system chat notices', () => {
  it('renders a distinct notice and explains a historic empty block message to both participants', () => {
    const sender = mount(ChatSystemMessage, { props: { message, userId: 5 } });
    const peer = mount(ChatSystemMessage, { props: { message, userId: 6 } });
    expect(sender.text()).toContain('Вы заблокировали пользователя');
    expect(peer.text()).toContain('Runos заблокировал(а) вас');
    expect(peer.classes()).toContain('chat-system-message--block');
    sender.unmount(); peer.unmount();
  });
});
