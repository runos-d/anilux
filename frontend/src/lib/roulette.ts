import type { Anime } from "@/api/anime";

export const ROULETTE_COLORS = [
  "#3A86FF", // AniLux accent blue
  "#818CF8", // indigo genre accent
  "#263B70", // deep midnight blue
  "#45B8E8", // cyan signal
  "#FBBF24", // warm rating gold
  "#655CF0", // electric violet
  "#1C2945", // dark interface blue
  "#9BAAF5", // pale periwinkle
] as const;

export interface RouletteEntry {
  anime: Anime;
  weight: number;
  disabled: boolean;
  eliminated?: boolean;
  excludedByLibrary?: boolean;
  libraryStatus?: string;
}

export interface RouletteRules {
  excludeCompleted: boolean;
  excludeDropped: boolean;
  excludedLibraryStatuses: string[];
  avoidLast: number;
  eliminateWinner: boolean;
  inverseWeights: boolean;
  spinDurationSeconds: number;
  spinSpeedRpm: number;
}

export interface RouletteHistoryItem {
  id: string;
  anime: Anime;
  createdAt: string;
}

export interface RoulettePreset {
  id: string;
  name: string;
  entries: RouletteEntry[];
  rules: RouletteRules;
  history: RouletteHistoryItem[];
  createdAt: string;
  updatedAt: string;
}

export interface RouletteState {
  version: 1;
  activePresetId: string;
  presets: RoulettePreset[];
}

export const createId = (): string => {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

export const createPreset = (name = "Мой вечер"): RoulettePreset => {
  const now = new Date().toISOString();
  return {
    id: createId(),
    name,
    entries: [],
    rules: {
      excludeCompleted: true,
      excludeDropped: true,
      excludedLibraryStatuses: ["completed", "dropped"],
      avoidLast: 1,
      eliminateWinner: false,
      inverseWeights: false,
      spinDurationSeconds: 3.7,
      spinSpeedRpm: 100,
    },
    history: [],
    createdAt: now,
    updatedAt: now,
  };
};

export const createRouletteState = (): RouletteState => {
  const preset = createPreset();
  return { version: 1, activePresetId: preset.id, presets: [preset] };
};

export const clampWeight = (weight: number): number => {
  if (!Number.isFinite(weight)) return 1;
  return Math.min(1_000_000_000, Math.max(0.01, Math.round(weight * 100) / 100));
};

export const clampSpinDuration = (seconds: number): number => {
  if (!Number.isFinite(seconds)) return 3.7;
  return Math.max(0.1, Math.round(seconds * 10) / 10);
};

export const clampSpinSpeed = (rpm: number): number => {
  if (!Number.isFinite(rpm)) return 100;
  return Math.max(0.1, Math.round(rpm * 10) / 10);
};

export const isEntryExcluded = (entry: RouletteEntry): boolean =>
  entry.disabled || Boolean(entry.eliminated) || Boolean(entry.excludedByLibrary);

export const effectiveWeight = (entry: RouletteEntry, inverse = false): number =>
  inverse ? 1 / clampWeight(entry.weight) : clampWeight(entry.weight);

export const getEligibleEntries = (preset: RoulettePreset): RouletteEntry[] => {
  const recentIds = new Set(
    preset.history.slice(0, Math.max(0, preset.rules.avoidLast)).map((item) => item.anime.id),
  );
  const active = preset.entries.filter((entry) => !isEntryExcluded(entry));
  const withoutRecent = active.filter((entry) => !recentIds.has(entry.anime.id));
  return withoutRecent.length ? withoutRecent : active;
};

export const pickWeighted = (
  entries: RouletteEntry[],
  random = Math.random(),
  inverse = false,
): RouletteEntry | null => {
  if (!entries.length) return null;
  const total = entries.reduce((sum, entry) => sum + effectiveWeight(entry, inverse), 0);
  let cursor = Math.min(0.999999999, Math.max(0, random)) * total;
  for (const entry of entries) {
    cursor -= effectiveWeight(entry, inverse);
    if (cursor < 0) return entry;
  }
  return entries.at(-1) ?? null;
};

export const entryProbability = (
  entry: RouletteEntry,
  entries: RouletteEntry[],
  inverse = false,
): number => {
  const active = entries.filter((item) => !isEntryExcluded(item));
  const total = active.reduce((sum, item) => sum + effectiveWeight(item, inverse), 0);
  if (!total || isEntryExcluded(entry)) return 0;
  return (effectiveWeight(entry, inverse) / total) * 100;
};

export const buildWheelGradient = (entries: RouletteEntry[], inverse = false): string => {
  const active = entries.filter((entry) => !isEntryExcluded(entry));
  if (!active.length) return "conic-gradient(#e9d9f8 0deg 360deg)";
  const total = active.reduce((sum, entry) => sum + effectiveWeight(entry, inverse), 0);
  let angle = 0;
  const stops = active.map((entry, index) => {
    const start = angle;
    angle += (effectiveWeight(entry, inverse) / total) * 360;
    const divider = Math.min(.75, Math.max(.08, (angle - start) * .08));
    const colorEnd = Math.max(start, angle - divider);
    return `${ROULETTE_COLORS[index % ROULETTE_COLORS.length]} ${start.toFixed(3)}deg ${colorEnd.toFixed(3)}deg, rgba(15, 12, 18, .72) ${colorEnd.toFixed(3)}deg ${angle.toFixed(3)}deg`;
  });
  return `conic-gradient(from 0deg, ${stops.join(", ")})`;
};

export const wheelSegmentCenter = (
  target: RouletteEntry,
  entries: RouletteEntry[],
  inverse = false,
): number => {
  const active = entries.filter((entry) => !isEntryExcluded(entry));
  const total = active.reduce((sum, entry) => sum + effectiveWeight(entry, inverse), 0);
  let angle = 0;
  for (const entry of active) {
    const span = total ? (effectiveWeight(entry, inverse) / total) * 360 : 0;
    if (entry.anime.id === target.anime.id) return angle + span / 2;
    angle += span;
  }
  return 0;
};

export const wheelSegmentLanding = (
  target: RouletteEntry,
  entries: RouletteEntry[],
  inverse = false,
  random = Math.random(),
): number => {
  const active = entries.filter((entry) => !isEntryExcluded(entry));
  const total = active.reduce((sum, entry) => sum + effectiveWeight(entry, inverse), 0);
  let angle = 0;
  for (const entry of active) {
    const span = total ? (effectiveWeight(entry, inverse) / total) * 360 : 0;
    if (entry.anime.id === target.anime.id) {
      const positionInsideSegment = .06 + Math.min(1, Math.max(0, random)) * .88;
      return angle + span * positionInsideSegment;
    }
    angle += span;
  }
  return 0;
};

export const parseRouletteState = (raw: string | null): RouletteState | null => {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<RouletteState>;
    if (value.version !== 1 || !Array.isArray(value.presets) || !value.presets.length) return null;
    const validPresets = value.presets.filter((preset) =>
      preset && typeof preset.id === "string" && typeof preset.name === "string" && Array.isArray(preset.entries),
    );
    if (!validPresets.length) return null;
    const presets = validPresets.map((preset) => {
      const allowedLibraryStatuses = new Set(["started", "completed", "on_hold", "dropped", "planned"]);
      const legacyExcluded = [
        ...(preset.rules?.excludeCompleted ?? true ? ["completed"] : []),
        ...(preset.rules?.excludeDropped ?? true ? ["dropped"] : []),
      ];
      const excludedLibraryStatuses = Array.isArray(preset.rules?.excludedLibraryStatuses)
        ? preset.rules.excludedLibraryStatuses.filter((status): status is string => allowedLibraryStatuses.has(status))
        : legacyExcluded;
      return {
        ...preset,
        rules: {
        excludeCompleted: excludedLibraryStatuses.includes("completed"),
        excludeDropped: excludedLibraryStatuses.includes("dropped"),
        excludedLibraryStatuses,
        avoidLast: preset.rules?.avoidLast ?? 1,
        eliminateWinner: preset.rules?.eliminateWinner ?? false,
        inverseWeights: preset.rules?.inverseWeights ?? false,
        spinDurationSeconds: clampSpinDuration(preset.rules?.spinDurationSeconds ?? 3.7),
        spinSpeedRpm: clampSpinSpeed(preset.rules?.spinSpeedRpm ?? 100),
      },
        history: Array.isArray(preset.history) ? preset.history : [],
      };
    }) as RoulettePreset[];
    return {
      version: 1,
      activePresetId: presets.some((preset) => preset.id === value.activePresetId)
        ? String(value.activePresetId)
        : presets[0]!.id,
      presets,
    };
  } catch {
    return null;
  }
};
