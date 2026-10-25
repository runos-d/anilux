import { defineComponent, onMounted } from 'vue';
import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import AttachmentStack from './AttachmentStack.vue';

describe('AttachmentStack', () => {
  it('keeps slotted cards mounted while collapsing and expanding', async () => {
    const mounted = vi.fn();
    const Card = defineComponent({
      setup() { onMounted(mounted); },
      template: '<article class="test-card">Карточка</article>',
    });
    const wrapper = mount(AttachmentStack, {
      props: { count: 1, posters: [], label: 'Аниме' },
      slots: { default: Card },
      global: { stubs: { SakuraIcon: true, OptimizedImage: true } },
    });

    expect(mounted).toHaveBeenCalledTimes(1);
    await wrapper.get('.stack-toggle').trigger('click');
    await wrapper.get('.stack-toggle').trigger('click');
    await wrapper.get('.stack-preview').trigger('click');

    expect(mounted).toHaveBeenCalledTimes(1);
    expect(wrapper.get('.test-card').isVisible()).toBe(true);
  });
});
