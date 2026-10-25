import { describe, expect, it } from "vitest";
import {
  buildWheelGradient,
  clampSpinDuration,
  clampSpinSpeed,
  clampWeight,
  createPreset,
  entryProbability,
  getEligibleEntries,
  parseRouletteState,
  pickWeighted,
  wheelSegmentLanding,
  type RouletteEntry,
} from "./roulette";

const entry = (id: number, weight: number): RouletteEntry => ({
  anime: { id, title_ru: `Аниме ${id}` },
  weight,
  disabled: false,
});

describe("roulette helpers", () => {
  it("picks entries by their configured weight", () => {
    const entries = [entry(1, 1), entry(2, 3)];
    expect(pickWeighted(entries, 0)?.anime.id).toBe(1);
    expect(pickWeighted(entries, 0.26)?.anime.id).toBe(2);
    expect(entryProbability(entries[1]!, entries)).toBe(75);
  });

  it("inverts weights when the reverse mode is enabled", () => {
    const entries = [entry(1, 1), entry(2, 3)];
    expect(pickWeighted(entries, 0.49, true)?.anime.id).toBe(1);
    expect(pickWeighted(entries, 0.8, true)?.anime.id).toBe(2);
    expect(entryProbability(entries[0]!, entries, true)).toBeCloseTo(75);
  });

  it("accepts real-world donation weights and clamps spin settings", () => {
    expect(clampWeight(13_762)).toBe(13_762);
    expect(clampWeight(0)).toBe(0.01);
    expect(clampSpinDuration(99)).toBe(99);
    expect(clampSpinSpeed(137.26)).toBe(137.3);
    expect(clampSpinSpeed(50_000)).toBe(50_000);
  });

  it("lands at different safe points inside the selected segment", () => {
    const entries = [entry(1, 1), entry(2, 1)];
    expect(wheelSegmentLanding(entries[0]!, entries, false, 0)).toBeCloseTo(10.8);
    expect(wheelSegmentLanding(entries[0]!, entries, false, 1)).toBeCloseTo(169.2);
  });

  it("temporarily excludes recent results but relaxes the rule for a tiny set", () => {
    const preset = createPreset();
    preset.entries = [entry(1, 10), entry(2, 10)];
    preset.rules.avoidLast = 1;
    preset.history = [{ id: "h1", anime: preset.entries[0]!.anime, createdAt: new Date().toISOString() }];
    expect(getEligibleEntries(preset).map((item) => item.anime.id)).toEqual([2]);

    preset.entries[1]!.disabled = true;
    expect(getEligibleEntries(preset).map((item) => item.anime.id)).toEqual([1]);

    preset.entries[0]!.eliminated = true;
    expect(getEligibleEntries(preset)).toEqual([]);
  });

  it("builds a full conic gradient and rejects malformed persisted state", () => {
    const gradient = buildWheelGradient([entry(1, 1), entry(2, 1)]);
    expect(gradient).toContain("0.000deg 179.250deg");
    expect(gradient).toContain("180.000deg 359.250deg");
    expect(gradient).toContain("rgba(15, 12, 18, .72)");
    expect(parseRouletteState('{"version":1,"presets":[]}')).toBeNull();
  });
});
