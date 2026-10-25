import { shallowMount } from '@vue/test-utils';
import type { CalendarData } from '@/api/anime';
import { createPinia, setActivePinia } from 'pinia';
import { nextTick } from 'vue';
import { beforeEach } from 'vitest';
import { describe, expect, it, vi } from 'vitest';
import CalendarView from './CalendarView.vue';

const routerPush = vi.hoisted(() => vi.fn());
vi.mock('vue-router', () => ({ useRouter: () => ({ push: routerPush }) }));
vi.mock('@/api/anime', () => ({ default: {} }));
beforeEach(() => { setActivePinia(createPinia()); routerPush.mockReset(); });

describe('calendar before its snapshot arrives', () => {
  it('renders the initial week with no selected data or releases', () => {
    const wrapper = shallowMount(CalendarView, { props:{ data:null, loading:false, error:null } });
    expect(wrapper.findAll('.cal-strip-cell')).toHaveLength(7);
    expect(wrapper.find('.cal-rows').exists()).toBe(false);
    wrapper.unmount();
  });
});

const data = (): CalendarData => ({ month_key: '2026-09', year: 2026, month: 9,
  month_label: 'September 2026', today: '2026-10-12', grid_start: '2026-08-31', grid_end: '2026-10-05',
  has_prev: true, has_next: true, next_month_key: '2026-10', prev_month_key: '2026-08', total: 1,
  days: [{ date: '2026-09-30', weekday: 2, weekday_name: 'Ср', in_month: true, is_today: false,
    items: [{ aired_at: '2026-09-30T16:30:00-07:00', local_day: '2026-09-30', time: '16:30',
      episode_number: 1, is_upcoming: false,
      anime: { id: 1, title_ru: 'История', title_en: '', kind: 'tv' } }] }] });

describe('saved calendar navigation', () => {
  it('selects a saved historical release in week mode when props arrive asynchronously', async () => {
    localStorage.clear();
    const wrapper = shallowMount(CalendarView, { props: { data: null, loading: false, error: null } });
    await wrapper.setProps({ data: data() });
    expect(wrapper.find('.cal-strip-cell.is-active').text()).toContain('30');
    expect(wrapper.findAllComponents({ name: 'CalendarReleaseCard' })).toHaveLength(1);
    await wrapper.find('button[aria-label="Назад"]').trigger('click');
    await wrapper.find('button[aria-label="Назад"]').trigger('click');
    await wrapper.find('button[aria-label="Назад"]').trigger('click');
    await wrapper.find('button[aria-label="Назад"]').trigger('click');
    await wrapper.find('button[aria-label="Назад"]').trigger('click');
    expect(wrapper.emitted('change-month')?.at(-1)).toEqual(['2026-08']);
    wrapper.unmount();
  });

  it('opens the exact anime page instead of its franchise', async () => {
    const value = data();
    value.days[0]!.items[0]!.anime = {
      ...value.days[0]!.items[0]!.anime,
      id: 42,
      slug: 'istoriya',
      franchise_id: 7,
    };
    const wrapper = shallowMount(CalendarView, { props: { data: value, loading: false, error: null } });
    wrapper.findComponent({ name: 'CalendarReleaseCard' }).vm.$emit('click');
    await nextTick();
    expect(routerPush).toHaveBeenCalledWith('/anime/42-istoriya');
    wrapper.unmount();
  });
});
