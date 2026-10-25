import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import PlaylistCover from './PlaylistCover.vue';
import PlaylistTopicPicker from './PlaylistTopicPicker.vue';
vi.mock('@/api/client', () => ({ getMediaUrl: (url: string) => url }));
const choices = [
  { slug: 'beginners', name: 'Для новичков' }, { slug: 'friends', name: 'Для компании' },
  { slug: 'evening', name: 'На один вечер' }, { slug: 'cozy', name: 'Уютное и спокойное' },
  { slug: 'thoughtful', name: 'Есть о чём подумать' }, { slug: 'adventure', name: 'Дух приключений' },
];
describe('curated playlist presentation', () => {
  it('replaces a choice only in its own group, with no free text tags', async () => {
    const wrapper = mount(PlaylistTopicPicker, { props: { choices, modelValue: ['beginners', 'cozy'] } });
    expect(wrapper.findAll('input[type=text]')).toHaveLength(0);
    expect(wrapper.findAll('fieldset')).toHaveLength(2);
    await wrapper.findAll('input[type=radio]')[3]!.setValue(); // evening, after the optional none choice
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([['cozy', 'evening']]);
    wrapper.unmount();
  });
  it('does not silently discard older multi-topic selections', () => {
    const wrapper = mount(PlaylistTopicPicker, { props: { choices, modelValue: ['beginners', 'friends', 'cozy'] } });
    expect(wrapper.find('.topic-legacy').exists()).toBe(true);
    expect(wrapper.emitted('update:modelValue')).toBeUndefined();
    wrapper.unmount();
  });
  it('uses the uploaded cover, and falls back gracefully when an image fails', async () => {
    const wrapper = mount(PlaylistCover, { props: { customCover: '/custom.jpg', posters: ['/one.jpg', '/two.jpg', '/one.jpg'] } });
    expect(wrapper.find('.art-custom').exists()).toBe(true);
    await wrapper.get('.art-custom').trigger('error');
    expect(wrapper.get('.art-front').attributes('src')).toBe('/one.jpg');
    await wrapper.get('.art-front').trigger('error');
    expect(wrapper.get('.art-front').attributes('src')).toBe('/two.jpg');
    await wrapper.get('.art-front').trigger('error');
    expect(wrapper.find('.art-empty').exists()).toBe(true);
    wrapper.unmount();
  });
});
