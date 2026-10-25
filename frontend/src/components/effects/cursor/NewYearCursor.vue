<template>
  <div class="cursor-trail" aria-hidden="true">
    <span
      v-for="p in particles"
      :key="p.id"
      :class="['cursor-trail__p', `cursor-trail__p--${p.kind}`]"
      :style="p.style"
    >
      <svg viewBox="-18 -18 36 36" class="cursor-trail__svg">
        <use :href="p.ref" />
      </svg>
    </span>
  </div>
</template>

<script setup lang="ts">
import { pick, rnd, useCursorTrail } from "./useCursorTrail";

const SNOW = ["#ffffff", "#e4f5ff", "#bfe6ff", "#d6ecff"] as const;
const STAR = ["#ffcf4a", "#fff6d6", "#bfe6ff"] as const;
const BALL = ["#ff3b5c", "#3d8bff", "#ffcf4a", "#ff7eb6", "#27cf9a", "#b98bff"] as const;
const GIFT = ["#ff4f6e", "#3d8bff", "#27cf9a", "#b98bff"] as const;

const SPARKS = [
  { ref: "#ny-st", palette: STAR },
  { ref: "#ny-ball", palette: BALL },
  { ref: "#ny-gift", palette: GIFT },
] as const;

const FLAKES = [
  { ref: "#ny-sf", palette: SNOW },
] as const;

const makeParticle = (): {
  kind: string;
  ref: string;
  vars: Record<string, string>;
  life: number;
} => {
  if (Math.random() < 0.7) {
    const dur = rnd(560, 950);
    const item = pick(SPARKS);
    const vars: Record<string, string> = {
      "--size": `${rnd(11, 17).toFixed(1)}px`,
      "--dur": `${dur.toFixed(0)}ms`,
      "--dx": `${rnd(-16, 16).toFixed(1)}px`,
      "--dy": `-${rnd(36, 70).toFixed(1)}px`,
      "--op": rnd(0.85, 1).toFixed(2),
      "--color": pick(item.palette),
    };
    return { kind: "spark", ref: item.ref, life: dur, vars };
  }
  const dur = rnd(1000, 1700);
  const item = pick(FLAKES);
  const vars: Record<string, string> = {
    "--size": `${rnd(12, 18).toFixed(1)}px`,
    "--dur": `${dur.toFixed(0)}ms`,
    "--dx": `${rnd(-28, 28).toFixed(1)}px`,
    "--dy": `${rnd(44, 96).toFixed(1)}px`,
    "--sway": `${rnd(3, 9).toFixed(1)}px`,
    "--op": "0.9",
    "--color": pick(item.palette),
  };
  return { kind: "flake", ref: item.ref, life: dur, vars };
};

const { particles } = useCursorTrail({
  makeParticle,
  maxParticles: 30,
  spawnIntervalMs: 55,
  minMovePx: 20,
});
</script>

<style scoped>
.cursor-trail {
  position: fixed;
  inset: 0;
  z-index: 9999;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --ny-ink: #0b1d3f;
  --ny-gold: #ffcf4a;
}

.cursor-trail__p {
  position: absolute;
  left: 0;
  top: 0;
  width: var(--size);
  height: var(--size);
  transform: translate(-50%, -50%);
  color: var(--color, #ffffff);
  will-change: transform, opacity;
}

.cursor-trail__p--spark {
  opacity: 0;
  animation: cursor-rise var(--dur) ease-out forwards;
}

.cursor-trail__p--flake {
  opacity: 0;
  animation: cursor-drift var(--dur) ease-in forwards;
}

.cursor-trail__svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
}

.cursor-trail__p--spark .cursor-trail__svg {
  animation: cursor-twinkle var(--dur) ease-in-out forwards;
}

.cursor-trail__p--flake .cursor-trail__svg {
  animation: cursor-sway-flake calc(var(--dur) / 2) ease-in-out infinite alternate;
}

/* ── Те же чернильные стили, что в NewYearOverlay ── */
:global(.ny-sf-ink) {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 4.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
:global(.ny-sf-col) {
  fill: none;
  stroke: var(--color, #e4f5ff);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
:global(.ny-sf-core) {
  fill: var(--color, #e4f5ff);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
}
:global(.ny-sf-dot) { fill: #fff; }

:global(.ny-st-body) {
  fill: var(--color, #ffcf4a);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.ny-st-core) { fill: #fff; }

:global(.ny-b-fill) { fill: var(--color, #ff3b5c); }
:global(.ny-b-shade) { fill: color-mix(in srgb, var(--color, #ff3b5c) 58%, #10204a); }
:global(.ny-b-band) {
  fill: none;
  stroke: #fff;
  stroke-width: 2.4;
  opacity: 0.85;
}
:global(.ny-b-hatch) {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
:global(.ny-b-ink) {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 2.6;
}
:global(.ny-b-cap) {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.9;
  stroke-linejoin: round;
}
:global(.ny-b-loop) {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 1.6;
  stroke-linecap: round;
}
:global(.ny-b-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 2.2;
  stroke-linecap: round;
}
:global(.ny-b-dot) { fill: #fff; }

:global(.ny-g-body) {
  fill: var(--color, #ff4f6e);
  stroke: var(--ny-ink);
  stroke-width: 2.3;
  stroke-linejoin: round;
}
:global(.ny-g-shade) { fill: color-mix(in srgb, var(--color, #ff4f6e) 58%, #10204a); }
:global(.ny-g-lid) {
  fill: color-mix(in srgb, var(--color, #ff4f6e) 82%, #fff);
  stroke: var(--ny-ink);
  stroke-width: 2.3;
  stroke-linejoin: round;
}
:global(.ny-g-rib) {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.ny-g-bow) {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.9;
  stroke-linejoin: round;
}
:global(.ny-g-knot) {
  fill: #ffe38a;
  stroke: var(--ny-ink);
  stroke-width: 1.6;
}
:global(.ny-g-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
}

@keyframes cursor-rise {
  0% {
    transform: translate(-50%, -50%) scale(0.35);
    opacity: 0;
  }
  35% {
    opacity: var(--op, 1);
  }
  100% {
    transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) scale(1);
    opacity: 0;
  }
}

@keyframes cursor-drift {
  to {
    transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy)));
    opacity: 0;
  }
}

@keyframes cursor-twinkle {
  0% { scale: 0; rotate: 0deg; }
  40% { scale: 1.15; rotate: 25deg; }
  100% { scale: 1; rotate: 45deg; }
}

@keyframes cursor-sway-flake {
  from { transform: translateX(calc(var(--sway, 0px) * -1)) rotate(0deg); }
  to   { transform: translateX(var(--sway, 0px)) rotate(180deg); }
}

@media (prefers-reduced-motion: reduce) {
  .cursor-trail { display: none; }
}

@media print {
  .cursor-trail { display: none; }
}
</style>