import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it } from 'vitest';
import KodikPlayer from './KodikPlayer.vue';

const mounted: ReturnType<typeof mount>[] = [];
afterEach(() => mounted.splice(0).forEach(wrapper => wrapper.unmount()));
describe('Kodik message boundary', () => {
  it('keeps excerpt-only iframe parameters out of normal playback', () => {
    const normal = mount(KodikPlayer, { props: { link: 'https://kodikplayer.com/serial/1/hash/720p' } }); mounted.push(normal);
    expect(normal.find('iframe').attributes('src')).not.toContain('only_episode');
    const excerpt = mount(KodikPlayer, { props: { link: 'https://kodikplayer.com/seria/3/hash/720p', startFrom: 10.25, onlyEpisode: true } }); mounted.push(excerpt);
    expect(excerpt.find('iframe').attributes('src')).toContain('start_from=10.25');
    expect(excerpt.find('iframe').attributes('src')).toContain('only_episode=true');
    expect(excerpt.find('iframe').attributes('src')).not.toContain('autoplay=1');
  });
  it('keeps the iframe loaded across mode switches', async () => {
    const wrapper = mount(KodikPlayer, {
      props: {
        link: 'https://kodikplayer.com/seria/3/hash/720p',
        autoplay: true,
        episode: 1,
      },
    });
    mounted.push(wrapper);
    const initialSrc = wrapper.find('iframe').attributes('src');

    await wrapper.setProps({ autoplay: false });
    expect(wrapper.find('iframe').attributes('src')).toBe(initialSrc);

    await wrapper.setProps({ active: false, episode: 2 });
    expect(wrapper.find('iframe').attributes('src')).toBe(initialSrc);

    await wrapper.setProps({ active: true });
    const restoredSrc = wrapper.find('iframe').attributes('src');
    expect(restoredSrc).not.toBe(initialSrc);
    expect(restoredSrc).toContain('episode=2');
  });
  it('accepts fractional time only from the player window and origin', () => {
    const wrapper = mount(KodikPlayer, { props: { link: 'https://kodikplayer.com/seria/3/hash/720p' } }); mounted.push(wrapper);
    const source = (wrapper.find('iframe').element as HTMLIFrameElement).contentWindow;
    const data = { key: 'kodik_player_time', value: 10.2525 };
    window.dispatchEvent(new MessageEvent('message', { data, source: window, origin: 'https://kodikplayer.com' }));
    window.dispatchEvent(new MessageEvent('message', { data, source, origin: 'https://attacker.test' }));
    expect(wrapper.emitted('preciseTime')).toBeUndefined();
    window.dispatchEvent(new MessageEvent('message', { data, source, origin: 'https://kodikplayer.com' }));
    expect(wrapper.emitted('preciseTime')).toEqual([[10.2525]]);
  });
});
