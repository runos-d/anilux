export const animeSections = ['catalog', 'ongoings', 'recommendations', 'announcements', 'random', 'calendar', 'currently_watching'] as const;
export type AnimeSection = typeof animeSections[number];

/** Choose before children mount, so hidden tabs cannot start their requests. */
export function initialAnimeSection(query: Record<string, unknown>, saved: string | null, hasPreset = false): AnimeSection {
  if (['search', 'genre_name', 'genres', 'type', 'status', 'year_from', 'year_to', 'studio']
    .some(key => query[key] != null && query[key] !== '') || hasPreset) return 'catalog';
  const section = typeof query.section === 'string' ? query.section : saved;
  return animeSections.includes(section as AnimeSection) ? section as AnimeSection : 'catalog';
}
