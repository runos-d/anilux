import { describe, expect, it } from "vitest";
import {
  buildEpisodeGroups,
  episodeForSeason,
  hasTranslationSeason,
  nextEpisodeInGroups,
  resolveDefaultSeason,
  resolveEpisodeTarget,
} from "./playerSeasons";

const range = (from: number, to: number) =>
  Array.from({ length: to - from + 1 }, (_, index) => from + index);

const steponee = {
  id: 641,
  seasons: {
    "2": { title: null, episodes: range(1, 68) },
  },
  last_season: 2,
};

const miraidub = {
  id: 1060,
  seasons: {
    "0": { title: "Спешлы", episodes: range(1, 4) },
    "2": { title: null, episodes: range(1, 64) },
  },
  last_season: 2,
};

describe("playerSeasons", () => {
  it("keeps specials separate when the selected dub folds them into the season", () => {
    const groups = buildEpisodeGroups({
      translations: [steponee, miraidub],
      selectedTranslationId: 641,
      episodes: 64,
    });

    expect(groups).toEqual([
      {
        season: 0,
        label: "Спешлы",
        episodes: range(1, 4),
        translationId: 1060,
      },
      {
        season: 2,
        label: "Сезон 2",
        episodes: range(1, 64),
        translationId: 641,
      },
    ]);
  });

  it("switches the second-season source when MiraiDUB is selected", () => {
    const groups = buildEpisodeGroups({
      translations: [steponee, miraidub],
      selectedTranslationId: 1060,
    });

    expect(groups.find(group => group.season === 2)).toMatchObject({
      episodes: range(1, 64),
      translationId: 1060,
    });
  });

  it("falls back to anime seasons and last_season", () => {
    const groups = buildEpisodeGroups({
      episodes: 12,
      lastSeason: 2,
    });

    expect(groups).toEqual([
      {
        season: 2,
        label: "Сезон 2",
        episodes: range(1, 12),
        translationId: null,
      },
    ]);
    expect(resolveDefaultSeason(groups, 1, 2)).toBe(2);
    expect(resolveDefaultSeason(groups, 0, 2)).toBe(2);
  });

  it("resolves route seasons, clamps episodes and crosses season boundaries", () => {
    const groups = buildEpisodeGroups({
      translations: [steponee, miraidub],
      selectedTranslationId: 1060,
    });

    expect(resolveDefaultSeason(groups, 0, 2)).toBe(0);
    expect(resolveDefaultSeason(groups, null, 2)).toBe(2);
    expect(episodeForSeason(groups, 2, 64)).toBe(64);
    expect(episodeForSeason(groups, 2, 99)).toBe(1);
    expect(nextEpisodeInGroups(groups, 0, 4)).toBeNull();
    expect(nextEpisodeInGroups(groups, 2, 64)).toEqual({
      season: 0,
      episode: 1,
    });
  });

  it("resolves deep links across gaps and season boundaries", () => {
    const groups = buildEpisodeGroups({
      translations: [steponee, miraidub],
      selectedTranslationId: 1060,
    });

    expect(resolveEpisodeTarget(groups, 0, 5)).toEqual({
      season: 0,
      episode: 4,
    });
    expect(resolveEpisodeTarget(groups, 2, 65)).toEqual({
      season: 0,
      episode: 1,
    });
    expect(resolveEpisodeTarget(groups, 5, 1)).toEqual({
      season: 2,
      episode: 64,
    });
  });

  it("keeps Kodik season separation for flat-allowed titles", () => {
    const groups = buildEpisodeGroups({
      translations: [miraidub],
      selectedTranslationId: 1060,
      allowFlat: true,
      flatLabel: "Фильм",
    });

    expect(groups).toEqual([
      {
        season: 0,
        label: "Спешлы",
        episodes: range(1, 4),
        translationId: 1060,
      },
      {
        season: 2,
        label: "Сезон 2",
        episodes: range(1, 64),
        translationId: 1060,
      },
    ]);
  });

  it("flattens single-season movie translations into a plain list", () => {
    const movie = {
      id: 1060,
      seasons: {
        "2": { title: null, episodes: range(1, 64) },
      },
      last_season: 2,
    };

    const groups = buildEpisodeGroups({
      translations: [movie],
      selectedTranslationId: 1060,
      allowFlat: true,
      flatLabel: "Фильм",
    });

    expect(groups).toEqual([
      {
        season: 1,
        label: "Фильм",
        episodes: range(1, 64),
        translationId: 1060,
      },
    ]);
  });

  it("keeps fallback season separation for flat-allowed titles", () => {
    const groups = buildEpisodeGroups({
      seasons: {
        "0": { episodes: { "1": "a" } },
        "1": { episodes: { "1": "b", "2": "c" } },
      },
      allowFlat: true,
      flatLabel: "Фильм",
    });

    expect(groups).toEqual([
      {
        season: 0,
        label: "Спешл",
        episodes: [1],
        translationId: null,
      },
      {
        season: 1,
        label: "Сезон 1",
        episodes: [1, 2],
        translationId: null,
      },
    ]);
  });

  it("checks whether a translation itself has the requested season", () => {
    expect(hasTranslationSeason(miraidub, 0)).toBe(true);
    expect(hasTranslationSeason(steponee, 0)).toBe(false);
    expect(hasTranslationSeason(steponee, 2)).toBe(true);
  });
});
