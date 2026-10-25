import { mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import AniLuxPlayer from './AniLuxPlayer.vue';

const anime4k = vi.hoisted(() => ({
  attachVideo: vi.fn(),
  start: vi.fn(),
  stop: vi.fn(),
  detachVideo: vi.fn(),
}));

vi.mock('hls.js', () => ({
  default: class HlsMock {
    static isSupported() {
      return false;
    }

    on() {}
    loadSource() {}
    attachMedia() {}
    destroy() {}
  },
}));

vi.mock('@/lib/anime4k', () => ({
  loadAnime4K: vi.fn(async () => ({
    ANIME4KJS_SIMPLE_M_2X: ['simple-m-2x'],
    VideoUpscaler: class VideoUpscalerMock {
      static isSupported() {
        return true;
      }

      attachVideo = anime4k.attachVideo;
      start = anime4k.start;
      stop = anime4k.stop;
      detachVideo = anime4k.detachVideo;
    },
  })),
}));

const mounted: ReturnType<typeof mount>[] = [];
afterEach(() => {
  vi.restoreAllMocks();
  vi.clearAllMocks();
  mounted.splice(0).forEach(wrapper => wrapper.unmount());
});

const translations = [
  { id: 734, name: 'Проф. Многоголосый', type: 'voice', episodes_done: 24 },
  { id: 1895, name: 'FumoDub', type: 'voice', episodes_done: 24 },
];

describe('AniLux player source pickers', () => {
  it('emits the chosen episode from the episode menu', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1, 2, 3] }],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select').trigger('click');
    expect(wrapper.find('.player__menu--episodes').exists()).toBe(true);

    const second = wrapper.findAll('.player__episode-btn').find(button => button.text() === '2');
    expect(second).toBeDefined();
    await second!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 2, season: 1 }]]);
    expect(wrapper.find('.player__menu--episodes').exists()).toBe(false);
  });

  it('switches seasons before picking an episode', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [
          { season: 1, label: 'Сезон 1', episodes: [1, 2] },
          { season: 2, label: 'Сезон 2', episodes: [1, 2] },
        ],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select').trigger('click');
    const seasonTab = wrapper.findAll('.player__season-tab').find(tab => tab.text() === 'Сезон 2');
    await seasonTab!.trigger('click');

    const second = wrapper.findAll('.player__episode-btn').find(button => button.text() === '2');
    await second!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 2, season: 2 }]]);
  });

  it('keeps season zero when picking a special episode', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 2,
        episodeGroups: [
          { season: 0, label: 'Спешлы', episodes: [1, 2, 3, 4] },
          { season: 2, label: 'Сезон 2', episodes: [1, 2] },
        ],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select').trigger('click');
    const specialTab = wrapper.findAll('.player__season-tab').find(tab => tab.text() === 'Спешлы');
    await specialTab!.trigger('click');

    const second = wrapper.findAll('.player__episode-btn').find(button => button.text() === '2');
    await second!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 2, season: 0 }]]);
  });

  it('shows the season button only when there are multiple groups', () => {
    const singleSeason = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1, 2] }],
        translations,
        translationId: 734,
      },
    });
    mounted.push(singleSeason);
    expect(singleSeason.find('.player__select--season').exists()).toBe(false);

    const multiSeason = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 2,
        episodeGroups: [
          { season: 0, label: 'Спешлы', episodes: [1, 2, 3, 4] },
          { season: 2, label: 'Сезон 2', episodes: [1, 2] },
        ],
        translations,
        translationId: 734,
      },
    });
    mounted.push(multiSeason);
    expect(multiSeason.find('.player__select--season').exists()).toBe(true);
    expect(multiSeason.find('.player__select--season').text()).toContain('Сезон 2');
  });

  it('switches seasons from the dedicated season button', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 2,
        episodeGroups: [
          { season: 0, label: 'Спешлы', episodes: [1, 2, 3, 4] },
          { season: 2, label: 'Сезон 2', episodes: [1, 2] },
        ],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select--season').trigger('click');
    expect(wrapper.find('.player__menu--seasons').exists()).toBe(true);

    const specialOption = wrapper.findAll('.player__season-option').find(
      option => option.text().includes('Спешлы'),
    );
    expect(specialOption).toBeDefined();
    await specialOption!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 1, season: 0 }]]);
    expect(wrapper.find('.player__menu--seasons').exists()).toBe(false);
  });

  it('keeps the current episode number when the target season has it', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 2,
        season: 0,
        episodeGroups: [
          { season: 0, label: 'Спешлы', episodes: [1, 2, 3, 4] },
          { season: 2, label: 'Сезон 2', episodes: [1, 2] },
        ],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select--season').trigger('click');
    const seasonOption = wrapper.findAll('.player__season-option').find(
      option => option.text().includes('Сезон 2'),
    );
    await seasonOption!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 2, season: 2 }]]);
  });

  it('emits the chosen translation with its own id', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    await wrapper.find('.player__select--translation').trigger('click');
    const items = wrapper.findAll('.player__menu--translations .player__menu-item');
    expect(items).toHaveLength(2);

    await items[1]!.trigger('click');

    expect(wrapper.emitted('selectTranslation')).toEqual([[1895]]);
    expect(wrapper.find('.player__menu--translations').exists()).toBe(false);
  });

  it('lists only real qualities and defaults to the first one', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [
          { quality: '720', url: 'https://example.com/720.m3u8' },
          { quality: '480', url: 'https://example.com/480.m3u8' },
          { quality: 'auto', url: 'https://example.com/auto.m3u8' },
        ],
      },
    });
    mounted.push(wrapper);
    await wrapper.vm.$nextTick();
    await wrapper.vm.$nextTick();

    expect(wrapper.find('.player__quality-text').text()).toBe('720p');

    await wrapper.find('.player__quality-btn').trigger('click');
    const options = wrapper.findAll('.player__quality-item');
    expect(options.map(option => option.text())).toEqual(['1440pAnime4K', '720p', '480p']);
  });

  it('offers neutral stream names and emits the selected stream', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        sources: [{ quality: 'auto', url: '/api/anime/alternative-stream/content/?token=test' }],
        streams: [
          { id: 'primary', label: 'Основной' },
          { id: 'reserve', label: 'СВ-Дубль' },
        ],
        streamId: 'primary',
      },
    });
    mounted.push(wrapper);

    expect(wrapper.find('.player__select--stream').text()).toContain('Поток 1');
    await wrapper.find('.player__select--stream').trigger('click');
    const options = wrapper.findAll('.player__stream-option');
    expect(options.map(option => option.text())).toEqual([
      'Поток 1Основной',
      'Поток 2СВ-Дубль',
    ]);
    await options[1]!.trigger('click');

    expect(wrapper.emitted('selectStream')).toEqual([['reserve']]);
    expect(wrapper.find('.player__menu--streams').exists()).toBe(false);

    await wrapper.find('.player__quality-btn').trigger('click');
    expect(wrapper.find('.player__quality-item--anime4k').text()).toBe('1440pAnime4K');
  });

  it('runs Anime4K from the 1440p quality option and releases it on episode change', async () => {
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
      getExtension: vi.fn(() => ({})),
    } as unknown as WebGLRenderingContext);
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1, 2] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/720.m3u8' }],
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    await wrapper.find('.player__quality-btn').trigger('click');
    await wrapper.find('.player__quality-item--anime4k').trigger('click');
    await vi.waitFor(() => expect(anime4k.attachVideo).toHaveBeenCalledWith(
      video,
      wrapper.find('.player__upscale-canvas').element,
    ));
    expect(wrapper.find('.player__quality-text').text()).toBe('1440p');

    video.dispatchEvent(new Event('play'));
    await wrapper.vm.$nextTick();
    expect(anime4k.start).toHaveBeenCalled();

    video.dispatchEvent(new Event('pause'));
    await wrapper.vm.$nextTick();
    expect(anime4k.stop).toHaveBeenCalled();

    await wrapper.setProps({ episode: 2 });
    expect(anime4k.detachVideo).toHaveBeenCalled();
  });

  it('resets the timeline after a translation switch', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/old.m3u8' }],
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    let mediaDuration = 1000;
    let mediaTime = 120;
    Object.defineProperty(video, 'duration', {
      configurable: true,
      get: () => mediaDuration,
    });
    Object.defineProperty(video, 'currentTime', {
      configurable: true,
      get: () => mediaTime,
      set: (value: number) => {
        mediaTime = value;
      },
    });

    video.dispatchEvent(new Event('loadedmetadata'));
    await wrapper.vm.$nextTick();
    (wrapper.vm as unknown as { prepareTranslationSwitch: () => void }).prepareTranslationSwitch();

    await wrapper.setProps({
      translationId: 1895,
      sources: [{ quality: '720', url: 'https://example.com/new.m3u8' }],
    });
    await wrapper.vm.$nextTick();

    mediaDuration = 1100;
    video.dispatchEvent(new Event('loadedmetadata'));
    await wrapper.vm.$nextTick();

    expect(mediaTime).toBe(0);
  });

  it('offers to continue from the saved position', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/source.m3u8' }],
        resumeTime: 120,
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    let mediaTime = 0;
    Object.defineProperty(video, 'duration', {
      configurable: true,
      get: () => 600,
    });
    Object.defineProperty(video, 'currentTime', {
      configurable: true,
      get: () => mediaTime,
      set: (value: number) => {
        mediaTime = value;
      },
    });
    const play = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(video, 'play', { configurable: true, value: play });

    video.dispatchEvent(new Event('loadedmetadata'));
    await wrapper.vm.$nextTick();

    const resume = wrapper.find('.player__resume-btn');
    expect(resume.text()).toContain('Продолжить с 2:00');

    await resume.trigger('click');
    expect(mediaTime).toBe(120);
    expect(play).toHaveBeenCalled();
    expect(wrapper.find('.player__resume').exists()).toBe(false);
  });

  it('starts from the beginning when the resume prompt is dismissed', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/source.m3u8' }],
        resumeTime: 120,
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    let mediaTime = 0;
    Object.defineProperty(video, 'duration', {
      configurable: true,
      get: () => 600,
    });
    Object.defineProperty(video, 'currentTime', {
      configurable: true,
      get: () => mediaTime,
      set: (value: number) => {
        mediaTime = value;
      },
    });
    const play = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(video, 'play', { configurable: true, value: play });

    video.dispatchEvent(new Event('loadedmetadata'));
    await wrapper.vm.$nextTick();

    await wrapper.find('.player__resume-restart').trigger('click');
    expect(mediaTime).toBe(0);
    expect(play).toHaveBeenCalled();
  });

  it('seeks by five seconds with the arrow keys', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/source.m3u8' }],
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    let mediaTime = 20;
    Object.defineProperty(video, 'duration', {
      configurable: true,
      get: () => 100,
    });
    Object.defineProperty(video, 'currentTime', {
      configurable: true,
      get: () => mediaTime,
      set: (value: number) => {
        mediaTime = value;
      },
    });

    video.dispatchEvent(new Event('timeupdate'));
    await wrapper.vm.$nextTick();

    await wrapper.find('.player').trigger('keydown', { code: 'ArrowRight' });
    expect(mediaTime).toBe(25);

    await wrapper.find('.player').trigger('keydown', { code: 'ArrowLeft' });
    expect(mediaTime).toBe(20);
    expect(wrapper.emitted('selectEpisode')).toBeUndefined();
  });

  it('restores the previous volume after unmuting', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/source.m3u8' }],
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    await wrapper.find('.player').trigger('keydown', { code: 'ArrowDown' });
    await wrapper.find('.player').trigger('keydown', { code: 'ArrowDown' });
    expect(video.volume).toBeCloseTo(0.6);

    const muteButton = wrapper.find('.player__vol .player__btn');
    await muteButton.trigger('click');
    expect(video.muted).toBe(true);
    expect(video.volume).toBeCloseTo(0.6);

    await muteButton.trigger('click');
    expect(video.muted).toBe(false);
    expect(video.volume).toBeCloseTo(0.6);
  });

  it('steps to the next episode with the arrow control', async () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 2,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1, 2, 3] }],
        translations,
        translationId: 734,
      },
    });
    mounted.push(wrapper);

    const next = wrapper.findAll('.player__step')[1];
    await next!.trigger('click');

    expect(wrapper.emitted('selectEpisode')).toEqual([[{ episode: 3, season: 1 }]]);
  });

  it('captures the current frame without seeking the video', () => {
    const wrapper = mount(AniLuxPlayer, {
      props: {
        episode: 1,
        season: 1,
        episodeGroups: [{ season: 1, label: 'Сезон 1', episodes: [1] }],
        translations,
        translationId: 734,
        sources: [{ quality: '720', url: 'https://example.com/source.m3u8' }],
      },
    });
    mounted.push(wrapper);

    const video = wrapper.find('video').element as HTMLVideoElement;
    Object.defineProperties(video, {
      readyState: { configurable: true, value: 2 },
      videoWidth: { configurable: true, value: 1280 },
      videoHeight: { configurable: true, value: 720 },
      currentTime: { configurable: true, value: 123.456789 },
    });

    const drawImage = vi.fn();
    vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({
      drawImage,
    } as unknown as CanvasRenderingContext2D);
    vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockReturnValue('data:image/png;base64,AAAA');

    const frame = (wrapper.vm as unknown as {
      captureFrame: () => { timestamp: number; width: number; height: number; blob: Blob };
    }).captureFrame();

    expect(drawImage).toHaveBeenCalledWith(video, 0, 0, 1280, 720);
    expect(frame.timestamp).toBe(123.456789);
    expect(frame.width).toBe(1280);
    expect(frame.height).toBe(720);
    expect(frame.blob.type).toBe('image/png');
    expect(video.currentTime).toBe(123.456789);
  });
});
