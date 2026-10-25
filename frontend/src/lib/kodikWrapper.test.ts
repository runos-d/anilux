import { describe, expect, it } from 'vitest';
import {
  extractKodikEpisodes,
  extractKodikSeasons,
  extractKodikTranslations,
  pickBestKodikSource,
} from './kodikWrapper';

describe('kodikWrapper', () => {
  it('extracts dubs and seasons from a material payload', () => {
    const material = {
      translations: [
        { id: 1, title: 'Original', type: 'voice' },
        { id: 2, title: 'JAP', type: 'voice' },
      ],
      seasons: {
        1: {
          episodes: {
            1: '//kodik.example/video/1/hash/720p',
            2: '//kodik.example/video/1/hash/720p',
          },
        },
        2: {
          episodes: {
            1: '//kodik.example/video/2/hash/720p',
          },
        },
      },
    };

    expect(extractKodikTranslations(material)).toEqual([
      { id: 1, name: 'Original', type: 'voice' },
      { id: 2, name: 'JAP', type: 'voice' },
    ]);

    expect(extractKodikSeasons(material)).toEqual([
      { season: 1, episodes: [1, 2] },
      { season: 2, episodes: [1] },
    ]);
  });

  it('picks the highest quality source from a Kodik HLS map', () => {
    const best = pickBestKodikSource({
      360: [{ src: '//cdn.example/360.m3u8', type: 'application/x-mpegURL' }],
      720: [{ src: '//cdn.example/720.m3u8', type: 'application/x-mpegURL' }],
      1080: [{ src: '//cdn.example/1080.m3u8', type: 'application/x-mpegURL' }],
    });

    expect(best).toMatchObject({
      quality: '1080',
      url: 'https://cdn.example/1080.m3u8',
    });
  });

  it('collects episode numbers from a material without losing order', () => {
    const episodes = extractKodikEpisodes({
      seasons: {
        1: { episodes: { 3: 'url', 1: 'url', 2: 'url' } },
      },
    });

    expect(episodes).toEqual([1, 2, 3]);
  });
});
