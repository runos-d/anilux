import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
vi.mock('@unpic/vue', () => ({ Image: { props: ['src'], emits: ['error'], template: '<img :src="src" @error="$emit(\'error\', $event)">' } }));
import OptimizedImage from './OptimizedImage.vue';

describe('content image fallback', () => {
  it('keeps caller error handling, renders SVG and retries a new URL', async () => {
    const wrapper = mount(OptimizedImage, { props: { src: '/broken.jpg', alt: 'Постер', width: 180, height: 270 } });
    await wrapper.get('img').trigger('error');
    expect(wrapper.emitted('error')).toHaveLength(1);
    expect(wrapper.get('[role="img"]').attributes('aria-label')).toBe('Постер');
    expect(wrapper.find('svg').exists()).toBe(true);
    await wrapper.setProps({ src: '/replacement.jpg' });
    expect(wrapper.get('img').attributes('src')).toBe('/replacement.jpg');
    wrapper.unmount();
  });
});
