<template>
  <div class="ny-overlay" aria-hidden="true">
    <!-- ── Определения (рисуются один раз, используются через <use>) ── -->
    <svg class="ny-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Луч снежинки: одна «ось» с зубцами -->
        <g id="ny-arm">
          <path
            d="M0,-14 L0,14 M0,-9 L-3.8,-13 M0,-9 L3.8,-13 M0,9 L-3.8,13 M0,9 L3.8,13 M0,-4.6 L-2.8,-7.4 M0,-4.6 L2.8,-7.4 M0,4.6 L-2.8,7.4 M0,4.6 L2.8,7.4"
          />
        </g>

        <!-- Снежинка в стиле манги: жирный контур → ледяная заливка → ядро -->
        <g id="ny-sf">
          <g class="ny-sf-ink">
            <use href="#ny-arm" />
            <use href="#ny-arm" transform="rotate(60)" />
            <use href="#ny-arm" transform="rotate(120)" />
          </g>
          <g class="ny-sf-col">
            <use href="#ny-arm" />
            <use href="#ny-arm" transform="rotate(60)" />
            <use href="#ny-arm" transform="rotate(120)" />
          </g>
          <circle class="ny-sf-core" r="3.4" />
          <circle class="ny-sf-dot" cx="-1.1" cy="-1.1" r="0.9" />
        </g>

        <!-- Четырёхконечная звезда-искра -->
        <g id="ny-st">
          <path
            class="ny-st-body"
            d="M0,-11 C1,-3.5 3.5,-1 11,0 C3.5,1 1,3.5 0,11 C-1,3.5 -3.5,1 -11,0 C-3.5,-1 -1,-3.5 0,-11 Z"
          />
          <circle class="ny-st-core" r="2" />
        </g>

        <!-- Ёлочный шар -->
        <clipPath id="ny-bclip"><circle cx="0" cy="3" r="11" /></clipPath>
        <g id="ny-ball">
          <circle class="ny-b-fill" cx="0" cy="3" r="11" />
          <g clip-path="url(#ny-bclip)">
            <path class="ny-b-shade" d="M14,3 C14,12 6,17 -2,15 C8,10 10,2 6,-8 L14,-8 Z" />
            <path class="ny-b-band" d="M-12,1 Q0,6 12,1" />
            <path class="ny-b-hatch" d="M6,9 L9.6,5.4 M3,11.8 L7.6,7.4 M9.4,2 L12,-0.6" />
          </g>
          <circle class="ny-b-ink" cx="0" cy="3" r="11" />
          <rect class="ny-b-cap" x="-3.6" y="-9.6" width="7.2" height="4.2" rx="1.2" />
          <path class="ny-b-loop" d="M-1.6,-9.6 C-1.6,-14.4 1.6,-14.4 1.6,-9.6" />
          <path class="ny-b-gloss" d="M-7.4,1 C-7.4,-2.6 -5,-4.8 -2,-5" />
          <circle class="ny-b-dot" cx="-8" cy="4.6" r="0.95" />
        </g>

        <!-- Подарок с бантом -->
        <g id="ny-gift">
          <rect class="ny-g-body" x="-10.5" y="-3" width="21" height="14" rx="1.4" />
          <path class="ny-g-shade" d="M5.5,-3 L10.5,-3 L10.5,11 L5.5,11 Z" />
          <rect class="ny-g-lid" x="-12.5" y="-8.6" width="25" height="6.4" rx="1.6" />
          <rect class="ny-g-rib" x="-2.6" y="-8.6" width="5.2" height="19.6" />
          <path class="ny-g-bow" d="M0,-8.6 C-4,-17 -11,-14.4 -8.4,-10.4 C-7,-8.4 -3,-8.4 0,-8.6 Z" />
          <path class="ny-g-bow" d="M0,-8.6 C4,-17 11,-14.4 8.4,-10.4 C7,-8.4 3,-8.4 0,-8.6 Z" />
          <circle class="ny-g-knot" cx="0" cy="-9" r="2.2" />
          <path class="ny-g-gloss" d="M-8.6,0.4 L-8.6,6" />
        </g>

        <!-- Лампочка гирлянды -->
        <g id="ny-bulb">
          <rect class="ny-l-cap" x="-2.8" y="1.2" width="5.6" height="4.4" rx="1" />
          <path class="ny-l-body" d="M-2.8,5.4 C-8,9 -7.6,17 0,21 C7.6,17 8,9 2.8,5.4 Z" />
          <path class="ny-l-gloss" d="M-4.4,9.6 C-5.2,12 -4.6,14.4 -3,16" />
        </g>

        <!-- Диагональная красно-белая полоска для леденца -->
        <pattern
          id="ny-stripe"
          width="15"
          height="15"
          patternUnits="userSpaceOnUse"
          patternTransform="rotate(38)"
        >
          <rect width="15" height="15" fill="#ffffff" />
          <rect width="7.5" height="15" fill="#e8213f" />
        </pattern>

        <!-- Леденец-трость: контур → полосатое тело → тень → блик -->
        <g id="ny-cane">
          <path class="ny-c-ink" d="M0,62 L0,-30 C0,-56 30,-56 30,-30" />
          <path
            class="ny-c-body"
            stroke="url(#ny-stripe)"
            d="M0,62 L0,-30 C0,-56 30,-56 30,-30"
          />
          <path class="ny-c-shade" d="M3.8,58 L3.8,-26" />
          <path class="ny-c-gloss" d="M-2.8,56 L-2.8,-24" />
        </g>

        <!-- Красная варежка: заливка → тень → штриховка → контур → блик -->
        <clipPath id="ny-mclip">
          <path d="M-10,4 L-10,-12 C-10,-24 10,-24 10,-12 L10,4 Z" />
        </clipPath>
        <g id="ny-mitten">
          <path class="ny-m-loop" d="M-2.2,-22.6 C-2.2,-30 2.2,-30 2.2,-22.6" />
          <path class="ny-m-fill" d="M-10,-9 C-19,-11 -22,-1 -16,4 C-14,6 -11,5 -10,3 Z" />
          <path class="ny-m-ink" d="M-10,-9 C-19,-11 -22,-1 -16,4 C-14,6 -11,5 -10,3 Z" />
          <path class="ny-m-fill" d="M-10,4 L-10,-12 C-10,-24 10,-24 10,-12 L10,4 Z" />
          <g clip-path="url(#ny-mclip)">
            <path class="ny-m-shade" d="M4,-28 C9,-14 8,-4 3,5 L14,5 L14,-28 Z" />
            <path class="ny-m-hatch" d="M6,-2 L9.4,-5.4 M3.4,1.4 L8,-3.2" />
          </g>
          <path class="ny-m-ink" d="M-10,4 L-10,-12 C-10,-24 10,-24 10,-12 L10,4 Z" />
          <circle class="ny-m-dot" cx="-3" cy="-13" r="1.5" />
          <circle class="ny-m-dot" cx="2.6" cy="-7.6" r="1.5" />
          <circle class="ny-m-dot" cx="-4.2" cy="-4" r="1.3" />
          <rect class="ny-m-cuff" x="-11.8" y="2" width="23.6" height="9.4" rx="2.6" />
          <path class="ny-m-fold" d="M-6,3.8 L-6,9.8 M0,3.8 L0,9.8 M6,3.8 L6,9.8" />
          <path class="ny-m-gloss" d="M-6.4,-18 C-8,-16 -8,-12 -7.6,-8" />
        </g>

        <!-- Бант на перекрестии -->
        <g id="ny-bow">
          <path class="ny-bw-tail" d="M-1,2 L-10,19 L-4,16 L0,21 Z" />
          <path class="ny-bw-tail" d="M1,2 L10,19 L4,16 L0,21 Z" />
          <path class="ny-bw" d="M0,0 C-4,-13 -22,-14 -20,-3 C-19,6 -8,5 0,0 Z" />
          <path class="ny-bw" d="M0,0 C4,-13 22,-14 20,-3 C19,6 8,5 0,0 Z" />
          <path class="ny-bw-fold" d="M-6,-5 C-11,-6 -14,-4 -15,-1 M6,-5 C11,-6 14,-4 15,-1" />
          <circle class="ny-bw-knot" r="4.4" />
        </g>

        <!-- Мини-версии для падающих предметов (вписываются в 36×36) -->
        <g id="ny-cane-mini">
          <use href="#ny-cane" transform="scale(0.28) translate(-15 -3)" />
        </g>
        <g id="ny-mitten-mini">
          <use href="#ny-mitten" transform="translate(5 6) scale(0.85)" />
        </g>

        <!-- Взрыв фейерверка (манга-стиль) -->
        <g id="ny-bu">
          <g class="ny-bu-ink">
            <path v-for="i in 12" :key="`i${i}`" :d="ray(i)" :transform="`rotate(${(i - 1) * 30})`" />
          </g>
          <g class="ny-bu-col">
            <path v-for="i in 12" :key="`c${i}`" :d="ray(i)" :transform="`rotate(${(i - 1) * 30})`" />
          </g>
          <circle
            v-for="i in 6"
            :key="`d${i}`"
            class="ny-bu-dot"
            cx="0"
            cy="-39"
            r="2.8"
            :transform="`rotate(${(i - 1) * 60})`"
          />
          <circle class="ny-bu-core" r="6.5" />
          <circle class="ny-bu-spot" r="2.6" />
        </g>
      </defs>
    </svg>

    <!-- ── Растровые полутона (скринтон) по краям ── -->
    <div class="ny-tone"></div>

    <!-- ── Манга-линии скорости (фокус на центр) ── -->
    <svg class="ny-rays" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="xMidYMid slice">
      <path
        v-for="r in rays"
        :key="r.key"
        :d="r.d"
        :class="r.white ? 'ny-ray ny-ray-w' : 'ny-ray'"
      />
    </svg>

    <!-- ── Аура: пульсирующая звезда по центру ── -->
    <!-- <div class="ny-aura">
      <svg viewBox="-100 -100 200 200" class="ny-aura-svg">
        <defs>
          <radialGradient id="ny-aura-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#9fe0ff" stop-opacity="0.34" />
            <stop offset="55%" stop-color="#b98bff" stop-opacity="0.1" />
            <stop offset="100%" stop-color="#b98bff" stop-opacity="0" />
          </radialGradient>
        </defs>
        <path class="ny-aura-star" fill="url(#ny-aura-grad)" :d="AURA_STAR" />
      </svg>
    </div> -->

    <!-- Мягкая вспышка -->
    <!-- <div class="ny-flash"></div> -->

    <!-- ── Фейерверки ── -->
    <!-- <svg
      v-for="(b, i) in BURSTS"
      :key="`bu${i}`"
      :class="`ny-burst ny-burst-${i + 1}`"
      viewBox="-48 -48 96 96"
    >
      <g class="ny-burst-pop" :style="{ '--color': b.c, animationDelay: b.d + 's' }">
        <use href="#ny-bu" />
      </g>
    </svg> -->

    <!-- ── Гирлянда по периметру: чернильный провод + лампочки ── -->
    <!-- <svg class="ny-garland" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="none">
      <defs>
        <radialGradient v-for="(color, i) in COLORS" :id="`ny-g${i}`" :key="color">
          <stop offset="0" :stop-color="color" stop-opacity="1" />
          <stop offset="0.35" :stop-color="color" stop-opacity="0.5" />
          <stop offset="1" :stop-color="color" stop-opacity="0" />
        </radialGradient>
      </defs>

      <g class="ny-wire-group">
        <path :d="wirePath" class="ny-wire-ink" />
        <path :d="wirePath" class="ny-wire-ice" />
        <path :d="wirePath" class="ny-runner" />
      </g>

      <g
        v-for="b in bulbs"
        :key="b.key"
        :transform="b.transform"
        class="ny-bulb"
        :style="{ '--d': b.delay, '--dd': b.dur }"
      >
        <circle class="ny-glow" cx="0" cy="12" r="19" :fill="`url(#ny-g${b.ci})`" />
        <use href="#ny-bulb" class="ny-bulb-use" :style="{ '--color': b.color }" />
      </g>
    </svg> -->

    <!-- ── Уголки: скрещённые леденцы, бант, звезда, шар, варежка и подарок ── -->
    <!-- <svg
      v-for="c in corners"
      :key="c"
      :class="`ny-corner ny-corner-${c}`"
      viewBox="0 0 200 200"
    >
      <g :transform="`translate(0 ${DY[c]})`">
        <use
          v-for="(k, i) in CANES"
          :key="`cn${i}`"
          href="#ny-cane"
          :transform="k.transform"
        />

        <g v-for="(b, i) in HANGS" :key="`hg${i}`">
          <line class="ny-thread-ink" :x1="b.x" :y1="b.y1" :x2="b.x" :y2="b.y2" />
          <line class="ny-thread" :x1="b.x" :y1="b.y1" :x2="b.x" :y2="b.y2" />
          <g :transform="`translate(${b.x} ${b.by})`">
            <g class="ny-swing" :style="{ animationDelay: b.d + 's' }">
              <use :href="b.ref" :transform="`scale(${b.s})`" :style="{ '--color': b.c }" />
            </g>
          </g>
        </g>

        <use href="#ny-bow" transform="translate(72 84) scale(1.15)" />

        <g transform="translate(72 34)">
          <g class="ny-corner-beat">
            <use href="#ny-st" transform="scale(1.3) rotate(8)" style="--color:#ffcf4a" />
          </g>
        </g>

        <use href="#ny-gift" transform="translate(148 150) rotate(-6) scale(1.45)" style="--color:#3d8bff" />

        <use
          v-for="(s, i) in CORNER_STARS"
          :key="`cs${i}`"
          href="#ny-st"
          class="ny-corner-star"
          :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
          :style="{ '--color': s.c, animationDelay: s.d + 's' }"
        />
      </g>
    </svg> -->

    <!-- ── Дальний слой ── -->
    <div class="ny-layer ny-far">
      <span v-for="it in items.far" :key="it.id" class="ny-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ny-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Средний слой ── -->
    <div class="ny-layer ny-mid">
      <span v-for="it in items.mid" :key="it.id" class="ny-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ny-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Ближний слой: крупные шары, подарки, леденцы, варежки ── -->
    <div class="ny-layer ny-near">
      <span v-for="it in items.near" :key="it.id" class="ny-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ny-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Звуковые эффекты (ономатопея) ── -->
    <!-- <svg class="ny-sfx ny-sfx-1" viewBox="0 0 240 100">
      <g class="ny-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="ny-sfx-outer">キラキラ</text>
        <text x="112" y="66" text-anchor="middle" class="ny-sfx-text">キラキラ</text>
        <use href="#ny-st" transform="translate(214 28) rotate(14) scale(1.5)" style="--color:#ffcf4a" />
      </g>
    </svg>
    <svg class="ny-sfx ny-sfx-2" viewBox="0 0 240 100">
      <g class="ny-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="ny-sfx-outer">ワクワク</text>
        <text x="112" y="66" text-anchor="middle" class="ny-sfx-text ny-sfx-text-alt">ワクワク</text>
        <use href="#ny-sf" transform="translate(214 30) rotate(-12) scale(1.3)" style="--color:#dff3ff" />
      </g>
    </svg> -->

    <!-- ── Искры-звёзды, поднимающиеся снизу ── -->
    <div class="ny-sparks">
      <span v-for="s in sparks" :key="`s${s.id}`" class="ny-spark" :style="s.style">
        <svg viewBox="-14 -14 28 28" class="ny-spark-svg">
          <use href="#ny-st" />
        </svg>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";

type Vars = Record<string, string>;
interface Pt { x: number; y: number }
interface Edge { p0: Pt; p2: Pt; c: Pt; hint: Pt }
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

const COLORS = ["#7be0ff", "#b98bff", "#ff8ac2", "#8affd1", "#ffd166"] as const;
const SNOW_COLORS = ["#ffffff", "#e4f5ff", "#bfe6ff", "#d6ecff"] as const;
const BALL_COLORS = ["#ff3b5c", "#3d8bff", "#ffcf4a", "#ff7eb6", "#27cf9a", "#b98bff"] as const;
const GIFT_COLORS = ["#ff4f6e", "#3d8bff", "#27cf9a", "#b98bff"] as const;
const STAR_COLORS = ["#ffcf4a", "#fff6d6", "#bfe6ff"] as const;

const SEGMENT = 150;
const SAG = 13;
const INSET = 1;

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
    rays: small ? 38 : 64,
  };
});

const AURA_STAR = (() => {
  const pts: string[] = [];
  const N = 16;
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2 - Math.PI / 2;
    const r = i % 2 === 0 ? 88 : 36;
    pts.push(`${(Math.cos(a) * r).toFixed(1)},${(Math.sin(a) * r).toFixed(1)}`);
  }
  return `M${pts.join(" L")} Z`;
})();

const ray = (i: number) => (i % 2 ? "M0,-11 L0,-33" : "M0,-11 L0,-24");

const BURSTS = [
  { c: "#ff4f93", d: 0 },
  { c: "#ffcf4a", d: 3 },
  { c: "#4fd0ff", d: 6 },
] as const;

const corners = ["tl", "tr", "bl", "br"] as const;
type Corner = (typeof corners)[number];

const DY: Record<Corner, number> = { tl: 0, tr: 0, bl: 26, br: 26 };

const CANES = [
  { transform: "translate(72 84) rotate(-24) scale(-1.15 1.15)" },
  { transform: "translate(72 84) rotate(24) scale(1.15)" },
] as const;

const HANGS = [
  { ref: "#ny-ball", x: 26, y1: 68, y2: 91, by: 106, s: 1.1, c: "#ff3b5c", d: 0 },
  { ref: "#ny-mitten", x: 118, y1: 68, y2: 81, by: 112, s: 1.15, c: "#e8213f", d: -1.4 },
] as const;

const CORNER_STARS = [
  { x: 172, y: 36, s: 1.2, c: "#ffcf4a", d: 0 },
  { x: 186, y: 84, s: 0.7, c: "#ffffff", d: 0.8 },
  { x: 128, y: 14, s: 0.55, c: "#bfe6ff", d: 1.9 },
  { x: 22, y: 150, s: 0.8, c: "#ffcf4a", d: 1.4 },
  { x: 72, y: 172, s: 0.6, c: "#ffffff", d: 0.4 },
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

    let ref = "#ny-sf";
    let color: string = pick(SNOW_COLORS);

    if (layer === "near") {
      const k = i % 5;
      if (k === 0) { ref = "#ny-gift"; color = pick(GIFT_COLORS); }
      else if (k === 1) { ref = "#ny-cane-mini"; }
      else if (k === 2) { ref = "#ny-ball"; color = pick(BALL_COLORS); }
      else if (k === 3) { ref = "#ny-mitten-mini"; }
    } else if (layer === "mid") {
      const k = i % 6;
      if (k === 5) { ref = "#ny-ball"; color = pick(BALL_COLORS); }
      else if (k === 4) { ref = "#ny-st"; color = pick(STAR_COLORS); }
      else if (k === 3) { ref = "#ny-mitten-mini"; }
      else if (k === 2) { ref = "#ny-cane-mini"; }
    } else {
      const k = i % 5;
      if (k === 4) { ref = "#ny-st"; color = pick(STAR_COLORS); }
      else if (k === 2) { ref = "#ny-cane-mini"; }
    }

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
        "--color": color,
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

const rays = computed(() => {
  const W = w.value, H = h.value;
  const cx = W / 2, cy = H / 2;
  const rOut = Math.hypot(W, H) * 0.6;
  const rIn = rOut * 0.5;
  const rand = seeded(2027);
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

const edges = computed<Edge[]>(() => {
  const W = w.value, H = h.value;
  const spanX = W - INSET * 2, spanY = H - INSET * 2;
  const nx = Math.max(2, Math.round(spanX / SEGMENT));
  const ny = Math.max(2, Math.round(spanY / SEGMENT));
  const sx = spanX / nx, sy = spanY / ny;
  const list: Edge[] = [];
  for (let i = 0; i < nx; i++) {
    const x0 = INSET + i * sx, x1 = x0 + sx, mx = (x0 + x1) / 2;
    list.push({ p0: { x: x0, y: INSET }, p2: { x: x1, y: INSET }, c: { x: mx, y: INSET + SAG * 2 }, hint: { x: 0, y: 1 } });
    list.push({ p0: { x: x0, y: H - INSET }, p2: { x: x1, y: H - INSET }, c: { x: mx, y: H - INSET - SAG * 2 }, hint: { x: 0, y: -1 } });
  }
  for (let j = 0; j < ny; j++) {
    const y0 = INSET + j * sy, y1 = y0 + sy, my = (y0 + y1) / 2;
    list.push({ p0: { x: INSET, y: y0 }, p2: { x: INSET, y: y1 }, c: { x: INSET + SAG * 2, y: my }, hint: { x: 1, y: 0 } });
    list.push({ p0: { x: W - INSET, y: y0 }, p2: { x: W - INSET, y: y1 }, c: { x: W - INSET - SAG * 2, y: my }, hint: { x: -1, y: 0 } });
  }
  return list;
});

const wirePath = computed(() =>
  edges.value
    .map((e) => `M${e.p0.x.toFixed(1)},${e.p0.y.toFixed(1)} Q${e.c.x.toFixed(1)},${e.c.y.toFixed(1)} ${e.p2.x.toFixed(1)},${e.p2.y.toFixed(1)}`)
    .join(" "),
);

const bulbs = computed(() => {
  const scale = w.value < 640 ? 0.85 : 1;
  const out: {
    key: string;
    transform: string;
    color: string;
    ci: number;
    delay: string;
    dur: string;
  }[] = [];
  let n = 0;
  edges.value.forEach((e, ei) => {
    const len = Math.hypot(e.p2.x - e.p0.x, e.p2.y - e.p0.y);
    const m = Math.min(4, Math.max(2, Math.round(len / 56)));
    for (let i = 0; i < m; i++) {
      const t = (i + 0.5) / m, u = 1 - t;
      const x = u * u * e.p0.x + 2 * u * t * e.c.x + t * t * e.p2.x;
      const y = u * u * e.p0.y + 2 * u * t * e.c.y + t * t * e.p2.y;
      let tx = 2 * u * (e.c.x - e.p0.x) + 2 * t * (e.p2.x - e.c.x);
      let ty = 2 * u * (e.c.y - e.p0.y) + 2 * t * (e.p2.y - e.c.y);
      const l = Math.hypot(tx, ty) || 1;
      tx /= l; ty /= l;
      let nx = -ty, ny = tx;
      if (nx * e.hint.x + ny * e.hint.y < 0) { nx = ty; ny = -tx; }
      const angle = (Math.atan2(ny, nx) * 180) / Math.PI - 90;
      const ci = n % COLORS.length;
      const color = COLORS[ci] ?? COLORS[0];
      const baseDur = [2.0, 2.8, 3.6, 2.4][n % 4] ?? 2.6;

      out.push({
        key: `${ei}-${i}`,
        transform: `translate(${x.toFixed(1)} ${y.toFixed(1)}) rotate(${angle.toFixed(1)}) scale(${scale})`,
        color,
        ci,
        delay: `-${((n * 0.37) % 4).toFixed(2)}s`,
        dur: `${(baseDur + (n % 5) * 0.1).toFixed(2)}s`,
      });
      n++;
    }
  });
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
      "--color": pick(STAR_COLORS),
      "--tw": `${rnd(1.2, 2.4).toFixed(2)}s`,
    } as Vars,
  })),
);
</script>

<style scoped>
.ny-overlay {
  position: fixed;
  opacity: 0.5 !important;
  inset: 0;
  z-index: 9997;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --ny-ink: #0b1d3f;
  --ny-gold: #ffcf4a;
  --ny-aura-1: rgba(120, 190, 255, 0.3);
  --ny-aura-2: rgba(200, 160, 255, 0.16);
  --ny-ray: rgba(80, 160, 255, 0.001);
  --ny-ray-w: rgba(10, 4, 4, 0.001);
  --ny-tone: rgba(80, 160, 255, 0.001);
}

:global(html[data-theme="dark"]) .ny-overlay,
:global(body.theme-dark) .ny-overlay {
  --ny-aura-1: rgba(140, 200, 255, 0.38);
  --ny-aura-2: rgba(210, 170, 255, 0.2);
  --ny-ray: rgba(130, 190, 255, 0.26);
  --ny-ray-w: rgba(235, 245, 255, 0.24);
  --ny-tone: rgba(130, 190, 255, 0.38);
}

.ny-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

/* ══════ Снежинка ══════ */
.ny-sf-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 4.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ny-sf-col {
  fill: none;
  stroke: var(--color, #e4f5ff);
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ny-sf-core {
  fill: var(--color, #e4f5ff);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
}
.ny-sf-dot { fill: #fff; }

/* ══════ Звезда ══════ */
.ny-st-body {
  fill: var(--color, #ffcf4a);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.ny-st-core { fill: #fff; }

/* ══════ Ёлочный шар ══════ */
.ny-b-fill { fill: var(--color, #ff3b5c); }
.ny-b-shade { fill: color-mix(in srgb, var(--color, #ff3b5c) 58%, #10204a); }
.ny-b-band {
  fill: none;
  stroke: #fff;
  stroke-width: 2.4;
  opacity: 0.85;
}
.ny-b-hatch {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
.ny-b-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 2.6;
}
.ny-b-cap {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.9;
  stroke-linejoin: round;
}
.ny-b-loop {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 1.6;
  stroke-linecap: round;
}
.ny-b-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2.2;
  stroke-linecap: round;
}
.ny-b-dot { fill: #fff; }

/* ══════ Подарок ══════ */
.ny-g-body {
  fill: var(--color, #ff4f6e);
  stroke: var(--ny-ink);
  stroke-width: 2.3;
  stroke-linejoin: round;
}
.ny-g-shade { fill: color-mix(in srgb, var(--color, #ff4f6e) 58%, #10204a); }
.ny-g-lid {
  fill: color-mix(in srgb, var(--color, #ff4f6e) 82%, #fff);
  stroke: var(--ny-ink);
  stroke-width: 2.3;
  stroke-linejoin: round;
}
.ny-g-rib {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.ny-g-bow {
  fill: var(--ny-gold);
  stroke: var(--ny-ink);
  stroke-width: 1.9;
  stroke-linejoin: round;
}
.ny-g-knot {
  fill: #ffe38a;
  stroke: var(--ny-ink);
  stroke-width: 1.6;
}
.ny-g-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
}

/* ══════ Лампочка ══════ */
.ny-l-cap {
  fill: #6d7fa8;
  stroke: var(--ny-ink);
  stroke-width: 1.6;
  stroke-linejoin: round;
}
.ny-l-body {
  fill: var(--color, #7be0ff);
  stroke: var(--ny-ink);
  stroke-width: 2;
  stroke-linejoin: round;
}
.ny-l-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.6;
  stroke-linecap: round;
}

/* ══════ Леденец-трость ══════ */
.ny-c-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 15;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ny-c-body {
  fill: none;
  stroke-width: 10.4;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ny-c-shade {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 2.4;
  stroke-linecap: round;
  opacity: 0.22;
}
.ny-c-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
  opacity: 0.75;
}

/* ══════ Красная варежка ══════ */
.ny-m-fill { fill: #e8213f; }
.ny-m-shade { fill: #a8122e; }
.ny-m-hatch {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.4;
}
.ny-m-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 2.4;
  stroke-linejoin: round;
}
.ny-m-loop {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 1.8;
  stroke-linecap: round;
}
.ny-m-dot { fill: #fff; }
.ny-m-cuff {
  fill: #fff;
  stroke: var(--ny-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}
.ny-m-fold {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 1.2;
  stroke-linecap: round;
  opacity: 0.3;
}
.ny-m-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
  opacity: 0.9;
}

/* ══════ Бант ══════ */
.ny-bw {
  fill: #2fb67f;
  stroke: var(--ny-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}
.ny-bw-tail {
  fill: #1b7f5c;
  stroke: var(--ny-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}
.ny-bw-fold {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 1.3;
  stroke-linecap: round;
  opacity: 0.45;
}
.ny-bw-knot {
  fill: #4fd9a0;
  stroke: var(--ny-ink);
  stroke-width: 2;
}

/* ══════ Взрыв фейерверка ══════ */
.ny-bu-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 7;
  stroke-linecap: round;
}
.ny-bu-col {
  fill: none;
  stroke: var(--color, #ffcf4a);
  stroke-width: 3.2;
  stroke-linecap: round;
}
.ny-bu-dot {
  fill: #fff;
  stroke: var(--ny-ink);
  stroke-width: 1.8;
}
.ny-bu-core {
  fill: var(--color, #ffcf4a);
  stroke: var(--ny-ink);
  stroke-width: 2.6;
}
.ny-bu-spot { fill: #fff; }

/* ══════ Растр + линии скорости ══════ */
.ny-tone {
  position: absolute;
  inset: -40%;
  background-image: radial-gradient(circle, var(--ny-tone) 1.3px, transparent 1.7px);
  background-size: 9px 9px;
  transform: rotate(15deg);
  -webkit-mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  opacity: 0.75;
}

.ny-rays {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  animation: ny-rays-shake 0.5s steps(2, jump-none) infinite;
}
.ny-ray { fill: var(--ny-ray); }
.ny-ray-w { fill: var(--ny-ray-w); }

@keyframes ny-rays-shake {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(1.5px, -1px) scale(1.012); }
}

/* ══════ Аура ══════ */
.ny-aura {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(80vmin, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  animation: ny-aura-pulse 4.4s ease-in-out infinite;
}
.ny-aura-svg { width: 100%; height: 100%; overflow: visible; }
.ny-aura-star { filter: blur(6px); }

@keyframes ny-aura-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.94) rotate(0deg); opacity: 0.8; }
  50%      { transform: translate(-50%, -50%) scale(1.06) rotate(6deg); opacity: 1; }
}

/* ══════ Вспышка ══════ */
.ny-flash {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, var(--ny-aura-1), transparent 60%),
    radial-gradient(ellipse at 70% 60%, var(--ny-aura-2), transparent 60%);
  opacity: 0;
  animation: ny-flash 24s linear infinite;
}
@keyframes ny-flash {
  0%, 92.5%, 94.5%, 100% { opacity: 0; }
  93%   { opacity: 1; }
  94%   { opacity: 0.5; }
}

/* ══════ Фейерверки ══════ */
.ny-burst {
  position: absolute;
  width: clamp(90px, 12vw, 170px);
  overflow: visible;
}
.ny-burst-1 { left: 11vw; top: 13%; rotate: -8deg; }
.ny-burst-2 { right: 9vw; top: 20%; rotate: 10deg; }
.ny-burst-3 { left: 66vw; top: 6%; rotate: 0deg; }

.ny-burst-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: ny-burst-pop 9s ease-out infinite;
}
@keyframes ny-burst-pop {
  0%        { opacity: 0; transform: scale(0.1) rotate(-10deg); }
  5%        { opacity: 1; transform: scale(1.25) rotate(4deg); }
  10%       { transform: scale(1) rotate(0); }
  16%       { transform: scale(1.08); }
  22%       { transform: scale(1); opacity: 1; }
  34%       { opacity: 0; transform: scale(1.3); }
  100%      { opacity: 0; transform: scale(1.3); }
}

/* ══════ Гирлянда ══════ */
.ny-garland {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.ny-wire-group {
  animation: ny-wire-sway 7s ease-in-out infinite alternate;
  will-change: transform;
}
@keyframes ny-wire-sway {
  from { transform: translateY(-1.2px); }
  to   { transform: translateY(1.2px); }
}
.ny-wire-ink {
  fill: none;
  stroke: var(--ny-ink);
  stroke-width: 4.4;
  stroke-linecap: round;
}
.ny-wire-ice {
  fill: none;
  stroke: #bfe6ff;
  stroke-width: 1.8;
  stroke-linecap: round;
}
.ny-runner {
  fill: none;
  stroke: #ffffff;
  stroke-width: 2.4;
  stroke-linecap: round;
  stroke-dasharray: 26 320;
  opacity: 0.9;
  filter: drop-shadow(0 0 5px rgba(255, 255, 255, 0.95));
  animation: ny-run 6s linear infinite;
  mix-blend-mode: screen;
}
@keyframes ny-run {
  from { stroke-dashoffset: 0; }
  to   { stroke-dashoffset: -346; }
}

.ny-glow {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0.4;
  animation: ny-glow var(--dd, 2.6s) ease-in-out var(--d, 0s) infinite;
}
@keyframes ny-glow {
  0%, 100% { opacity: 0.3; transform: scale(0.9); }
  50%      { opacity: 1;   transform: scale(1.18); }
}
.ny-bulb-use {
  animation: ny-bulb-pulse var(--dd, 2.6s) ease-in-out var(--d, 0s) infinite;
}
@keyframes ny-bulb-pulse {
  0%, 100% { filter: brightness(0.92); }
  50%      { filter: brightness(1.35); }
}

/* ══════ Уголки ══════ */
.ny-corner {
  position: absolute;
  width: clamp(120px, 18vw, 220px);
  height: clamp(120px, 18vw, 220px);
  overflow: visible;
}
/* Только горизонтальное зеркало для правых уголков -никаких переворотов вверх ногами */
.ny-corner-tl { top: 4px; left: 4px; }
.ny-corner-tr { top: 4px; right: 4px; transform: scaleX(-1); }
.ny-corner-bl { bottom: 4px; left: 4px; }
.ny-corner-br { bottom: 4px; right: 4px; transform: scaleX(-1); }

.ny-thread-ink {
  stroke: var(--ny-ink);
  stroke-width: 3.4;
  stroke-linecap: round;
}
.ny-thread {
  stroke: #ffe38a;
  stroke-width: 1.3;
  stroke-linecap: round;
}
.ny-swing {
  transform-box: fill-box;
  transform-origin: 50% -20%;
  animation: ny-swing 3.4s ease-in-out infinite alternate;
}
@keyframes ny-swing {
  from { transform: rotate(-5deg); }
  to   { transform: rotate(5deg); }
}

.ny-corner-beat {
  transform-box: fill-box;
  transform-origin: center;
  animation: ny-corner-beat 2s ease-in-out infinite;
}
@keyframes ny-corner-beat {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25%      { transform: scale(1.12) rotate(6deg); }
  50%      { transform: scale(0.97) rotate(0deg); }
  75%      { transform: scale(1.07) rotate(-5deg); }
}

.ny-corner-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: ny-corner-star 2.4s ease-in-out infinite;
}
@keyframes ny-corner-star {
  0%, 100% { opacity: 0.55; scale: 0.8; }
  50%      { opacity: 1;    scale: 1.2; }
}

/* ══════ Падающие предметы ══════ */
.ny-layer { position: absolute; inset: 0; }

.ny-item {
  position: absolute;
  top: calc(var(--size) * -2);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #fff);
  opacity: 0;
  animation: ny-fall var(--dur) cubic-bezier(0.35, 0.05, 0.65, 0.95) var(--delay) infinite;
  will-change: transform, opacity;
}

@keyframes ny-fall {
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

.ny-item-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation:
    ny-sway var(--sway-dur) ease-in-out infinite alternate,
    ny-spin var(--spin-dur) linear infinite,
    ny-twinkle var(--tw-dur, 1.6s) ease-in-out infinite;
}

@keyframes ny-sway {
  from { transform: translateX(calc(-1 * var(--sway-amp, 12px))); }
  to   { transform: translateX(var(--sway-amp, 12px)); }
}
@keyframes ny-spin {
  from { rotate: -14deg; }
  to   { rotate: 14deg; }
}
@keyframes ny-twinkle {
  0%, 100% { scale: 1; }
  20%      { scale: 1.1; }
  40%      { scale: 0.97; }
  60%      { scale: 1.05; }
}

/* ══════ Звуковые эффекты ══════ */
.ny-sfx {
  position: absolute;
  width: clamp(110px, 15vw, 210px);
  overflow: visible;
}
.ny-sfx-1 { left: 3vw; top: 40%; rotate: -10deg; }
.ny-sfx-2 { right: 3vw; top: 60%; rotate: 8deg; }
.ny-sfx-2 .ny-sfx-pop { animation-delay: 4.5s; }

.ny-sfx-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: ny-sfx-pop 9s ease-in-out infinite;
}

.ny-sfx-outer,
.ny-sfx-text {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans JP", Impact, sans-serif;
  font-size: 52px;
  font-weight: 900;
  letter-spacing: 2px;
  stroke-linejoin: round;
}
.ny-sfx-outer {
  fill: #fff;
  stroke: #fff;
  stroke-width: 15;
}
.ny-sfx-text {
  fill: #4fd0ff;
  stroke: var(--ny-ink);
  stroke-width: 6;
  paint-order: stroke fill;
}
.ny-sfx-text-alt { fill: #ffcf4a; }

@keyframes ny-sfx-pop {
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
.ny-sparks { position: absolute; inset: 0; }

.ny-spark {
  position: absolute;
  bottom: -20px;
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ffcf4a);
  opacity: 0;
  animation: ny-spark-rise var(--dur) linear var(--delay) infinite;
  will-change: transform, opacity;
}
.ny-spark-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: ny-spark-twinkle var(--tw, 1.6s) ease-in-out infinite alternate;
}
@keyframes ny-spark-rise {
  0%   { transform: translate3d(0, 0, 0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.85; }
  100% { transform: translate3d(var(--drift), -108vh, 0); opacity: 0; }
}
@keyframes ny-spark-twinkle {
  from { scale: 0.55; rotate: 0deg; }
  to   { scale: 1.15; rotate: 45deg; }
}

/* ══════ Доступность и печать ══════ */
@media (prefers-reduced-motion: reduce) {
  .ny-overlay { display: none; }
}
@media print {
  .ny-overlay { display: none; }
}
</style>