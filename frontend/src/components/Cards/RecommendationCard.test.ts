import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import RecommendationCard from './RecommendationCard.vue';

const push = vi.fn();
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }));
const props = { animeId: 1, title: 'Фильм', poster: '', genres: [], rating: 8,
  ratingCount: 0, status: 'released', year: 2026, reason: 'Фильм из одной серии с рейтингом 8.0.' };
const wrappers: ReturnType<typeof mount>[] = [];
const card = () => {
  const wrapper = mount(RecommendationCard, { props, attachTo: document.body,
    global: { stubs: { AnimeCard: true, FranchiseCard: true } } });
  wrappers.push(wrapper);
  return wrapper;
};
afterEach(() => { wrappers.splice(0).forEach(wrapper => wrapper.unmount()); push.mockClear(); });

describe('currently disabled recommendation explanation', () => {
  it('keeps the disabled control unavailable even when reason data arrives', async () => {
    const wrapper = card();
    expect(wrapper.find('.reason-btn').exists()).toBe(false);
    await wrapper.trigger('pointerenter', {pointerType:'mouse'});
    await wrapper.trigger('click');
    expect(document.querySelector('[role=tooltip]')).toBeNull();
    expect(push).not.toHaveBeenCalled();
  });
  it('retains the active card actions and navigation', async () => {
    const wrapper = card();
    const anime = wrapper.findComponent({name:'AnimeCard'});
    expect(anime.props('showActions')).toBe(true);
    anime.vm.$emit('click');
    await wrapper.vm.$nextTick();
    expect(push).toHaveBeenCalled();
  });
});
