import { describe, expect, it } from 'vitest';
import { initialAnimeSection } from './animeSection';

describe('initial anime tab', () => {
  it('selects the requested tab before any catalog child mounts', () => {
    expect(initialAnimeSection({ section: 'calendar' }, 'catalog')).toBe('calendar');
    expect(initialAnimeSection({}, 'recommendations')).toBe('recommendations');
  });
  it('keeps search, genre and preset URLs in the catalog', () => {
    expect(initialAnimeSection({ search: 'Ван-Пис', section: 'calendar' }, null)).toBe('catalog');
    expect(initialAnimeSection({ genre_name: 'Комедия' }, 'calendar')).toBe('catalog');
    expect(initialAnimeSection({}, 'calendar', true)).toBe('catalog');
    expect(initialAnimeSection({ section: 'invalid' }, 'calendar')).toBe('catalog');
  });
});
