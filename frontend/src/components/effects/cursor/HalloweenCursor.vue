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

const PUMPKIN = ["#ff8a1f", "#ff6a00", "#ffa63d"] as const;
const GHOST = ["#ffffff", "#efe6ff", "#d9ccff"] as const;
const BAT = ["#6b46c1", "#4b2f94", "#8a5cff"] as const;
const CANDY = ["#ff4f93", "#7be0ff", "#b98bff", "#8affd1", "#ffd166"] as const;
const STAR = ["#ffd166", "#fff6d6", "#b98bff", "#8affd1"] as const;

const REFS = [
  { ref: "#hw-pk", palette: PUMPKIN },
  { ref: "#hw-gh", palette: GHOST },
  { ref: "#hw-bt", palette: BAT },
  { ref: "#hw-cd", palette: CANDY },
  { ref: "#hw-st", palette: STAR },
] as const;

const makeParticle = () => {
  const dur = rnd(900, 1500);
  const item = pick(REFS);
  return {
    kind: "rise",
    ref: item.ref,
    life: dur,
    vars: {
      "--size": `${rnd(14, 22).toFixed(1)}px`,
      "--dur": `${dur.toFixed(0)}ms`,
      "--dx": `${rnd(-24, 24).toFixed(1)}px`,
      "--dy": `-${rnd(40, 84).toFixed(1)}px`,
      "--sway": `${rnd(6, 14).toFixed(1)}deg`,
      "--op": rnd(0.85, 1).toFixed(2),
      "--color": pick(item.palette),
    },
  };
};

const { particles } = useCursorTrail({
  makeParticle,
  maxParticles: 28,
  spawnIntervalMs: 65,
  minMovePx: 22,
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
  --hw-ink: #1d0d33;
  --hw-glow: #ffe066;
}

.cursor-trail__p {
  position: absolute;
  left: 0;
  top: 0;
  width: var(--size);
  height: var(--size);
  transform: translate(-50%, -50%);
  color: var(--color, #ff8a1f);
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

/* ── Те же чернильные стили, что в HalloweenOverlay ── */
:global(.hw-pk-fill) { fill: var(--color, #ff8a1f); stroke: none; }
:global(.hw-pk-shade) { fill: color-mix(in srgb, var(--color, #ff8a1f) 58%, #7a1f00); }
:global(.hw-pk-rib) {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #ff8a1f) 55%, #7a1f00);
  stroke-width: 1.2;
  stroke-linecap: round;
}
:global(.hw-pk-hatch) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
:global(.hw-pk-ink) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
:global(.hw-pk-stem) {
  fill: #5fcf5a;
  stroke: var(--hw-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.hw-pk-eye),
:global(.hw-pk-mouth) {
  fill: var(--hw-glow);
  stroke: var(--hw-ink);
  stroke-width: 1.4;
  stroke-linejoin: round;
}
:global(.hw-pk-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}
:global(.hw-pk-dot) { fill: #fff; }

:global(.hw-gh-fill) { fill: var(--color, #fff); stroke: none; }
:global(.hw-gh-shade) { fill: color-mix(in srgb, var(--color, #fff) 70%, #8a6cd6); }
:global(.hw-gh-hatch) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.35;
}
:global(.hw-gh-ink) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
:global(.hw-gh-eye) { fill: var(--hw-ink); }
:global(.hw-gh-glint) { fill: #fff; }
:global(.hw-gh-blush) { fill: #ff8ac2; opacity: 0.7; }
:global(.hw-gh-mouth) { fill: var(--hw-ink); }
:global(.hw-gh-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
  opacity: 0.9;
}

:global(.hw-bt-wing) {
  fill: var(--color, #6b46c1);
  stroke: var(--hw-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}
:global(.hw-bt-bone) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.5;
}
:global(.hw-bt-body) {
  fill: color-mix(in srgb, var(--color, #6b46c1) 75%, #fff);
  stroke: var(--hw-ink);
  stroke-width: 2;
}
:global(.hw-bt-ear) {
  fill: color-mix(in srgb, var(--color, #6b46c1) 75%, #fff);
  stroke: var(--hw-ink);
  stroke-width: 1.6;
  stroke-linejoin: round;
}
:global(.hw-bt-eye) { fill: #fff; stroke: var(--hw-ink); stroke-width: 0.9; }
:global(.hw-bt-pupil) { fill: var(--hw-ink); }
:global(.hw-bt-fang) { fill: #fff; stroke: var(--hw-ink); stroke-width: 0.7; stroke-linejoin: round; }

:global(.hw-cd-wrap) {
  fill: #fff6d6;
  stroke: var(--hw-ink);
  stroke-width: 2;
  stroke-linejoin: round;
}
:global(.hw-cd-body) { fill: var(--color, #ff4f93); }
:global(.hw-cd-shade) { fill: color-mix(in srgb, var(--color, #ff4f93) 58%, #2a0a50); }
:global(.hw-cd-stripe) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  opacity: 0.85;
}
:global(.hw-cd-ink) {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.4;
}
:global(.hw-cd-gloss) {
  fill: none;
  stroke: #fff;
  stroke-width: 1.6;
  stroke-linecap: round;
}

:global(.hw-st-body) {
  fill: var(--color, #ffd166);
  stroke: var(--hw-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
:global(.hw-st-core) { fill: #fff; }

/* ── Общие keyframes (совпадают во всех курсорах) ── */
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