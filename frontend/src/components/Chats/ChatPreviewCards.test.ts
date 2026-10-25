import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';
import ChatContentCard from './ChatContentCard.vue';
import ChatPreviewCards from './ChatPreviewCards.vue';

vi.mock('@/api/client', () => ({ getMediaUrl: (url?: string) => url }));

describe('chat content cards', () => {
  it('uses the real message cards for the One Piece and playlist preview, with navigation disabled', async () => {
    const wrapper = mount(ChatPreviewCards);
    const cards = wrapper.findAllComponents(ChatContentCard);
    expect(cards.map(card => card.props('type'))).toEqual(['anime', 'playlist']);
    expect(cards[0]!.text()).toContain('Ван-Пис');
    expect(cards[0]!.text()).toContain('1999 · ТВ-сериал');
    expect(cards[1]!.text()).toContain('Любимые приключения');
    expect(cards[1]!.text()).toContain('1 аниме');
    expect(wrapper.findAll('img')).toHaveLength(2);
    expect(wrapper.findAll('button').every(button => button.attributes('disabled') !== undefined)).toBe(true);
    await cards[0]!.trigger('click');
    expect(cards[0]!.emitted('open')).toBeUndefined();
    wrapper.unmount();
  });

  it('keeps live cards clickable and shows the supplied attachment data and message time', async () => {
    const wrapper = mount(ChatContentCard, { props: {
      type: 'playlist', data: { title: 'Мой плейлист', items_count: 3, posters: ['/media/cover.jpg'] }, time: '14:05',
    } });
    expect(wrapper.text()).toContain('Мой плейлист');
    expect(wrapper.text()).toContain('3 аниме');
    expect(wrapper.text()).toContain('14:05');
    expect(wrapper.find('img').attributes('src')).toBe('/media/cover.jpg');
    await wrapper.trigger('click');
    expect(wrapper.emitted('open')).toHaveLength(1);
    wrapper.unmount();
  });
});
