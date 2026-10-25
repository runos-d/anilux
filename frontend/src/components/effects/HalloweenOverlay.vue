<template>
  <div class="hw-overlay" aria-hidden="true">
    <!-- ── Определения (рисуются один раз, используются через <use>) ── -->
    <svg class="hw-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Контур тыквы -->
        <path
          id="hw-pkp"
          d="M0,-9 C-6,-14 -17,-12 -19,-2 C-21,8 -12,14 -6,13 C-3,15 3,15 6,13 C12,14 21,8 19,-2 C17,-12 6,-14 0,-9 Z"
        />
        <clipPath id="hw-pkclip"><use href="#hw-pkp" /></clipPath>

        <!-- Тыква-джек: заливка → тень → рёбра → контур → стебель → светящееся лицо → блик -->
        <g id="hw-pk">
          <use href="#hw-pkp" class="hw-pk-fill" />
          <g clip-path="url(#hw-pkclip)">
            <path class="hw-pk-shade" d="M24,-14 C24,6 12,16 -2,16 C12,10 16,0 12,-14 Z" />
            <path class="hw-pk-rib" d="M-7,-12 C-11,-3 -11,6 -7,14 M7,-12 C11,-3 11,6 7,14" />
            <path class="hw-pk-hatch" d="M10,6 L14,2 M7,10 L12,5.4 M13,-2 L16,-4.6" />
          </g>
          <use href="#hw-pkp" class="hw-pk-ink" />
          <path class="hw-pk-stem" d="M-1.8,-9 C-1.4,-14 2,-16.6 5.6,-16.6 L6.6,-13.4 C3.6,-13.2 2.6,-11.4 3,-9 Z" />
          <path class="hw-pk-eye" d="M-10,-1 L-4,-1 L-7,-6.6 Z" />
          <path class="hw-pk-eye" d="M4,-1 L10,-1 L7,-6.6 Z" />
          <path class="hw-pk-mouth" d="M-9.4,3.2 L-5.6,2.2 L-3.4,6 L0,3 L3.4,6 L5.6,2.2 L9.4,3.2 C7.4,10.4 -7.4,10.4 -9.4,3.2 Z" />
          <path class="hw-pk-gloss" d="M-14.6,-5.4 C-15,-8.4 -12.6,-10.6 -9.8,-10.4" />
          <circle class="hw-pk-dot" cx="-15.4" cy="-1.4" r="1" />
        </g>

        <!-- Призрак -->
        <path
          id="hw-ghp"
          d="M0,-14 C-9,-14 -14,-7 -14,2 L-14,14 Q-11,11 -8,14 Q-4,17.4 0,14 Q4,11 8,14 Q11,17.4 14,14 L14,2 C14,-7 9,-14 0,-14 Z"
        />
        <clipPath id="hw-ghclip"><use href="#hw-ghp" /></clipPath>
        <g id="hw-gh">
          <use href="#hw-ghp" class="hw-gh-fill" />
          <g clip-path="url(#hw-ghclip)">
            <path class="hw-gh-shade" d="M20,-16 C20,4 12,16 3,17 C10,8 11,-4 8,-16 Z" />
            <path class="hw-gh-hatch" d="M10,6 L13.4,2.4 M8,10 L12,6" />
          </g>
          <use href="#hw-ghp" class="hw-gh-ink" />
          <ellipse class="hw-gh-eye" cx="-5" cy="-3" rx="2.6" ry="3.6" />
          <ellipse class="hw-gh-eye" cx="5" cy="-3" rx="2.6" ry="3.6" />
          <circle class="hw-gh-glint" cx="-5.9" cy="-4.4" r="1" />
          <circle class="hw-gh-glint" cx="4.1" cy="-4.4" r="1" />
          <ellipse class="hw-gh-blush" cx="-9" cy="2.4" rx="2.2" ry="1.2" />
          <ellipse class="hw-gh-blush" cx="9" cy="2.4" rx="2.2" ry="1.2" />
          <ellipse class="hw-gh-mouth" cx="0" cy="3.6" rx="1.8" ry="2.2" />
          <path class="hw-gh-gloss" d="M-10.4,-6 C-10.6,-9 -8.6,-11 -6,-11.4" />
        </g>

        <!-- Летучая мышь -->
        <g id="hw-bt">
          <path
            class="hw-bt-wing"
            d="M0,-3 C-3,-9 -6,-6 -8,-9.4 C-10,-6 -14,-6.4 -17.6,-2 C-13.6,-2 -12.6,1 -11.6,4.6 C-8.6,0.6 -6.4,2.6 -4,6 L4,6 C6.4,2.6 8.6,0.6 11.6,4.6 C12.6,1 13.6,-2 17.6,-2 C14,-6.4 10,-6 8,-9.4 C6,-6 3,-9 0,-3 Z"
          />
          <path class="hw-bt-bone" d="M-4,-1 L-14,-2.4 M-4,0 L-10.6,3.2 M4,-1 L14,-2.4 M4,0 L10.6,3.2" />
          <ellipse class="hw-bt-body" cx="0" cy="1.6" rx="4" ry="6" />
          <path class="hw-bt-ear" d="M-3.6,-4.6 L-4.8,-11 L0,-5.6 Z M3.6,-4.6 L4.8,-11 L0,-5.6 Z" />
          <circle class="hw-bt-eye" cx="-1.7" cy="-1.4" r="1.4" />
          <circle class="hw-bt-eye" cx="1.7" cy="-1.4" r="1.4" />
          <circle class="hw-bt-pupil" cx="-1.7" cy="-1.2" r="0.62" />
          <circle class="hw-bt-pupil" cx="1.7" cy="-1.2" r="0.62" />
          <path class="hw-bt-fang" d="M-1.4,1.4 L-0.7,3.4 L0,1.4 L0.7,3.4 L1.4,1.4 Z" />
        </g>

        <!-- Завёрнутая конфета -->
        <clipPath id="hw-cdclip"><ellipse cx="0" cy="0" rx="7.4" ry="5.6" /></clipPath>
        <g id="hw-cd">
          <path class="hw-cd-wrap" d="M-6,0 L-14.4,-5.6 C-12.6,-2 -12.6,2 -14.4,5.6 Z" />
          <path class="hw-cd-wrap" d="M6,0 L14.4,-5.6 C12.6,-2 12.6,2 14.4,5.6 Z" />
          <ellipse class="hw-cd-body" cx="0" cy="0" rx="7.4" ry="5.6" />
          <g clip-path="url(#hw-cdclip)">
            <path class="hw-cd-shade" d="M-9,3 C-3,6 5,6 9,2 L9,7 L-9,7 Z" />
            <path class="hw-cd-stripe" d="M-4,-6 L-1,6 M2,-6 L5,6" />
          </g>
          <ellipse class="hw-cd-ink" cx="0" cy="0" rx="7.4" ry="5.6" />
          <path class="hw-cd-gloss" d="M-4.6,-2.4 C-3.6,-3.6 -2,-4 -0.6,-3.6" />
        </g>

        <!-- Четырёхконечная звезда-искра -->
        <g id="hw-st">
          <path
            class="hw-st-body"
            d="M0,-11 C1,-3.5 3.5,-1 11,0 C3.5,1 1,3.5 0,11 C-1,3.5 -3.5,1 -11,0 C-3.5,-1 -1,-3.5 0,-11 Z"
          />
          <circle class="hw-st-core" r="2" />
        </g>

        <!-- Паучок -->
        <g id="hw-sp">
          <g class="hw-sp-legs-ink">
            <path d="M-4,-1 L-12,-8 L-16,-2 M-4.4,2 L-14,1 L-17,8 M-3.6,5 L-11,10 L-11,16 M-2,7 L-6,13 L-5,18" />
            <path d="M4,-1 L12,-8 L16,-2 M4.4,2 L14,1 L17,8 M3.6,5 L11,10 L11,16 M2,7 L6,13 L5,18" />
          </g>
          <g class="hw-sp-legs">
            <path d="M-4,-1 L-12,-8 L-16,-2 M-4.4,2 L-14,1 L-17,8 M-3.6,5 L-11,10 L-11,16 M-2,7 L-6,13 L-5,18" />
            <path d="M4,-1 L12,-8 L16,-2 M4.4,2 L14,1 L17,8 M3.6,5 L11,10 L11,16 M2,7 L6,13 L5,18" />
          </g>
          <ellipse class="hw-sp-abd" cx="0" cy="6" rx="7.4" ry="8.6" />
          <path class="hw-sp-abd-shade" d="M7,4 C7,10 3,14.4 -1,14.6 C4,11 5,7 4,1 Z" />
          <ellipse class="hw-sp-ink" cx="0" cy="6" rx="7.4" ry="8.6" />
          <path class="hw-sp-mark" d="M0,1 C-2.4,4 -3,6 0,10 C3,6 2.4,4 0,1 Z" />
          <circle class="hw-sp-head" cx="0" cy="-5.4" r="5.6" />
          <ellipse class="hw-sp-eye" cx="-2.3" cy="-5.6" rx="1.7" ry="2.1" />
          <ellipse class="hw-sp-eye" cx="2.3" cy="-5.6" rx="1.7" ry="2.1" />
          <circle class="hw-sp-glint" cx="-2.9" cy="-6.4" r="0.7" />
          <circle class="hw-sp-glint" cx="1.7" cy="-6.4" r="0.7" />
        </g>
      </defs>
    </svg>

    <!-- ── Растровые полутона (скринтон) ── -->
    <div class="hw-tone"></div>

    <!-- ── Манга-линии скорости ── -->
    <svg class="hw-rays" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="xMidYMid slice">
      <path
        v-for="r in rays"
        :key="r.key"
        :d="r.d"
        :class="r.white ? 'hw-ray hw-ray-w' : 'hw-ray'"
      />
    </svg>

    <!-- ── Аура: пульсирующая тыква по центру ── -->
    <!-- <div class="hw-aura">
      <svg viewBox="-100 -100 200 200" class="hw-aura-svg">
        <defs>
          <radialGradient id="hw-aura-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#ff9a3d" stop-opacity="0.34" />
            <stop offset="55%" stop-color="#a06bff" stop-opacity="0.12" />
            <stop offset="100%" stop-color="#a06bff" stop-opacity="0" />
          </radialGradient>
        </defs>
        <path
          class="hw-aura-pk"
          fill="url(#hw-aura-grad)"
          d="M0,-9 C-6,-14 -17,-12 -19,-2 C-21,8 -12,14 -6,13 C-3,15 3,15 6,13 C12,14 21,8 19,-2 C17,-12 6,-14 0,-9 Z"
          transform="scale(4.4)"
        />
      </svg>
    </div> -->

    <!-- Мягкая вспышка (молния) -->
    <!-- <div class="hw-flash"></div> -->

    <!-- ── Летающие призраки и летучие мыши ── -->
    <div
      v-for="f in flyers"
      :key="f.id"
      class="hw-fly"
      :class="f.dir"
      :style="f.style"
    >
      <div class="hw-fly-bob">
        <svg viewBox="-18 -18 36 36" class="hw-fly-svg" :class="f.bat ? 'hw-fly-flap' : ''">
          <use :href="f.ref" />
        </svg>
      </div>
    </div>

    <!-- ── Гирлянда по периметру: чернильный шнур + тыквы, призраки, конфеты ── -->
    <!-- <svg class="hw-frame" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="none">
      <g class="hw-cord-group">
        <path :d="framePath" class="hw-cord-ink" />
        <path :d="framePath" class="hw-cord-col" />
      </g>
      <g v-for="f in frameItems" :key="f.key" :transform="f.transform">
        <use :href="f.ref" class="hw-frame-i" :style="f.style" />
      </g>
    </svg> -->

    <!-- ── Уголки: паутина, паук на нити, тыква, летучая мышь ── -->
    <!-- <svg
      v-for="c in corners"
      :key="c"
      :class="`hw-corner hw-corner-${c}`"
      viewBox="0 0 200 200"
    >
      <g class="hw-web">
        <path class="hw-web-ink" :d="WEB.rings" />
        <path class="hw-web-ink" :d="WEB.rays" />
        <path class="hw-web-line" :d="WEB.rings" />
        <path class="hw-web-line hw-web-line-r" :d="WEB.rays" />
      </g>

      <g v-if="c === 'tl' || c === 'tr'" class="hw-sp-swing">
        <line class="hw-thread-ink" x1="148" y1="0" x2="148" y2="72" />
        <line class="hw-thread" x1="148" y1="0" x2="148" y2="72" />
        <use href="#hw-sp" transform="translate(148 86) scale(1.5)" />
      </g>

        <g
          v-if="c === 'bl' || c === 'br'"
          :transform="c === 'br' ? 'translate(154 156)' : 'translate(46 156)'"
        >
        <g class="hw-corner-beat">
          <use href="#hw-pk" transform="scale(2.2) rotate(-6)" style="--color:#ff8a1f" />
        </g>
      </g>

      <use href="#hw-cd" transform="translate(104 168) rotate(-16) scale(1.1)" style="--color:#ff4f93" />
      <use href="#hw-cd" transform="translate(14 104) rotate(60) scale(0.9)" style="--color:#7be0ff" />

      <g transform="translate(112 118)">
        <g class="hw-corner-bat">
          <use href="#hw-bt" transform="scale(1.4)" style="--color:#6b46c1" />
        </g>
      </g>

      <use
        v-for="(s, i) in CORNER_STARS"
        :key="`cs${i}`"
        href="#hw-st"
        class="hw-corner-star"
        :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
        :style="{ '--color': s.c, animationDelay: s.d + 's' }"
      />
    </svg> -->

    <div class="hw-layer hw-far">
      <span v-for="it in items.far" :key="it.id" class="hw-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="hw-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <div class="hw-layer hw-mid">
      <span v-for="it in items.mid" :key="it.id" class="hw-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="hw-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <div class="hw-layer hw-near">
      <span v-for="it in items.near" :key="it.id" class="hw-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="hw-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- <svg class="hw-sfx hw-sfx-1" viewBox="0 0 240 100">
      <g class="hw-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="hw-sfx-outer">ゾクゾク</text>
        <text x="112" y="66" text-anchor="middle" class="hw-sfx-text">ゾクゾク</text>
        <use href="#hw-pk" transform="translate(214 30) rotate(14) scale(1.3)" style="--color:#ff8a1f" />
      </g>
    </svg>
    <svg class="hw-sfx hw-sfx-2" viewBox="0 0 240 100">
      <g class="hw-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="hw-sfx-outer">ドロドロ</text>
        <text x="112" y="66" text-anchor="middle" class="hw-sfx-text hw-sfx-text-alt">ドロドロ</text>
        <use href="#hw-gh" transform="translate(214 30) rotate(-12) scale(1.4)" style="--color:#ffffff" />
      </g>
    </svg> -->

    <div class="hw-sparks">
      <span v-for="s in sparks" :key="`s${s.id}`" class="hw-spark" :style="s.style">
        <svg viewBox="-14 -14 28 28" class="hw-spark-svg">
          <use href="#hw-st" />
        </svg>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

type Vars = Record<string, string>;
interface Pt { x: number; y: number }
type Range = readonly [number, number];

interface LayerConf {
  size: Range;
  dur: Range;
  driftX: Range;
  sway: Range;
  op: Range;
  amp: Range;
}

const rnd = (a: number, b: number) => a + Math.random() * (b - a);
const pick = <T,>(arr: readonly T[]): T =>
  arr[Math.floor(Math.random() * arr.length)] as T;

const seeded = (seed: number) => () => {
  seed = (seed * 1664525 + 1013904223) % 4294967296;
  return seed / 4294967296;
};

const PUMPKIN_COLORS = ["#ff8a1f", "#ff6a00", "#ffa63d"] as const;
const GHOST_COLORS = ["#ffffff", "#efe6ff", "#d9ccff"] as const;
const CANDY_COLORS = ["#ff4f93", "#7be0ff", "#b98bff", "#8affd1", "#ffd166"] as const;
const BAT_COLORS = ["#6b46c1", "#4b2f94", "#8a5cff"] as const;
const STAR_COLORS = ["#ffd166", "#fff6d6", "#b98bff", "#8affd1"] as const;
const FRAME_REFS = ["#hw-pk", "#hw-cd", "#hw-gh", "#hw-bt", "#hw-st"] as const;

const colorFor = (ref: string): string => {
  switch (ref) {
    case "#hw-pk": return pick(PUMPKIN_COLORS);
    case "#hw-gh": return pick(GHOST_COLORS);
    case "#hw-cd": return pick(CANDY_COLORS);
    case "#hw-bt": return pick(BAT_COLORS);
    default: return pick(STAR_COLORS);
  }
};

const corners = ["tl", "tr", "bl", "br"] as const;

const w = ref(1280);
const h = ref(720);
let raf = 0;
const measure = () => {
  w.value = document.documentElement.clientWidth || window.innerWidth;
  h.value = window.innerHeight;
};
const onResize = () => {
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(measure);
};
onMounted(() => {
  measure();
  window.addEventListener("resize", onResize, { passive: true });
});
onBeforeUnmount(() => {
  cancelAnimationFrame(raf);
  window.removeEventListener("resize", onResize);
});

const counts = computed(() => {
  const small = w.value < 640;
  return {
    far: small ? 10 : 16,
    mid: small ? 8 : 12,
    near: small ? 4 : 7,
    sparks: small ? 10 : 16,
    frame: small ? 20 : 32,
    rays: small ? 38 : 64,
    ghosts: small ? 1 : 2,
    bats: small ? 3 : 5,
  };
});

const WEB = (() => {
  const R = 178;
  const RAYS = 7;
  const RINGS = 6;
  const angles = Array.from({ length: RAYS }, (_, i) => (i / (RAYS - 1)) * (Math.PI / 2));
  let rays = "";
  for (const a of angles) {
    rays += `M0,0 L${(Math.cos(a) * R).toFixed(1)},${(Math.sin(a) * R).toFixed(1)} `;
  }
  let rings = "";
  for (let k = 1; k <= RINGS; k++) {
    const r = (R * k) / RINGS;
    for (let i = 0; i < RAYS - 1; i++) {
      const a0 = angles[i] as number;
      const a1 = angles[i + 1] as number;
      const am = (a0 + a1) / 2;
      rings +=
        `M${(Math.cos(a0) * r).toFixed(1)},${(Math.sin(a0) * r).toFixed(1)} ` +
        `Q${(Math.cos(am) * r * 0.82).toFixed(1)},${(Math.sin(am) * r * 0.82).toFixed(1)} ` +
        `${(Math.cos(a1) * r).toFixed(1)},${(Math.sin(a1) * r).toFixed(1)} `;
    }
  }
  return { rays, rings };
})();

const CORNER_STARS = [
  { x: 180, y: 130, s: 1.0, c: "#ffd166", d: 0 },
  { x: 176, y: 170, s: 0.6, c: "#ffffff", d: 0.8 },
  { x: 84, y: 190, s: 0.55, c: "#b98bff", d: 1.9 },
  { x: 24, y: 130, s: 0.7, c: "#8affd1", d: 1.4 },
] as const;

const LAYERS: Record<"far" | "mid" | "near", LayerConf> = {
  far: {
    size: [11, 17], dur: [24, 36], driftX: [-24, 24],
    sway: [3.4, 5.2], op: [0.6, 0.8], amp: [6, 12],
  },
  mid: {
    size: [18, 28], dur: [18, 28], driftX: [-36, 36],
    sway: [2.8, 4.4], op: [0.85, 1], amp: [10, 20],
  },
  near: {
    size: [30, 46], dur: [14, 22], driftX: [-48, 48],
    sway: [2.2, 3.6], op: [0.95, 1], amp: [14, 26],
  },
};

const buildItems = (count: number, layer: "far" | "mid" | "near") => {
  const conf = LAYERS[layer];
  const out: { id: string; ref: string; style: Vars }[] = [];
  for (let i = 0; i < count; i++) {
    const size = rnd(conf.size[0], conf.size[1]);
    const dur = rnd(conf.dur[0], conf.dur[1]);

    let ref = "#hw-st";
    if (layer === "near") ref = (["#hw-pk", "#hw-cd", "#hw-bt"] as const)[i % 3] as string;
    else if (layer === "mid") ref = (["#hw-pk", "#hw-cd", "#hw-st", "#hw-bt"] as const)[i % 4] as string;
    else ref = (["#hw-st", "#hw-cd", "#hw-st", "#hw-pk", "#hw-st"] as const)[i % 5] as string;

    out.push({
      id: `${layer}${i}`,
      ref,
      style: {
        "--left": `${rnd(0, 100).toFixed(2)}%`,
        "--size": `${size.toFixed(1)}px`,
        "--dur": `${dur.toFixed(1)}s`,
        "--delay": `${(-rnd(0, dur)).toFixed(1)}s`,
        "--drift": `${rnd(conf.driftX[0], conf.driftX[1]).toFixed(0)}px`,
        "--sway-dur": `${rnd(conf.sway[0], conf.sway[1]).toFixed(2)}s`,
        "--sway-amp": `${rnd(conf.amp[0], conf.amp[1]).toFixed(1)}px`,
        "--op": rnd(conf.op[0], conf.op[1]).toFixed(2),
        "--color": colorFor(ref),
        "--spin-dur": `${rnd(10, 22).toFixed(1)}s`,
        "--tw-dur": `${rnd(1.2, 2.2).toFixed(2)}s`,
      },
    });
  }
  return out;
};

const items = computed(() => ({
  far: buildItems(counts.value.far, "far"),
  mid: buildItems(counts.value.mid, "mid"),
  near: buildItems(counts.value.near, "near"),
}));

const flyers = computed(() => {
  const out: { id: string; ref: string; bat: boolean; dir: string; style: Vars }[] = [];
  for (let i = 0; i < counts.value.ghosts; i++) {
    out.push({
      id: `fg${i}`,
      ref: "#hw-gh",
      bat: false,
      dir: i % 2 ? "hw-l" : "hw-r",
      style: {
        "--top": `${(24 + i * 34).toFixed(0)}%`,
        "--w": `${(84 - i * 16).toFixed(0)}px`,
        "--dur": `${(58 + i * 12).toFixed(0)}s`,
        "--delay": `-${(16 + i * 26).toFixed(0)}s`,
        "--bob": `${(4.6 + i).toFixed(1)}s`,
        "--color": "#ffffff",
        "--op": "0.55",
      } as Vars,
    });
  }
  for (let i = 0; i < counts.value.bats; i++) {
    out.push({
      id: `fb${i}`,
      ref: "#hw-bt",
      bat: true,
      dir: i % 2 ? "hw-l" : "hw-r",
      style: {
        "--top": `${rnd(6, 50).toFixed(1)}%`,
        "--w": `${rnd(48, 76).toFixed(0)}px`,
        "--dur": `${rnd(16, 28).toFixed(1)}s`,
        "--delay": `-${rnd(0, 26).toFixed(1)}s`,
        "--bob": `${rnd(1.8, 3).toFixed(1)}s`,
        "--color": pick(BAT_COLORS),
        "--op": "0.95",
      } as Vars,
    });
  }
  return out;
});

const rays = computed(() => {
  const W = w.value, H = h.value;
  const cx = W / 2, cy = H / 2;
  const rOut = Math.hypot(W, H) * 0.6;
  const rIn = rOut * 0.5;
  const rand = seeded(1031);
  const N = counts.value.rays;
  const out: { key: string; d: string; white: boolean }[] = [];
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2 + rand() * 0.05;
    const half = 0.008 + rand() * 0.022;
    const ri = rIn * (0.9 + rand() * 0.25);
    const p0: Pt = { x: cx + Math.cos(a) * ri, y: cy + Math.sin(a) * ri };
    const p1: Pt = { x: cx + Math.cos(a - half) * rOut, y: cy + Math.sin(a - half) * rOut };
    const p2: Pt = { x: cx + Math.cos(a + half) * rOut, y: cy + Math.sin(a + half) * rOut };
    out.push({
      key: `r${i}`,
      white: i % 3 === 0,
      d: `M${p0.x.toFixed(1)},${p0.y.toFixed(1)} L${p1.x.toFixed(1)},${p1.y.toFixed(1)} L${p2.x.toFixed(1)},${p2.y.toFixed(1)} Z`,
    });
  }
  return out;
});

const INSET = 10;
const framePath = computed(() => {
  const W = w.value, H = h.value;
  const x0 = INSET, x1 = W - INSET;
  const y0 = INSET, y1 = H - INSET;
  const sag = 7;
  const step = 130;
  const segs: string[] = [];
  const nx = Math.max(2, Math.round((x1 - x0) / step));
  const sx = (x1 - x0) / nx;
  for (let i = 0; i < nx; i++) {
    const a = x0 + i * sx, b = a + sx, m = (a + b) / 2;
    segs.push(`M${a.toFixed(1)},${y0} Q${m.toFixed(1)},${(y0 + sag).toFixed(1)} ${b.toFixed(1)},${y0}`);
    segs.push(`M${a.toFixed(1)},${y1} Q${m.toFixed(1)},${(y1 - sag).toFixed(1)} ${b.toFixed(1)},${y1}`);
  }
  const ny = Math.max(2, Math.round((y1 - y0) / step));
  const sy = (y1 - y0) / ny;
  for (let j = 0; j < ny; j++) {
    const a = y0 + j * sy, b = a + sy, m = (a + b) / 2;
    segs.push(`M${x0},${a.toFixed(1)} Q${(x0 + sag).toFixed(1)},${m.toFixed(1)} ${x0},${b.toFixed(1)}`);
    segs.push(`M${x1},${a.toFixed(1)} Q${(x1 - sag).toFixed(1)},${m.toFixed(1)} ${x1},${b.toFixed(1)}`);
  }
  return segs.join(" ");
});

const frameItems = computed(() => {
  const W = w.value, H = h.value;
  const x0 = INSET, x1 = W - INSET;
  const y0 = INSET, y1 = H - INSET;
  const total = counts.value.frame;
  const per = 2 * (x1 - x0) + 2 * (y1 - y0);
  const topLen = x1 - x0;
  const rightLen = y1 - y0;
  const out: { key: string; ref: string; transform: string; style: Vars }[] = [];
  for (let i = 0; i < total; i++) {
    const d = ((i + 0.5) / total) * per;
    let pt: Pt;
    if (d < topLen) pt = { x: x0 + d, y: y0 };
    else if (d < topLen + rightLen) pt = { x: x1, y: y0 + (d - topLen) };
    else if (d < topLen * 2 + rightLen) pt = { x: x1 - (d - topLen - rightLen), y: y1 };
    else pt = { x: x0, y: y1 - (d - topLen * 2 - rightLen) };
    const ref = FRAME_REFS[i % FRAME_REFS.length] as string;
    const rot = ((i * 37) % 30) - 15;
    out.push({
      key: `fi${i}`,
      ref,
      transform: `translate(${pt.x.toFixed(1)} ${pt.y.toFixed(1)}) rotate(${rot}) scale(0.6)`,
      style: {
        "--color": colorFor(ref),
        animationDelay: `${((i * 0.37) % 3).toFixed(2)}s`,
      },
    });
  }
  return out;
});

const sparks = computed(() =>
  Array.from({ length: counts.value.sparks }, (_, id) => ({
    id,
    style: {
      "--left": `${rnd(0, 100).toFixed(2)}%`,
      "--size": `${rnd(9, 18).toFixed(1)}px`,
      "--dur": `${rnd(12, 22).toFixed(1)}s`,
      "--delay": `-${rnd(0, 20).toFixed(1)}s`,
      "--drift": `${rnd(-40, 40).toFixed(0)}px`,
      "--color": pick(["#ff8a1f", "#ffd166", "#b98bff", "#8affd1"] as const),
      "--tw": `${rnd(1.2, 2.4).toFixed(2)}s`,
    } as Vars,
  })),
);
</script>

<style scoped>
.hw-overlay {
  position: fixed;
  opacity: 0.5 !important;
  inset: 0;
  z-index: 9995;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --hw-ink: #1d0d33;
  --hw-orange: #ff8a1f;
  --hw-purple: #8a5cff;
  --hw-glow: #ffe066;
  --hw-aura-1: rgba(255, 140, 50, 0.3);
  --hw-aura-2: rgba(150, 100, 255, 0.18);
  --hw-ray: rgba(138, 92, 255, 0.001);
  --hw-ray-w: rgba(255, 190, 120, 0.001);
  --hw-tone: rgba(138, 92, 255, 0.001);
}

:global(html[data-theme="dark"]) .hw-overlay,
:global(body.theme-dark) .hw-overlay {
  --hw-aura-1: rgba(255, 150, 70, 0.38);
  --hw-aura-2: rgba(170, 120, 255, 0.22);
  --hw-ray: rgba(160, 120, 255, 0.26);
  --hw-ray-w: rgba(255, 200, 140, 0.22);
  --hw-tone: rgba(160, 120, 255, 0.36);
}

.hw-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

/* ══════ Тыква: заливка / тень / рёбра / контур / лицо / блик ══════ */
.hw-pk-fill { fill: var(--color, #ff8a1f); stroke: none; }
.hw-pk-shade { fill: color-mix(in srgb, var(--color, #ff8a1f) 58%, #7a1f00); }
.hw-pk-rib {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #ff8a1f) 55%, #7a1f00);
  stroke-width: 1.2;
  stroke-linecap: round;
}
.hw-pk-hatch {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
.hw-pk-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
.hw-pk-stem {
  fill: #5fcf5a;
  stroke: var(--hw-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.hw-pk-eye,
.hw-pk-mouth {
  fill: var(--hw-glow);
  stroke: var(--hw-ink);
  stroke-width: 1.4;
  stroke-linejoin: round;
}
.hw-pk-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}
.hw-pk-dot { fill: #fff; }

/* ══════ Призрак ══════ */
.hw-gh-fill { fill: var(--color, #fff); stroke: none; }
.hw-gh-shade { fill: color-mix(in srgb, var(--color, #fff) 70%, #8a6cd6); }
.hw-gh-hatch {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.35;
}
.hw-gh-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
.hw-gh-eye { fill: var(--hw-ink); }
.hw-gh-glint { fill: #fff; }
.hw-gh-blush { fill: #ff8ac2; opacity: 0.7; }
.hw-gh-mouth { fill: var(--hw-ink); }
.hw-gh-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
  opacity: 0.9;
}

/* ══════ Летучая мышь ══════ */
.hw-bt-wing {
  fill: var(--color, #6b46c1);
  stroke: var(--hw-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}
.hw-bt-bone {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.5;
}
.hw-bt-body {
  fill: color-mix(in srgb, var(--color, #6b46c1) 75%, #fff);
  stroke: var(--hw-ink);
  stroke-width: 2;
}
.hw-bt-ear {
  fill: color-mix(in srgb, var(--color, #6b46c1) 75%, #fff);
  stroke: var(--hw-ink);
  stroke-width: 1.6;
  stroke-linejoin: round;
}
.hw-bt-eye { fill: #fff; stroke: var(--hw-ink); stroke-width: 0.9; }
.hw-bt-pupil { fill: var(--hw-ink); }
.hw-bt-fang { fill: #fff; stroke: var(--hw-ink); stroke-width: 0.7; stroke-linejoin: round; }

/* ══════ Конфета ══════ */
.hw-cd-wrap {
  fill: #fff6d6;
  stroke: var(--hw-ink);
  stroke-width: 2;
  stroke-linejoin: round;
}
.hw-cd-body { fill: var(--color, #ff4f93); }
.hw-cd-shade { fill: color-mix(in srgb, var(--color, #ff4f93) 58%, #2a0a50); }
.hw-cd-stripe {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  opacity: 0.85;
}
.hw-cd-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.4;
}
.hw-cd-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.6;
  stroke-linecap: round;
}

/* ══════ Звезда ══════ */
.hw-st-body {
  fill: var(--color, #ffd166);
  stroke: var(--hw-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.hw-st-core { fill: #fff; }

/* ══════ Паучок ══════ */
.hw-sp-legs-ink path {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.hw-sp-legs path {
  fill: none;
  stroke: #7d5bd6;
  stroke-width: 1.6;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.hw-sp-abd { fill: #7d5bd6; }
.hw-sp-abd-shade { fill: #4b2f94; }
.hw-sp-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 2.4;
}
.hw-sp-mark { fill: #ff4d94; stroke: var(--hw-ink); stroke-width: 0.8; stroke-linejoin: round; }
.hw-sp-head {
  fill: #9a78ec;
  stroke: var(--hw-ink);
  stroke-width: 2.4;
}
.hw-sp-eye { fill: var(--hw-ink); }
.hw-sp-glint { fill: #fff; }

/* ══════ Растр + линии скорости ══════ */
.hw-tone {
  position: absolute;
  inset: -40%;
  background-image: radial-gradient(circle, var(--hw-tone) 1.3px, transparent 1.7px);
  background-size: 9px 9px;
  transform: rotate(15deg);
  -webkit-mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  opacity: 0.75;
}

.hw-rays {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  animation: hw-rays-shake 0.5s steps(2, jump-none) infinite;
}
.hw-ray { fill: var(--hw-ray); }
.hw-ray-w { fill: var(--hw-ray-w); }

@keyframes hw-rays-shake {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(1.5px, -1px) scale(1.012); }
}

/* ══════ Аура ══════ */
.hw-aura {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(80vmin, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  animation: hw-aura-pulse 4.4s ease-in-out infinite;
}
.hw-aura-svg { width: 100%; height: 100%; overflow: visible; }
.hw-aura-pk { filter: blur(6px); }

@keyframes hw-aura-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.94); opacity: 0.8; }
  50%      { transform: translate(-50%, -50%) scale(1.06); opacity: 1; }
}

/* ══════ Вспышка ══════ */
.hw-flash {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, var(--hw-aura-1), transparent 60%),
    radial-gradient(ellipse at 70% 60%, var(--hw-aura-2), transparent 60%);
  opacity: 0;
  animation: hw-flash 24s linear infinite;
}
@keyframes hw-flash {
  0%, 92.5%, 94.5%, 100% { opacity: 0; }
  93%   { opacity: 1; }
  94%   { opacity: 0.5; }
}

/* ══════ Летающие призраки и мыши ══════ */
.hw-fly {
  position: absolute;
  top: var(--top);
  left: 0;
  width: var(--w);
  opacity: var(--op, 0.9);
  color: var(--color, #fff);
  animation: hw-fly-r var(--dur) linear var(--delay) infinite;
  will-change: transform;
}
.hw-fly.hw-l { animation-name: hw-fly-l; }
.hw-fly.hw-l .hw-fly-svg { scale: -1 1; }

.hw-fly-bob { animation: hw-bob var(--bob, 2.4s) ease-in-out infinite alternate; }
.hw-fly-svg {
  display: block;
  width: 100%;
  overflow: visible;
}
.hw-fly-flap { animation: hw-flap 0.36s ease-in-out infinite alternate; transform-origin: 50% 50%; }

@keyframes hw-fly-r {
  0%   { transform: translate3d(-20vw, 0, 0); }
  100% { transform: translate3d(118vw, 0, 0); }
}
@keyframes hw-fly-l {
  0%   { transform: translate3d(118vw, 0, 0); }
  100% { transform: translate3d(-20vw, 0, 0); }
}
@keyframes hw-bob {
  from { transform: translateY(-14px) rotate(-5deg); }
  to   { transform: translateY(14px) rotate(5deg); }
}
@keyframes hw-flap {
  from { transform: scaleY(1); }
  to   { transform: scaleY(0.72); }
}

/* ══════ Гирлянда ══════ */
.hw-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.hw-cord-group {
  animation: hw-cord-sway 7s ease-in-out infinite alternate;
  will-change: transform;
}
@keyframes hw-cord-sway {
  from { transform: translateY(-1.2px); }
  to   { transform: translateY(1.2px); }
}
.hw-cord-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 4.4;
  stroke-linecap: round;
}
.hw-cord-col {
  fill: none;
  stroke: var(--hw-orange);
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-dasharray: 10 6;
}
.hw-frame-i { animation: hw-frame-twinkle 3s ease-in-out infinite; }
@keyframes hw-frame-twinkle {
  0%, 100% { opacity: 0.85; }
  50%      { opacity: 1; }
}

/* ══════ Уголки ══════ */
.hw-corner {
  position: absolute;
  width: clamp(120px, 18vw, 220px);
  height: clamp(120px, 18vw, 220px);
  overflow: visible;
}
.hw-corner-tl { top: 4px; left: 4px; }
.hw-corner-tr { top: 4px; right: 4px; }
.hw-corner-bl { bottom: 4px; left: 4px; }
.hw-corner-br { bottom: 4px; right: 4px; }

/* Зеркалится ТОЛЬКО паутина -под нужный угол.
   Паук, тыква, мышь, конфеты и звёзды остаются в нормальной ориентации. */
.hw-corner .hw-web {
  transform-box: fill-box;
  transform-origin: center;
}
.hw-corner-tr .hw-web { transform: scaleX(-1); }
.hw-corner-bl .hw-web { transform: scaleY(-1); }
.hw-corner-br .hw-web { transform: scale(-1, -1); }

.hw-web-ink {
  fill: none;
  stroke: var(--hw-ink);
  stroke-width: 4.6;
  stroke-linecap: round;
}
.hw-web-line {
  fill: none;
  stroke: #e9ddff;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.hw-web-line-r { stroke: #fff; stroke-width: 2; }

.hw-thread-ink { stroke: var(--hw-ink); stroke-width: 3.6; stroke-linecap: round; }
.hw-thread { stroke: #e9ddff; stroke-width: 1.4; stroke-linecap: round; }
.hw-sp-swing {
  transform-origin: 148px 0;
  animation: hw-sp-swing 3.2s ease-in-out infinite alternate;
}
@keyframes hw-sp-swing {
  from { transform: rotate(-5deg); }
  to   { transform: rotate(5deg); }
}

.hw-corner-beat {
  transform-box: fill-box;
  transform-origin: center;
  animation: hw-corner-beat 2s ease-in-out infinite;
}
@keyframes hw-corner-beat {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25%      { transform: scale(1.1) rotate(4deg); }
  50%      { transform: scale(0.98) rotate(0deg); }
  75%      { transform: scale(1.06) rotate(-4deg); }
}

.hw-corner-bat {
  transform-box: fill-box;
  transform-origin: center;
  animation: hw-corner-bat 1.8s ease-in-out infinite alternate;
}
@keyframes hw-corner-bat {
  from { transform: translateY(-3px) rotate(-6deg) scaleY(1); }
  to   { transform: translateY(4px) rotate(6deg) scaleY(0.82); }
}

.hw-corner-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: hw-corner-star 2.4s ease-in-out infinite;
}
@keyframes hw-corner-star {
  0%, 100% { opacity: 0.55; scale: 0.8; }
  50%      { opacity: 1;    scale: 1.2; }
}

/* ══════ Падающие предметы ══════ */
.hw-layer { position: absolute; inset: 0; }

.hw-item {
  position: absolute;
  top: calc(var(--size) * -2);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ff8a1f);
  opacity: 0;
  animation: hw-fall var(--dur) cubic-bezier(0.35, 0.05, 0.65, 0.95) var(--delay) infinite;
  will-change: transform, opacity;
}

@keyframes hw-fall {
  0% {
    transform: translate3d(0, 0, 0) scale(0.6);
    opacity: 0;
  }
  6% { opacity: var(--op, 0.9); }
  12% { transform: translate3d(calc(var(--drift) * 0.1), 12vh, 0) scale(1); }
  94% { opacity: var(--op, 0.9); }
  100% {
    transform: translate3d(var(--drift), 118vh, 0) scale(0.85);
    opacity: 0;
  }
}

.hw-item-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation:
    hw-sway var(--sway-dur) ease-in-out infinite alternate,
    hw-spin var(--spin-dur) ease-in-out infinite alternate,
    hw-twinkle var(--tw-dur, 1.6s) ease-in-out infinite;
}

@keyframes hw-sway {
  from { transform: translateX(calc(-1 * var(--sway-amp, 12px))); }
  to   { transform: translateX(var(--sway-amp, 12px)); }
}
@keyframes hw-spin {
  from { rotate: -16deg; }
  to   { rotate: 16deg; }
}
@keyframes hw-twinkle {
  0%, 100% { scale: 1; }
  20%      { scale: 1.1; }
  40%      { scale: 0.97; }
  60%      { scale: 1.05; }
}

/* ══════ Звуковые эффекты ══════ */
.hw-sfx {
  position: absolute;
  width: clamp(110px, 15vw, 210px);
  overflow: visible;
}
.hw-sfx-1 { left: 3vw; top: 40%; rotate: -10deg; }
.hw-sfx-2 { right: 3vw; top: 60%; rotate: 8deg; }
.hw-sfx-2 .hw-sfx-pop { animation-delay: 4.5s; }

.hw-sfx-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: hw-sfx-pop 9s ease-in-out infinite;
}

.hw-sfx-outer,
.hw-sfx-text {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans JP", Impact, sans-serif;
  font-size: 52px;
  font-weight: 900;
  letter-spacing: 2px;
  stroke-linejoin: round;
}
.hw-sfx-outer {
  fill: #fff;
  stroke: #fff;
  stroke-width: 15;
}
.hw-sfx-text {
  fill: #ff8a1f;
  stroke: var(--hw-ink);
  stroke-width: 6;
  paint-order: stroke fill;
}
.hw-sfx-text-alt { fill: #b98bff; }

@keyframes hw-sfx-pop {
  0%        { opacity: 0; transform: scale(0.2) rotate(-8deg); }
  4%        { opacity: 1; transform: scale(1.3) rotate(3deg); }
  8%        { transform: scale(1) rotate(0); }
  14%       { transform: scale(1.1); }
  20%       { transform: scale(1); }
  26%       { transform: scale(1.1); }
  32%       { transform: scale(1); opacity: 1; }
  40%, 100% { opacity: 0; transform: scale(0.6); }
}

/* ══════ Искры ══════ */
.hw-sparks { position: absolute; inset: 0; }

.hw-spark {
  position: absolute;
  bottom: -20px;
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ff8a1f);
  opacity: 0;
  animation: hw-spark-rise var(--dur) linear var(--delay) infinite;
  will-change: transform, opacity;
}
.hw-spark-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: hw-spark-twinkle var(--tw, 1.6s) ease-in-out infinite alternate;
}
@keyframes hw-spark-rise {
  0%   { transform: translate3d(0, 0, 0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.85; }
  100% { transform: translate3d(var(--drift), -108vh, 0); opacity: 0; }
}
@keyframes hw-spark-twinkle {
  from { scale: 0.55; rotate: 0deg; }
  to   { scale: 1.15; rotate: 45deg; }
}

/* ══════ Доступность и печать ══════ */
@media (prefers-reduced-motion: reduce) {
  .hw-overlay { display: none; }
}
@media print {
  .hw-overlay { display: none; }
}
</style>