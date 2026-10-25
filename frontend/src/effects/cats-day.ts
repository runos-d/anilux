import type { EffectModule } from "@/lib/EffectsManager";

export interface CatsDayState {
  running: boolean;
  t0: number;
  w: number;
  h: number;
  rollSize: number;
  rollOpacity: number;
  trailWidth: number;
  trailOpacity: number;
  ballX: number;
  ballScale: number;
  ballRotation: number;
}

const SHRINK = 0.62;
const SPEED = 120; // px/s
const TRAIL_FADE = 1.6;
const PAUSE = 0.7;
const smooth = (x: number) => x * x * (3 - 2 * x);

export function createCatsDayModule(): EffectModule {
  const state: CatsDayState = {
    running: false,
    t0: 0,
    w: 1280,
    h: 720,
    rollSize: 62,
    rollOpacity: 1,
    trailWidth: 0,
    trailOpacity: 1,
    ballX: 0,
    ballScale: 1,
    ballRotation: 0,
  };

  return {
    name: "catsDay",
    init: () => {
      state.running = true;
      state.t0 = performance.now() - 2500;
    },
    update: () => {
      if (!state.running) return;
      state.w = typeof window !== "undefined" ? window.innerWidth : 1280;
      state.h = typeof window !== "undefined" ? window.innerHeight : 720;
      state.rollSize = state.w < 640 ? 46 : 62;

      const now = performance.now();
      const size = state.rollSize;
      const x0 = -size * 0.5;
      const x1 = state.w + size * 0.5;
      const D = x1 - x0;
      const T = D / SPEED;
      const cycle = T + TRAIL_FADE + PAUSE;
      const t = (((now - state.t0) / 1000) % cycle + cycle) % cycle;

      if (t < T) {
        const p = t / T;
        state.ballScale = 1 - SHRINK * p;
        state.ballX = x0 + D * p;
        const r0 = size * 0.4;
        state.ballRotation = ((D / (r0 * SHRINK)) * -Math.log(1 - SHRINK * p) * 180) / Math.PI;
        state.rollOpacity = 1;
        state.trailWidth = Math.max(0, Math.min(state.ballX, state.w));
        state.trailOpacity = 1;
      } else {
        state.rollOpacity = 0;
        state.trailWidth = state.w;
        const q = Math.min(1, (t - T) / TRAIL_FADE);
        state.trailOpacity = 1 - smooth(q);
      }
    },
    draw: () => {
    },
    resize: () => {
      state.w = typeof window !== "undefined" ? window.innerWidth : 1280;
      state.h = typeof window !== "undefined" ? window.innerHeight : 720;
      state.rollSize = state.w < 640 ? 46 : 62;
    },
    destroy: () => {
      state.running = false;
    },
  };
}
