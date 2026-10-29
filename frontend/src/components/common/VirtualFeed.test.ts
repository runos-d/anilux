import { afterEach, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { nextTick } from 'vue';
import VirtualFeed from './VirtualFeed.vue';

afterEach(() => { vi.unstubAllGlobals(); });
it('keeps a long feed bounded and renders the correct window after scrolling', async () => {
  vi.stubGlobal('ResizeObserver', class { observe() {} disconnect() {} });
  const items = Array.from({ length: 1000 }, (_, id) => ({ id }));
  const wrapper = mount(VirtualFeed, { props: { items }, slots: { default: '<p>{{ params.item.id }}</p>' } });
  await nextTick();
  expect(wrapper.findAll('[data-feed-key]').length).toBeLessThan(12);
  vi.spyOn(wrapper.element, 'getBoundingClientRect').mockReturnValue({ top: -40000 } as DOMRect);
  window.dispatchEvent(new Event('scroll'));
  await new Promise(resolve => setTimeout(resolve, 30));
  await nextTick();
  expect(Number(wrapper.find('[data-feed-key]').attributes('data-feed-key'))).toBeGreaterThan(60);
  expect(wrapper.findAll('[data-feed-key]').length).toBeLessThan(12);
  wrapper.unmount();
});
