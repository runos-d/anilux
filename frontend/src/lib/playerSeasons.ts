export interface PlayerSeasonMeta {
  title?: string | null;
  episodes?: number[] | null;
}

export interface PlayerTranslationSeasons {
  id: number | string;
  is_custom?: boolean;
  seasons?: Record<string, PlayerSeasonMeta | null> | null;
  last_season?: number | null;
  episodes_done?: number | null;
}

export interface PlayerEpisodeGroup {
  season: number;
  label: string;
  episodes: number[];
  translationId?: number | string | null;
}

export interface BuildEpisodeGroupsOptions {
  translations?: PlayerTranslationSeasons[];
  selectedTranslationId?: number | string | null;
  seasons?: Record<string, { episodes?: Record<string, string> } | null> | null;
  episodes?: number | null;
  lastSeason?: number | null;
  allowFlat?: boolean;
  flatLabel?: string;
}

interface SeasonCandidate {
  translationId: number | string;
  title: string | null;
  episodes: number[];
}

const normalizeEpisodes = (values: Iterable<unknown>): number[] => {
  const episodes = new Set<number>();
  for (const value of values) {
    const episode = Number(value);
    if (Number.isInteger(episode) && episode > 0) episodes.add(episode);
  }
  return [...episodes].sort((a, b) => a - b);
};

const seasonLabel = (season: number, title?: string | null): string => {
  const cleanTitle = typeof title === "string" ? title.trim() : "";
  if (cleanTitle) return cleanTitle;
  return season === 0 ? "Спешл" : `Сезон ${season}`;
};

const parseSeasonNumber = (value: string): number | null => {
  const season = Number.parseInt(value, 10);
  return Number.isInteger(season) && season >= 0 ? season : null;
};

export const hasTranslationSeason = (
  translation: PlayerTranslationSeasons | null | undefined,
  season: number,
): boolean => {
  if (!translation || translation.is_custom) return false;
  return normalizeEpisodes(
    translation.seasons?.[String(season)]?.episodes ?? [],
  ).length > 0;
};

export const buildEpisodeGroups = ({
  translations = [],
  selectedTranslationId = null,
  seasons = null,
  episodes = null,
  lastSeason = null,
  allowFlat = false,
  flatLabel = "Серии",
}: BuildEpisodeGroupsOptions): PlayerEpisodeGroup[] => {
  const candidates = new Map<number, SeasonCandidate[]>();

  for (const translation of translations) {
    if (translation.is_custom) continue;
    for (const [seasonKey, seasonMeta] of Object.entries(translation.seasons ?? {})) {
      const season = parseSeasonNumber(seasonKey);
      if (season === null) continue;
      const seasonEpisodes = normalizeEpisodes(seasonMeta?.episodes ?? []);
      if (!seasonEpisodes.length) continue;
      const list = candidates.get(season) ?? [];
      list.push({
        translationId: translation.id,
        title: seasonMeta?.title ?? null,
        episodes: seasonEpisodes,
      });
      candidates.set(season, list);
    }
  }

  const selectedId =
    selectedTranslationId === null || selectedTranslationId === undefined
      ? ""
      : String(selectedTranslationId);

  const kodikSeasons = new Set<number>(candidates.keys());
  for (const [seasonKey, seasonMeta] of Object.entries(seasons ?? {})) {
    const season = parseSeasonNumber(seasonKey);
    if (season === null) continue;
    if (normalizeEpisodes(Object.keys(seasonMeta?.episodes ?? {})).length > 0) {
      kodikSeasons.add(season);
    }
  }

  if (allowFlat && kodikSeasons.size <= 1) {
    const selectedTranslation = selectedId
      ? translations.find(
          (translation) => String(translation.id) === selectedId,
        )
      : undefined;
    const source =
      selectedTranslation ??
      translations.find(
        (translation) =>
          !translation.is_custom &&
          Object.values(translation.seasons ?? {}).some(
            (meta) => normalizeEpisodes(meta?.episodes ?? []).length > 0,
          ),
      );
    const flatEpisodes: number[] = [];
    const appendEpisodes = (meta?: PlayerSeasonMeta | null) => {
      const count = normalizeEpisodes(meta?.episodes ?? []).length;
      for (let index = 0; index < count; index++) {
        flatEpisodes.push(flatEpisodes.length + 1);
      }
    };
    for (const [, meta] of Object.entries(source?.seasons ?? {}).sort(
      ([a], [b]) => Number(a) - Number(b),
    )) {
      appendEpisodes(meta);
    }
    if (!flatEpisodes.length) {
      for (const meta of Object.values(seasons ?? {})) {
        appendEpisodes({
          episodes: normalizeEpisodes(Object.keys(meta?.episodes ?? {})),
        });
      }
    }
    if (!flatEpisodes.length) {
      const total = Math.max(1, Math.trunc(Number(episodes) || 1));
      for (let number = 1; number <= total; number++) {
        flatEpisodes.push(number);
      }
    }
    return [
      {
        season: 1,
        label: flatLabel,
        episodes: flatEpisodes,
        translationId: source?.id ?? null,
      },
    ];
  }

  const allGroups: PlayerEpisodeGroup[] = [];
  const selectedGroups: PlayerEpisodeGroup[] = [];
  const knownSeasons = new Set<number>();

  for (const [season, seasonCandidates] of candidates) {
    const selected = selectedId
      ? seasonCandidates.find(
          (candidate) => String(candidate.translationId) === selectedId,
        )
      : undefined;
    const chosen =
      selected ??
      [...seasonCandidates].sort(
        (a, b) => b.episodes.length - a.episodes.length,
      )[0];
    if (!chosen) continue;

    const group = {
      season,
      label: seasonLabel(season, chosen.title),
      episodes: [...chosen.episodes],
      translationId: chosen.translationId,
    };
    allGroups.push(group);
    if (selected) selectedGroups.push(group);
    knownSeasons.add(season);
  }

  const selectedCoverage = selectedGroups.reduce(
    (sum, group) => sum + group.episodes.length,
    0,
  );
  const bestTotal = Math.max(
    Number(episodes) || 0,
    ...translations.map((translation) => Number(translation.episodes_done) || 0),
    ...translations.map((translation) =>
      Object.values(translation.seasons ?? {}).reduce(
        (sum, meta) =>
          sum + normalizeEpisodes(meta?.episodes ?? []).length,
        0,
      ),
    ),
    selectedCoverage,
  );

  const groups =
    candidates.size <= 1 && selectedGroups.length && selectedCoverage >= bestTotal
      ? selectedGroups
      : allGroups;

  const specialGroup = groups.find((group) => group.season === 0);
  const regularGroups = groups.filter((group) => group.season > 0);
  if (specialGroup && regularGroups.length === 1) {
    const regularGroup = regularGroups[0];
    if (regularGroup) {
      const explicitRegularLimit = Math.max(
        0,
        Math.trunc(Number(episodes) || 0),
        ...((candidates.get(regularGroup.season) ?? [])
          .filter((candidate) =>
            (candidates.get(0) ?? []).some(
              (special) => String(special.translationId) === String(candidate.translationId),
            ),
          )
          .map((candidate) => candidate.episodes.length)),
      );
      if (
        explicitRegularLimit > 0 &&
        regularGroup.episodes.length > explicitRegularLimit
      ) {
        regularGroup.episodes = regularGroup.episodes.slice(0, explicitRegularLimit);
      }
    }
  }

  if (!groups.length || !bestTotal || selectedCoverage < bestTotal) {
    for (const [seasonKey, seasonMeta] of Object.entries(seasons ?? {})) {
      const season = parseSeasonNumber(seasonKey);
      if (season === null || knownSeasons.has(season)) continue;
      const seasonEpisodes = normalizeEpisodes(
        Object.keys(seasonMeta?.episodes ?? {}),
      );
      if (!seasonEpisodes.length) continue;

      groups.push({
        season,
        label: seasonLabel(season),
        episodes: seasonEpisodes,
        translationId: null,
      });
      knownSeasons.add(season);
    }
  }

  if (!groups.length) {
    const totalEpisodes = Math.max(1, Math.trunc(Number(episodes) || 1));
    const fallbackSeason = Number(lastSeason);
    const season =
      Number.isInteger(fallbackSeason) && fallbackSeason > 0
        ? fallbackSeason
        : 1;
    groups.push({
      season,
      label: seasonLabel(season),
      episodes: Array.from({ length: totalEpisodes }, (_, index) => index + 1),
      translationId: null,
    });
  }

  return groups.sort((a, b) => a.season - b.season);
};

export const resolveDefaultSeason = (
  groups: PlayerEpisodeGroup[],
  requestedSeason?: number | null,
  lastSeason?: number | null,
): number => {
  const hasRequested =
    requestedSeason !== null && requestedSeason !== undefined;
  const requested = Number(requestedSeason);
  if (
    hasRequested &&
    Number.isInteger(requested) &&
    requested >= 0 &&
    groups.some((group) => group.season === requested)
  ) {
    return requested;
  }

  const hasPreferred = lastSeason !== null && lastSeason !== undefined;
  const preferred = Number(lastSeason);
  if (
    hasPreferred &&
    Number.isInteger(preferred) &&
    preferred >= 0 &&
    groups.some((group) => group.season === preferred)
  ) {
    return preferred;
  }

  const regularSeasons = groups.filter((group) => group.season > 0);
  const fallback = regularSeasons.at(-1) ?? groups.at(-1);
  return fallback?.season ?? 1;
};

export const episodeForSeason = (
  groups: PlayerEpisodeGroup[],
  season: number,
  episode: number,
): number => {
  const group = groups.find((item) => item.season === season);
  if (!group) return Math.max(1, Math.trunc(Number(episode) || 1));

  const requested = Number(episode);
  if (Number.isInteger(requested) && group.episodes.includes(requested)) {
    return requested;
  }
  return group.episodes[0] ?? 1;
};

export const orderedForPlayback = (
  groups: PlayerEpisodeGroup[],
): PlayerEpisodeGroup[] =>
  [...groups].sort((a, b) => {
    const specialA = a.season === 0 ? 1 : 0;
    const specialB = b.season === 0 ? 1 : 0;
    return specialA - specialB || a.season - b.season;
  });

export const resolveEpisodeTarget = (
  groups: PlayerEpisodeGroup[],
  season: number,
  episode: number,
): { season: number; episode: number } => {
  const ordered = orderedForPlayback(groups);
  const requestedEpisode = Math.max(1, Math.trunc(Number(episode) || 1));
  const groupIndex = ordered.findIndex((group) => group.season === season);

  if (groupIndex >= 0) {
    const group = ordered[groupIndex];
    if (group?.episodes.includes(requestedEpisode)) {
      return { season, episode: requestedEpisode };
    }
    const nextEpisode = group?.episodes.find(
      (number) => number >= requestedEpisode,
    );
    if (nextEpisode !== undefined) {
      return { season, episode: nextEpisode };
    }
    const nextGroup = ordered[groupIndex + 1];
    if (nextGroup?.episodes[0] !== undefined) {
      return { season: nextGroup.season, episode: nextGroup.episodes[0] };
    }
    const lastEpisode = group?.episodes.at(-1);
    if (lastEpisode !== undefined) {
      return { season, episode: lastEpisode };
    }
  }

  const nextGroup = ordered.find((group) => group.season >= season);
  if (nextGroup?.episodes[0] !== undefined) {
    return { season: nextGroup.season, episode: nextGroup.episodes[0] };
  }
  const lastGroup = [...groups].sort((a, b) => a.season - b.season).at(-1);
  return {
    season: lastGroup?.season ?? Math.max(0, season),
    episode: lastGroup?.episodes.at(-1) ?? requestedEpisode,
  };
};

export const nextEpisodeInGroups = (
  groups: PlayerEpisodeGroup[],
  season: number,
  episode: number,
): { season: number; episode: number } | null => {
  const ordered = orderedForPlayback(groups);
  const groupIndex = ordered.findIndex((group) => group.season === season);
  if (groupIndex < 0) return null;

  const group = ordered[groupIndex];
  if (!group) return null;

  const episodeIndex = group.episodes.indexOf(episode);
  const nextEpisode = group.episodes[episodeIndex + 1];
  if (episodeIndex >= 0 && nextEpisode !== undefined) {
    return { season, episode: nextEpisode };
  }

  const nextGroup = ordered[groupIndex + 1];
  const firstEpisode = nextGroup?.episodes[0];
  if (nextGroup && firstEpisode !== undefined) {
    return { season: nextGroup.season, episode: firstEpisode };
  }
  return null;
};
