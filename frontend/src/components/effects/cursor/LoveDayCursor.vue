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

const HEART = ["#ff4f93", "#ff7eb6", "#ff3b5c", "#ffa3c8", "#fff0f6", "#ffcf4a"] as const;
const STAR = ["#ffcf4a", "#fff0f6", "#ffa3c8"] as const;

const REFS = [
  { ref: "#vd-h", palette: HEART },
  { ref: "#vd-s", palette: STAR },
  { ref: "#vd-e", palette: HEART },
] as const;

const makeParticle = () => {
  const dur = rnd(1100, 1900);
  const item = pick(REFS);
  return {
    kind: "rise",
    ref: item.ref,
    life: dur,
    vars: {
      "--size": `${rnd(12, 18).toFixed(1)}px`,
      "--dur": `${dur.toFixed(0)}ms`,
      "--dx": `${rnd(-28, 28).toFixed(1)}px`,
      "--dy": `-${rnd(56, 100).toFixed(1)}px`,
      "--sway": `${rnd(8, 18).toFixed(0)}deg`,
      "--op": rnd(0.85, 1).toFixed(2),
      "--color": pick(item.palette),
    },
  };
};

const { particles } = useCursorTrail({
  makeParticle,
  maxParticles: 26,
  spawnIntervalMs: 60,
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
  --vd-ink: #3a0a26;
  --vd-gold: #ffcf4a;
}

.cursor-trail__p {
  position: absolute;
  left: 0;
  top: 0;
  width: var(--size);
  height: var(--size);
  transform: translate(-50%, -50%);
  color: var(--color, #ff4f93);
  opacity: 0;
  animation: cursor-rise var(--dur) cubic-bezier(0.24, 0.6, 0.4, 1) forwards;
  will-change: transform, opacity;
}

.cursor-trail__svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: cursor-sway calc(var(--dur) / 2.6) ease-in-out infinite alternate;
}

/* ── Те же чернильные стили, что в LoveDayOverlay ── */
:global(.vd-h-fill) { fill: var(--color, #ff4f93); stroke: none; }
:global(.vd-h-shade) { fill: color-mix(in srgb, var(--color, #ff4f93) 60%, #8a0f48); }
:global(.vd-h-hatch) {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
:global(.vd-h-ink) {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
:global(.vd-h-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 2.2;
  stroke-linecap: round;
}
:global(.vd-h-dot) { fill: #fff; }

:global(.vd-s-body) {
  fill: var(--color, #ffcf4a);
  stroke: var(--vd-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.vd-s-core) { fill: #fff; }

:global(.vd-e-body) {
  fill: #fff6fa;
  stroke: var(--vd-ink);
  stroke-width: 2.4;
  stroke-linejoin: round;
}
:global(.vd-e-flap) {
  fill: #ffd6e8;
  stroke: var(--vd-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
  stroke-linecap: round;
}
:global(.vd-e-fold) {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 1.4;
  stroke-linecap: round;
  opacity: 0.55;
}

@keyframes cursor-rise {
  0% {
    transform: translate(-50%, -50%) scale(0.35);
    opacity: 0;
  }
  16% {
    opacity: var(--op, 1);
  }
  100% {
    transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy))) scale(1);
    opacity: 0;
  }
}

@keyframes cursor-sway {
  from { transform: rotate(calc(var(--sway, 0deg) * -1)); }
  to   { transform: rotate(var(--sway, 0deg)); }
}

@media (prefers-reduced-motion: reduce) {
  .cursor-trail { display: none; }
}

@media print {
  .cursor-trail { display: none; }
}
</style>