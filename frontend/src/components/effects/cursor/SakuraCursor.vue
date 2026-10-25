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

const PETAL = ["#ff8fbd", "#ffb3d1", "#ffd3e5", "#fff0f6", "#ff6fa5"] as const;
const BLOSSOM = ["#ff8fbd", "#ffb3d1", "#ffd3e5", "#ff7fb2", "#fff0f6"] as const;
const STAR = ["#fff6d6", "#ffffff", "#ffd3e5"] as const;

const REFS = [
  { ref: "#sk-p", palette: PETAL },
  { ref: "#sk-bl", palette: BLOSSOM },
  { ref: "#sk-bud", palette: PETAL },
  { ref: "#sk-st", palette: STAR },
] as const;

const makeParticle = () => {
  const dur = rnd(900, 1700);
  const item = pick(REFS);
  return {
    kind: "drift",
    ref: item.ref,
    life: dur,
    vars: {
      "--size": `${rnd(11, 17).toFixed(1)}px`,
      "--dur": `${dur.toFixed(0)}ms`,
      "--dx": `${rnd(-46, 46).toFixed(1)}px`,
      "--dy": `${rnd(64, 132).toFixed(1)}px`,
      "--sway": `${rnd(4, 12).toFixed(1)}px`,
      "--r0": `${rnd(-45, 45).toFixed(0)}deg`,
      "--r1": `${rnd(140, 340).toFixed(0)}deg`,
      "--color": pick(item.palette),
    },
  };
};

const { particles } = useCursorTrail({
  makeParticle,
  maxParticles: 28,
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
  --sk-ink: #3b1630;
  --sk-gold: #ffcf4a;
}

.cursor-trail__p {
  position: absolute;
  left: 0;
  top: 0;
  width: var(--size);
  height: var(--size);
  transform: translate(-50%, -50%);
  color: var(--color, #ffb3d1);
  opacity: 0;
  animation: cursor-drift var(--dur) cubic-bezier(0.3, 0.05, 0.3, 1) forwards;
  will-change: transform, opacity;
}

.cursor-trail__svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: cursor-spin var(--dur) ease-in-out forwards;
}

/* ── Те же чернильные стили, что в SakuraOverlay ── */
:global(.sk-p-fill) { fill: var(--color, #ffb3d1); stroke: none; }
:global(.sk-p-shade) { fill: color-mix(in srgb, var(--color, #ffb3d1) 62%, #b0306a); }
:global(.sk-p-hatch) {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
:global(.sk-p-vein) {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #ffb3d1) 55%, #b0306a);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.8;
}
:global(.sk-p-ink) {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
:global(.sk-p-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}
:global(.sk-p-dot) { fill: #fff; }

:global(.sk-bp) {
  fill: var(--color, #ffb3d1);
  stroke: var(--sk-ink);
  stroke-width: 3.4;
  stroke-linejoin: round;
}
:global(.sk-bl-gloss path) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.4;
  stroke-linecap: round;
  opacity: 0.9;
}
:global(.sk-bl-ring) {
  fill: color-mix(in srgb, var(--color, #ffb3d1) 55%, #c0387a);
  stroke: none;
  opacity: 0.85;
}
:global(.sk-bl-stamen path) {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 1.1;
  stroke-linecap: round;
}
:global(.sk-bl-tip) {
  fill: var(--sk-gold);
  stroke: var(--sk-ink);
  stroke-width: 0.9;
}
:global(.sk-bl-core) {
  fill: var(--sk-gold);
  stroke: var(--sk-ink);
  stroke-width: 1.2;
}

:global(.sk-bud-body) { fill: var(--color, #ff8fbd); stroke: none; }
:global(.sk-bud-shade) { fill: color-mix(in srgb, var(--color, #ff8fbd) 58%, #b0306a); }
:global(.sk-bud-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.6;
  stroke-linecap: round;
}
:global(.sk-bud-cap) {
  fill: #5fcf8a;
  stroke: var(--sk-ink);
  stroke-width: 1.4;
  stroke-linejoin: round;
}

:global(.sk-st-body) {
  fill: var(--color, #fff6d6);
  stroke: var(--sk-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.sk-st-core) { fill: #fff; }

@keyframes cursor-drift {
  to {
    transform: translate(calc(-50% + var(--dx)), calc(-50% + var(--dy)));
    opacity: 0;
  }
}

@keyframes cursor-spin {
  0% {
    transform: translateX(calc(var(--sway, 0px) * -1)) rotate(var(--r0, 0deg));
  }
  50% {
    transform: translateX(var(--sway, 0px)) rotate(calc((var(--r0, 0deg) + var(--r1, 0deg)) / 2));
  }
  100% {
    transform: translateX(calc(var(--sway, 0px) * -1)) rotate(var(--r1, 0deg));
  }
}

@media (prefers-reduced-motion: reduce) {
  .cursor-trail { display: none; }
}

@media print {
  .cursor-trail { display: none; }
}
</style>