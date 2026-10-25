import { mount } from '@vue/test-utils';
import { describe, it, expect, vi } from 'vitest';
import { nextTick } from 'vue';
import VirtualChatTimeline from './VirtualChatTimeline.vue';
import { mergeMessages } from '@/lib/chatTimeline';

describe('long chat histories', () => {
  it('defers row resizing to a frame and uses the measured offset when navigating', async () => {
    let observer: ResizeObserverCallback;
    let frame: FrameRequestCallback;
    vi.stubGlobal('ResizeObserver', class {
      constructor(callback: ResizeObserverCallback) { observer = callback; }
      observe() {} disconnect() {}
    });
    vi.stubGlobal('requestAnimationFrame', vi.fn(callback => { frame = callback; return 1; }));
    vi.stubGlobal('cancelAnimationFrame', vi.fn());
    const element = document.createElement('div');
    Object.defineProperty(element, 'clientHeight', { value: 100 });
    Object.defineProperty(element, 'scrollHeight', { value: 1000 });
    const wrapper = mount(VirtualChatTimeline, { props: { messages: [{id:1,created_at:'2026-10-13'},{id:2,created_at:'2026-10-13'}], scrollElement: element } });
    await nextTick(); await nextTick();
    const row = wrapper.find('[data-timeline-id="1"]').element;
    vi.spyOn(row, 'getBoundingClientRect').mockReturnValue({ height: 160 } as DOMRect);
    observer!([{ target: row } as ResizeObserverEntry], {} as ResizeObserver);
    await wrapper.vm.scrollToMessage(2);
    expect(element.scrollTop).toBe(46);
    frame!(0); await nextTick(); await nextTick();
    await wrapper.vm.scrollToMessage(2);
    expect(element.scrollTop).toBe(110);
    wrapper.unmount(); vi.unstubAllGlobals();
  });
  it('keeps the bubble DOM node when HTTP and WebSocket acknowledge a pending message', async () => {
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
    const pending = { id: -1, sender_id: 7, client_message_id: 'stable-command', seq: 0, created_at: '2026-10-10' };
    const wrapper = mount(VirtualChatTimeline, { props: { messages: [pending] }, slots: { default: '<span>{{ params.message.id }}</span>' } });
    await nextTick();
    const bubble = wrapper.find('[data-timeline-id="-1"]').element;
    const ack = { ...pending, id: 150, seq: 23 };
    let messages = mergeMessages([pending], [ack]);
    await wrapper.setProps({ messages });
    expect(wrapper.find('[data-timeline-id="150"]').element).toBe(bubble);
    messages = mergeMessages(messages, [ack]);
    await wrapper.setProps({ messages });
    expect(wrapper.findAll('[data-timeline-id]')).toHaveLength(1);
    expect(wrapper.find('[data-timeline-id="150"]').element).toBe(bubble);
    wrapper.unmount(); vi.unstubAllGlobals();
  });
  it('renders a bounded window and reaches an offscreen message', async () => {
    vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
    const element = document.createElement('div');
    Object.defineProperty(element, 'clientHeight', { value: 600 });
    const messages = Array.from({ length: 5000 }, (_, index) => ({ id: index + 1, seq: index + 1, created_at: '2026-10-09' }));
    const wrapper = mount(VirtualChatTimeline, { props: { messages, scrollElement: element }, slots: { default: '<span>{{ params.message.id }}</span>' } });
    vi.spyOn(wrapper.element, 'getBoundingClientRect').mockImplementation(() => ({ top: -element.scrollTop, height: 600 } as DOMRect));
    await nextTick(); await nextTick();
    expect(wrapper.findAll('[data-timeline-id]').length).toBeLessThan(50);
    await wrapper.vm.scrollToMessage(4500);
    await nextTick();
    expect(wrapper.find('[data-timeline-id="4500"]').exists()).toBe(true);
    expect(wrapper.findAll('[data-timeline-id]').length).toBeLessThan(50);
    wrapper.unmount(); vi.unstubAllGlobals();
  });
});
