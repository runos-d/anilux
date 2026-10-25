import { mount, flushPromises } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import CalendarReleaseCard from './CalendarReleaseCard.vue';

const auth = { isAuthenticated: true };
const createReminder = vi.fn();
const deactivateReminder = vi.fn();
const store = { reminders: [] as Record<string, unknown>[], createReminder, deactivateReminder };
vi.mock('@/stores/auth', () => ({ useAuthStore: () => auth }));
vi.mock('@/stores/notifications', () => ({ useNotificationStore: () => store }));
vi.mock('@/composables/useToast', () => ({ useToast: () => ({ success: vi.fn(), error: vi.fn() }) }));
const item = { calendar_release_id: 44, aired_at: '2026-10-12T20:30:00Z', local_day: '2026-10-12',
  time: '23:30', episode_number: 3, is_upcoming: true,
  anime: { id: 92001, title_ru: 'Релиз', title_en: '', kind: 'tv' } };
beforeEach(() => { auth.isAuthenticated = true; store.reminders = []; createReminder.mockReset(); deactivateReminder.mockReset(); });

describe('calendar episode reminder', () => {
  it('opens the anime from mouse and keyboard activation', async () => {
    const wrapper = mount(CalendarReleaseCard, { props: { item } });
    await wrapper.get('article').trigger('click');
    await wrapper.get('article').trigger('keydown', { key: 'Enter' });
    expect(wrapper.emitted('click')).toHaveLength(2);
    wrapper.unmount();
  });
  it('posts the stable release ID and stops the card navigation and duplicate taps', async () => {
    let finish: (value: unknown) => void = () => {};
    createReminder.mockReturnValue(new Promise(resolve => { finish = resolve; }));
    const wrapper = mount(CalendarReleaseCard, { props: { item } });
    const button = wrapper.get('button');
    await button.trigger('click');
    await button.trigger('click');
    expect(createReminder).toHaveBeenCalledTimes(1);
    expect(createReminder).toHaveBeenCalledWith(expect.objectContaining({ calendar_release_id: 44, follow_schedule: true }));
    expect(wrapper.emitted('click')).toBeUndefined();
    finish({ id: 1 }); await flushPromises(); wrapper.unmount();
  });
  it('does not expose reminder creation to guests', () => {
    auth.isAuthenticated = false;
    const wrapper = mount(CalendarReleaseCard, { props: { item } });
    expect(wrapper.find('button').exists()).toBe(false); wrapper.unmount();
  });
  it('turns an active reminder off on the next click', async () => {
    store.reminders = [{ id: 9, calendar_release: 44, reminder_time: '2026-10-12T19:30:00Z', is_active: true }];
    deactivateReminder.mockResolvedValue(undefined);
    const wrapper = mount(CalendarReleaseCard, { props: { item } });
    await wrapper.get('button').trigger('click');
    expect(deactivateReminder).toHaveBeenCalledWith(9);
    expect(createReminder).not.toHaveBeenCalled();
    wrapper.unmount();
  });
});
