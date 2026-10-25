import * as KodikWrapper from 'kodikwrapper';

const { Client, VideoLinks } = KodikWrapper;

export interface KodikSourceEntry {
  src: string;
  type: string;
}

export interface KodikSourceQualityMap {
  [quality: string]: KodikSourceEntry[];
}

export interface KodikTranslationEntry {
  id: number | string;
  name: string;
  type?: string;
  quality?: string | number;
  is_custom?: boolean;
  kodik_link?: string;
  logo?: string;
}

export interface KodikSeasonSummary {
  season: number;
  episodes: number[];
}

export interface KodikBestSource {
  quality: string;
  url: string;
  type: string;
}

export interface KodikMaterialLike {
  id?: number | string;
  link?: string;
  translation?: {
    id?: number | string;
    title?: string;
    type?: string;
  };
  translations?: Array<{
    id?: number | string;
    title?: string;
    name?: string;
    type?: string;
  }>;
  seasons?: Record<string, { episodes?: Record<string, string | null> | null } | null>;
  episodes_count?: number;
  quality?: string | number;
  title?: string;
  title_orig?: string;
  type?: string;
}

const DEFAULT_PRIORITY = ['1080', '720', '480', '360', '240', 'auto'];

export const getKodikToken = () =>
  (typeof import.meta !== 'undefined' ? (import.meta.env.VITE_KODIK_API_TOKEN as string | undefined) : undefined) ?? '';

export const createKodikClient = (token = getKodikToken()) => {
  if (!token) {
    throw new Error('Kodik public token is not configured for frontend.');
  }
  return Client.fromToken(token);
};

export const normalizeKodikLink = (value?: string | null): string => {
  if (!value) return '';
  if (value.startsWith('//')) return `https:${value}`;
  if (!value.startsWith('http')) return `https://${value}`;
  return value;
};

export const dedupeKodikTranslations = (items: KodikTranslationEntry[]) => {
  const map = new Map<string, KodikTranslationEntry>();
  for (const item of items) {
    const key = String(item.id ?? `${item.name}:${item.type ?? 'voice'}`);
    if (!map.has(key)) map.set(key, item);
  }
  return [...map.values()];
};

export const extractKodikTranslations = (material?: KodikMaterialLike | null): KodikTranslationEntry[] => {
  const candidates: Array<{ id?: number | string; title?: string; name?: string; type?: string }> = [];

  const direct = Array.isArray(material?.translations) ? material.translations : [];
  for (const item of direct) {
    candidates.push({
      id: item.id,
      title: item.title ?? item.name,
      name: item.name ?? item.title,
      type: item.type,
    });
  }

  if (!candidates.length && material?.translation) {
    candidates.push({
      id: material.translation.id,
      title: material.translation.title,
      name: material.translation.title,
      type: material.translation.type,
    });
  }

  return dedupeKodikTranslations(
    candidates
      .filter((entry) => entry.id !== undefined && (entry.title || entry.name))
      .map((entry) => ({
        id: entry.id as number | string,
        name: entry.title || entry.name || 'Unknown',
        type: entry.type || 'voice',
        quality: material?.quality,
        kodik_link: material?.link,
      })),
  );
};

export const extractKodikEpisodes = (material?: KodikMaterialLike | null, season?: number | string): number[] => {
  const rawSeasons = material?.seasons ?? {};
  const seasonKey = season === undefined ? undefined : String(season);
  const chosenSeasons = seasonKey === undefined ? Object.entries(rawSeasons) : Object.entries(rawSeasons).filter(([key]) => key === seasonKey);

  const episodes = chosenSeasons.flatMap(([, seasonData]) => {
    const entries = seasonData?.episodes ?? {};
    return Object.keys(entries)
      .map((key) => Number.parseInt(key, 10))
      .filter((n) => Number.isFinite(n));
  });

  if (!episodes.length && material && Array.isArray((material as Record<string, unknown>)?.episodes)) {
    return (material as Record<string, unknown>).episodes as number[];
  }

  return [...new Set(episodes)].sort((a, b) => a - b);
};

export const extractKodikSeasons = (material?: KodikMaterialLike | null): KodikSeasonSummary[] => {
  const raw = material?.seasons ?? {};
  return Object.entries(raw)
    .map(([seasonKey, seasonData]) => {
      const episodes = seasonData?.episodes ?? {};
      const list = Object.keys(episodes)
        .map((key) => Number.parseInt(key, 10))
        .filter((value) => Number.isFinite(value))
        .sort((a, b) => a - b);

      const seasonNumber = Number.parseInt(seasonKey, 10);

      return {
        season: Number.isFinite(seasonNumber) ? seasonNumber : 1,
        episodes: list,
      };
    })
    .filter((item) => item.episodes.length > 0)
    .sort((a, b) => a.season - b.season);
};

export const pickBestKodikSource = (links?: KodikSourceQualityMap | null): KodikBestSource | null => {
  if (!links || typeof links !== 'object') return null;

  const candidates: Array<{ quality: string; url: string; type: string }> = [];

  for (const [quality, items] of Object.entries(links)) {
    if (!Array.isArray(items)) continue;
    for (const item of items) {
      const src = typeof item?.src === 'string' ? item.src : '';
      const type = typeof item?.type === 'string' ? item.type : 'application/x-mpegURL';
      if (!src) continue;
      candidates.push({
        quality,
        url: src.startsWith('//') ? `https:${src}` : src,
        type,
      });
    }
  }

  if (!candidates.length) return null;

  candidates.sort((a, b) => {
    const ai = DEFAULT_PRIORITY.indexOf(a.quality);
    const bi = DEFAULT_PRIORITY.indexOf(b.quality);

    const aRank = ai >= 0 ? ai : Number.MAX_SAFE_INTEGER;
    const bRank = bi >= 0 ? bi : Number.MAX_SAFE_INTEGER;

    if (aRank !== bRank) return aRank - bRank;

    return Number.parseInt(a.quality, 10) - Number.parseInt(b.quality, 10);
  });

  const best = candidates[0];
  if (!best) return null;

  return {
    quality: best.quality,
    url: best.url,
    type: best.type,
  };
};

export const findKodikMaterialForAnime = async (anime: {
  shikimori_id?: number | string | null;
  kodik_id?: number | string | null;
  title_ru?: string | null;
  title_en?: string | null;
}) => {
  const token = getKodikToken();
  if (!token) return null;

  try {
    const client = createKodikClient(token);

    const identifiers = [
      { key: 'shikimori_id', value: anime.shikimori_id },
      { key: 'id', value: anime.kodik_id },
    ];

    for (const identifier of identifiers) {
      if (identifier.value === undefined || identifier.value === null || identifier.value === '') continue;
      const response = await client.search({
        [identifier.key]: String(identifier.value),
        with_material_data: true,
        with_episodes: true,
        with_seasons: true,
        limit: 1,
      });

      const result = Array.isArray(response?.results) ? response.results[0] : null;
      if (result) {
        return result as KodikMaterialLike;
      }
    }

    const queryTitle = anime.title_ru || anime.title_en;
    if (!queryTitle) return null;

    const response = await client.search({
      title: queryTitle,
      with_material_data: true,
      with_episodes: true,
      with_seasons: true,
      limit: 1,
    });

    return Array.isArray(response?.results) ? (response.results[0] as KodikMaterialLike) : null;
  } catch {
    return null;
  }
};

export const resolveKodikVideoLinks = async (link: string) => {
  if (!link) return null;

  try {
    const parsed = await VideoLinks.parseLink({ link, extended: true });
    if (!parsed?.ex?.playerSingleUrl) return null;

    const endpoint = await VideoLinks.getActualVideoInfoEndpoint(parsed.ex.playerSingleUrl);
    const links = await VideoLinks.getLinks({
      link,
      videoInfoEndpoint: endpoint,
    });

    return {
      links,
      best: pickBestKodikSource(links),
      endpoint,
      parsed,
    };
  } catch {
    return null;
  }
};
