import { mount, flushPromises } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ReminderModal from './ReminderModal.vue';
import type { Anime } from '@/types';

const get = vi.fn(), patch = vi.fn(), post = vi.fn();
vi.mock('@/api/client', () => ({ default: { get: (...args: unknown[]) => get(...args),
  patch: (...args: unknown[]) => patch(...args), post: (...args: unknown[]) => post(...args) }, getMediaUrl: (url: string) => url }));
beforeEach(() => { get.mockReset(); patch.mockReset(); post.mockReset(); });

describe('manual episode subscription controls', () => {
  it('uses the subscription record ID to opt out and re-enable an existing subscription', async () => {
    get.mockResolvedValue({ data: { results: [{ id: 777, anime: 23, is_active: true }] } });
    patch.mockResolvedValueOnce({ data: { id: 777, is_active: false } }).mockResolvedValueOnce({ data: { id: 777, is_active: true } });
    const wrapper = mount(ReminderModal, { props: { show: true, anime: { id: 23, title_ru: 'Подписка' } as Anime },
      global: { stubs: { Teleport: true } } });
    await flushPromises();
    await wrapper.get('.btn-secondary').trigger('click'); await flushPromises();
    expect(patch).toHaveBeenCalledWith('/notifications/episode-subs/777/', { is_active: false });
    expect(wrapper.get('.btn-secondary').text()).toContain('Подписаться');
    await wrapper.get('.btn-secondary').trigger('click'); await flushPromises();
    expect(patch).toHaveBeenLastCalledWith('/notifications/episode-subs/777/', { is_active: true });
    expect(post).not.toHaveBeenCalled(); wrapper.unmount();
  });
  it('retains manual repeat intervals and a locally chosen end date', async () => {
    get.mockResolvedValue({ data: [] });
    const wrapper = mount(ReminderModal, { props: { show: true, anime: { id: 23, title_ru: 'Повтор' } as Anime },
      global: { stubs: { Teleport: true } } });
    await flushPromises();
    const preset = wrapper.findAll('button').find(button => button.text().includes('Через неделю'))!;
    await preset.trigger('click');
    await wrapper.findAll('.repeat-btn').find(button => button.text().includes('Свой интервал'))!.trigger('click');
    await wrapper.get('.stepper-input').setValue('14');
    await wrapper.get('.repeat-end input[type=checkbox]').setValue(true);
    const ending = new Date(); ending.setDate(ending.getDate() + 60);
    const date = `${ending.getFullYear()}-${String(ending.getMonth()+1).padStart(2,'0')}-${String(ending.getDate()).padStart(2,'0')}`;
    await wrapper.get('.repeat-end input[type=date]').setValue(date);
    await wrapper.get('.btn-save').trigger('click');
    const saved = wrapper.emitted('save')?.[0]?.[0] as { reminderTime: Date; repeatWeekly: boolean; repeatIntervalDays: number; endDate: Date };
    expect(saved.reminderTime.getTime()).toBeGreaterThan(Date.now());
    expect(saved.repeatWeekly).toBe(false); wrapper.unmount();
    expect(saved.repeatIntervalDays).toBe(14);
    expect(saved.endDate.getDate()).toBe(ending.getDate());
    expect(saved.endDate.getHours()).toBe(23);
  });
});
