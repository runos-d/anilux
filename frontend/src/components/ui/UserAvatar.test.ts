import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import UserAvatar from './UserAvatar.vue';

describe('avatar fallback', () => {
  it('shows SVG on image failure and retries a changed source', async () => {
    const wrapper = mount(UserAvatar, { props: { src: 'https://fixture.test/broken.png' } });
    await wrapper.get('img').trigger('error');
    expect(wrapper.find('img').exists()).toBe(false);
    expect(wrapper.find('.avatar-placeholder svg').exists()).toBe(true);
    await wrapper.setProps({ src: 'https://fixture.test/replacement.png' });
    expect(wrapper.get('img').attributes('src')).toBe('https://fixture.test/replacement.png');
    wrapper.unmount();
  });
});
