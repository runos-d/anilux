import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import ExcerptCapture from './ExcerptCapture.vue';
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ isAuthenticated: true }) }));
vi.mock('@/api/excerpts', async importOriginal => ({ ...await importOriginal<object>(), excerptsApi: { create: vi.fn() } }));
describe('Excerpt capture', () => {
  it('uses fractional responses and discards a range when material changes', async () => {
    const wrapper = mount(ExcerptCapture, { props: { animeId: 1, season: 2, episode: 3, translationId: 77, link: 'https://kodikplayer.com/serial/1/hash' }, global: { stubs: { RouterLink: true } } });
    const vm = wrapper.vm as unknown as { observeEpisode: (data: object) => void; observeDuration: (time: number) => void; captureTime: (time: number) => void };
    vm.observeEpisode({ episode: 3, season: 2, translation: { id: 77 } }); vm.observeDuration(1200); await wrapper.vm.$nextTick();
    await wrapper.findAll('button')[0]!.trigger('click'); expect(wrapper.emitted('requestTime')).toHaveLength(1);
    vm.captureTime(10.2525); await wrapper.vm.$nextTick();
    await wrapper.findAll('button')[1]!.trigger('click'); vm.captureTime(11.7575); await wrapper.vm.$nextTick();
    expect(wrapper.find('input[aria-label="Начало отрывка вручную"]').element).toHaveProperty('value', '10.2525');
    expect(wrapper.find('input[aria-label="Конец отрывка вручную"]').element).toHaveProperty('value', '11.7575');
    vm.observeEpisode({ episode: 4, season: 2, translation: { id: 77 } }); await wrapper.vm.$nextTick();
    expect(wrapper.find('form').exists()).toBe(false);
    expect(wrapper.findAll('button')[1]!.attributes('disabled')).toBeDefined(); wrapper.unmount();
  });
  it('does not keep the duration or a pending mark after selecting another dub', async () => {
    const wrapper = mount(ExcerptCapture, { props: { animeId: 1, season: 2, episode: 3, translationId: 77, link: 'https://kodikplayer.com/serial/1/hash' }, global: { stubs: { RouterLink: true } } });
    const vm = wrapper.vm as unknown as { observeEpisode: (data: object) => void; observeDuration: (time: number) => void; captureTime: (time: number) => void };
    vm.observeEpisode({ episode: 3, season: 2, translation: { id: 77 } }); vm.observeDuration(1200); await wrapper.vm.$nextTick();
    await wrapper.findAll('button')[0]!.trigger('click');
    await wrapper.setProps({ translationId: 78 }); vm.captureTime(10);
    await wrapper.vm.$nextTick(); expect(wrapper.findAll('button')[0]!.attributes('disabled')).toBeDefined(); expect(wrapper.find('form').exists()).toBe(false); wrapper.unmount();
  });
});
