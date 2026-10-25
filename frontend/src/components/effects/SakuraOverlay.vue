<template>
  <div class="sk-overlay" aria-hidden="true">
    <!-- ── Определения (рисуются один раз, используются через <use>) ── -->
    <svg class="sk-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Контур лепестка сакуры с характерной выемкой -->
        <path
          id="sk-pp"
          d="M0,-10 C-2,-14.5 -8,-14 -9.5,-8 C-11,-2 -6,7 0,13 C6,7 11,-2 9.5,-8 C8,-14 2,-14.5 0,-10 Z"
        />
        <clipPath id="sk-pclip"><use href="#sk-pp" /></clipPath>

        <!-- Лепесток в стиле манги: заливка → тень → штриховка → контур → блик -->
        <g id="sk-p">
          <use href="#sk-pp" class="sk-p-fill" />
          <g clip-path="url(#sk-pclip)">
            <path class="sk-p-shade" d="M14,-14 C14,2 6,11 -1,15 C7,6 8,-4 5,-15 Z" />
            <path class="sk-p-hatch" d="M4.6,6 L8,2.4 M2.4,9 L6.6,5 M7,-1 L10,-3.6" />
          </g>
          <path class="sk-p-vein" d="M0,-6 C0,0 0,5 0,10" />
          <use href="#sk-pp" class="sk-p-ink" />
          <path class="sk-p-gloss" d="M-6.4,-8 C-8.2,-5 -7.6,-1 -5.6,2" />
          <circle class="sk-p-dot" cx="-7.4" cy="4" r="0.9" />
        </g>

        <!-- Цветок сакуры: 5 лепестков, сердцевина, тычинки -->
        <g id="sk-bl">
          <use
            v-for="i in 5"
            :key="`bp${i}`"
            href="#sk-pp"
            class="sk-bp"
            :transform="`rotate(${(i - 1) * 72}) translate(0 -7.8) scale(0.6)`"
          />
          <g class="sk-bl-gloss">
            <path
              v-for="i in 5"
              :key="`bg${i}`"
              d="M-2.6,-12.4 C-4.2,-11 -4.6,-9 -4,-7.4"
              :transform="`rotate(${(i - 1) * 72})`"
            />
          </g>
          <circle class="sk-bl-ring" r="4.6" />
          <g class="sk-bl-stamen">
            <path
              v-for="i in 5"
              :key="`bs${i}`"
              d="M0,-1.6 L0,-5.2"
              :transform="`rotate(${(i - 1) * 72 + 36})`"
            />
          </g>
          <circle
            v-for="i in 5"
            :key="`bd${i}`"
            class="sk-bl-tip"
            cx="0"
            cy="-5.8"
            r="1.15"
            :transform="`rotate(${(i - 1) * 72 + 36})`"
          />
          <circle class="sk-bl-core" r="2" />
        </g>

        <!-- Бутон -->
        <g id="sk-bud">
          <path class="sk-bud-body" d="M0,-9 C5,-6 6,2 0,8 C-6,2 -5,-6 0,-9 Z" />
          <path class="sk-bud-shade" d="M0,-9 C5,-6 6,2 0,8 C2.4,1 2.6,-5 0,-9 Z" />
          <path class="sk-bud-gloss" d="M-2.6,-4 C-3.4,-1 -2.8,2 -1.6,3.6" />
          <path class="sk-bud-cap" d="M-3.2,6 C-1.6,9.6 1.6,9.6 3.2,6 C1.6,7 -1.6,7 -3.2,6 Z" />
        </g>

        <!-- Молодой листик -->
        <g id="sk-lf">
          <path class="sk-lf-body" d="M0,0 C6,-9 20,-10 28,0 C20,10 6,9 0,0 Z" />
          <path class="sk-lf-shade" d="M0,0 C8,0.6 20,0.6 28,0 C20,10 6,9 0,0 Z" />
          <path class="sk-lf-vein" d="M3,0 L22,0" />
          <path class="sk-lf-ink" d="M0,0 C6,-9 20,-10 28,0 C20,10 6,9 0,0 Z" />
        </g>

        <!-- Четырёхконечная звезда-искра -->
        <g id="sk-st">
          <path
            class="sk-st-body"
            d="M0,-11 C1,-3.5 3.5,-1 11,0 C3.5,1 1,3.5 0,11 C-1,3.5 -3.5,1 -11,0 C-3.5,-1 -1,-3.5 0,-11 Z"
          />
          <circle class="sk-st-core" r="2" />
        </g>
      </defs>
    </svg>

    <!-- ── Растровые полутона (скринтон) ── -->
    <div class="sk-tone"></div>

    <!-- ── Манга-линии скорости ── -->
    <svg class="sk-rays" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="xMidYMid slice">
      <path
        v-for="r in rays"
        :key="r.key"
        :d="r.d"
        :class="r.white ? 'sk-ray sk-ray-w' : 'sk-ray'"
      />
    </svg>

    <!-- ── Аура: пульсирующий цветок по центру ── -->
    <!-- <div class="sk-aura">
      <svg viewBox="-100 -100 200 200" class="sk-aura-svg">
        <defs>
          <radialGradient id="sk-aura-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#ff9cc6" stop-opacity="0.34" />
            <stop offset="55%" stop-color="#ffb3d1" stop-opacity="0.12" />
            <stop offset="100%" stop-color="#ffb3d1" stop-opacity="0" />
          </radialGradient>
        </defs>
        <path class="sk-aura-flower" fill="url(#sk-aura-grad)" :d="AURA_FLOWER" />
      </svg>
    </div> -->

    <!-- Мягкая вспышка -->
    <!-- <div class="sk-flash"></div> -->

    <!-- ── Полосы ветра ── -->
    <!-- <svg
      v-for="n in 3"
      :key="`wd${n}`"
      :class="`sk-wind sk-wind-${n}`"
      viewBox="0 0 240 50"
    >
      <path class="sk-wind-ink" d="M2,26 C40,4 78,46 118,24 C150,8 176,22 196,16 C210,12 214,22 206,26" />
      <path class="sk-wind-line" d="M2,26 C40,4 78,46 118,24 C150,8 176,22 196,16 C210,12 214,22 206,26" />
    </svg> -->

    <!-- ── Лоза по периметру: чернильная ветка + цветы ── -->
    <!-- <svg class="sk-frame" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="none">
      <g class="sk-vine-group">
        <path :d="framePath" class="sk-vine-ink" />
        <path :d="framePath" class="sk-vine-wood" />
      </g>
      <g v-for="f in frameItems" :key="f.key" :transform="f.transform">
        <use :href="f.ref" class="sk-frame-i" :style="f.style" />
      </g>
    </svg> -->

    <!-- ── Уголки: цветущая ветка сакуры ── -->
    <!-- <svg
      v-for="c in corners"
      :key="c"
      :class="`sk-corner sk-corner-${c}`"
      viewBox="0 0 200 200"
    >
      <template v-for="(d, i) in STEMS" :key="`st${i}`">
        <path class="sk-stem-ink" :d="d" />
        <path class="sk-stem-wood" :d="d" />
      </template>

      <use
        v-for="(l, i) in LEAVES"
        :key="`lf${i}`"
        href="#sk-lf"
        :transform="`translate(${l.x} ${l.y}) rotate(${l.r}) scale(${l.s})`"
      />

      <use
        v-for="(b, i) in BUDS"
        :key="`bd${i}`"
        href="#sk-bud"
        :transform="`translate(${b.x} ${b.y}) rotate(${b.r}) scale(${b.s})`"
        :style="{ '--color': b.c }"
      />

      <use
        v-for="(b, i) in BLOSSOMS"
        :key="`bl${i}`"
        href="#sk-bl"
        :transform="`translate(${b.x} ${b.y}) rotate(${b.r}) scale(${b.s})`"
        :style="{ '--color': b.c }"
      />

      <g transform="translate(142 92)">
        <g class="sk-corner-beat">
          <use href="#sk-bl" transform="rotate(10) scale(2.5)" style="--color:#ff7fb2" />
        </g>
      </g>

      <use
        v-for="(p, i) in CORNER_PETALS"
        :key="`cp${i}`"
        href="#sk-p"
        class="sk-corner-petal"
        :transform="`translate(${p.x} ${p.y}) rotate(${p.r}) scale(${p.s})`"
        :style="{ '--color': p.c, animationDelay: p.d + 's' }"
      />

      <use
        v-for="(s, i) in CORNER_STARS"
        :key="`cs${i}`"
        href="#sk-st"
        class="sk-corner-star"
        :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
        :style="{ '--color': s.c, animationDelay: s.d + 's' }"
      />
    </svg> -->

    <!-- ── Дальний слой ── -->
    <div class="sk-layer sk-far">
      <span v-for="it in items.far" :key="it.id" class="sk-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="sk-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Средний слой ── -->
    <div class="sk-layer sk-mid">
      <span v-for="it in items.mid" :key="it.id" class="sk-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="sk-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Ближний слой: крупные цветы и лепестки ── -->
    <div class="sk-layer sk-near">
      <span v-for="it in items.near" :key="it.id" class="sk-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="sk-item-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Звуковые эффекты (ономатопея) ── -->
    <!-- <svg class="sk-sfx sk-sfx-1" viewBox="0 0 240 100">
      <g class="sk-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="sk-sfx-outer">ひらひら</text>
        <text x="112" y="66" text-anchor="middle" class="sk-sfx-text">ひらひら</text>
        <use href="#sk-p" transform="translate(214 30) rotate(24) scale(1.5)" style="--color:#ff8fbd" />
      </g>
    </svg>
    <svg class="sk-sfx sk-sfx-2" viewBox="0 0 240 100">
      <g class="sk-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="sk-sfx-outer">ふわふわ</text>
        <text x="112" y="66" text-anchor="middle" class="sk-sfx-text sk-sfx-text-alt">ふわふわ</text>
        <use href="#sk-bl" transform="translate(214 30) rotate(-12) scale(1.3)" style="--color:#ffd3e5" />
      </g>
    </svg> -->

    <!-- ── Искры-звёзды, поднимающиеся снизу ── -->
    <div class="sk-sparks">
      <span v-for="s in sparks" :key="`s${s.id}`" class="sk-spark" :style="s.style">
        <svg viewBox="-14 -14 28 28" class="sk-spark-svg">
          <use href="#sk-st" />
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

const PETAL_COLORS = ["#ff8fbd", "#ffb3d1", "#ffd3e5", "#fff0f6", "#ff6fa5"] as const;
const BLOSSOM_COLORS = ["#ff8fbd", "#ffb3d1", "#ffd3e5", "#ff7fb2", "#fff0f6"] as const;
const STAR_COLORS = ["#fff6d6", "#ffffff", "#ffd3e5"] as const;
const FRAME_COLORS = ["#ff8fbd", "#fff0f6", "#ffb3d1", "#ff7fb2", "#ffd3e5"] as const;

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
    far: small ? 12 : 20,
    mid: small ? 9 : 15,
    near: small ? 5 : 8,
    sparks: small ? 8 : 12,
    frame: small ? 20 : 32,
    rays: small ? 38 : 64,
  };
});

const AURA_FLOWER = (() => {
  const pts: string[] = [];
  const N = 90;
  for (let i = 0; i < N; i++) {
    const a = (i / N) * Math.PI * 2 - Math.PI / 2;
    const r = 56 + 34 * Math.abs(Math.cos(2.5 * a));
    pts.push(`${(Math.cos(a) * r).toFixed(1)},${(Math.sin(a) * r).toFixed(1)}`);
  }
  return `M${pts.join(" L")} Z`;
})();

const STEMS = [
  "M-4,26 C46,20 94,44 142,92",
  "M-4,74 C30,70 54,86 80,118",
  "M92,43 C104,28 120,22 138,28",
  "M52,34 C56,50 62,60 72,68",
] as const;

const BLOSSOMS = [
  { x: 34, y: 23, r: 8, s: 1.35, c: "#ffb3d1" },
  { x: 92, y: 42, r: -12, s: 1.55, c: "#ff8fbd" },
  { x: 138, y: 28, r: 20, s: 1.15, c: "#fff0f6" },
  { x: 33, y: 73, r: -6, s: 1.25, c: "#ffd3e5" },
  { x: 80, y: 117, r: 14, s: 1.4, c: "#ff7fb2" },
  { x: 70, y: 68, r: 30, s: 0.95, c: "#ffb3d1" },
] as const;

const BUDS = [
  { x: 118, y: 62, r: 40, s: 1.0, c: "#ff8fbd" },
  { x: 58, y: 100, r: -35, s: 0.9, c: "#ffb3d1" },
  { x: 16, y: 46, r: -20, s: 0.85, c: "#ff7fb2" },
] as const;

const LEAVES = [
  { x: 60, y: 30, r: -48, s: 0.75 },
  { x: 112, y: 52, r: 38, s: 0.8 },
  { x: 48, y: 82, r: 62, s: 0.7 },
  { x: 94, y: 84, r: -30, s: 0.7 },
  { x: 20, y: 98, r: 76, s: 0.6 },
] as const;

const CORNER_PETALS = [
  { x: 168, y: 62, r: 20, s: 1.0, c: "#ffb3d1", d: 0 },
  { x: 150, y: 150, r: -30, s: 0.85, c: "#fff0f6", d: 0.9 },
  { x: 40, y: 150, r: 50, s: 0.9, c: "#ff8fbd", d: 1.6 },
  { x: 120, y: 120, r: 12, s: 0.7, c: "#ffd3e5", d: 0.4 },
] as const;

const CORNER_STARS = [
  { x: 172, y: 30, s: 1.1, c: "#fff6d6", d: 0 },
  { x: 184, y: 96, s: 0.65, c: "#ffffff", d: 0.8 },
  { x: 112, y: 12, s: 0.55, c: "#ffd3e5", d: 1.9 },
  { x: 24, y: 126, s: 0.75, c: "#fff6d6", d: 1.4 },
] as const;

const LAYERS: Record<"far" | "mid" | "near", LayerConf> = {
  far: {
    size: [12, 18], dur: [20, 30], driftX: [10, 34],
    sway: [3.4, 5.2], op: [0.6, 0.8], amp: [8, 16],
  },
  mid: {
    size: [20, 30], dur: [16, 24], driftX: [18, 50],
    sway: [2.8, 4.4], op: [0.85, 1], amp: [12, 24],
  },
  near: {
    size: [32, 48], dur: [12, 19], driftX: [26, 70],
    sway: [2.2, 3.6], op: [0.95, 1], amp: [16, 30],
  },
};

const buildItems = (count: number, layer: "far" | "mid" | "near") => {
  const conf = LAYERS[layer];
  const out: { id: string; ref: string; style: Vars }[] = [];
  for (let i = 0; i < count; i++) {
    const size = rnd(conf.size[0], conf.size[1]);
    const dur = rnd(conf.dur[0], conf.dur[1]);

    let ref = "#sk-p";
    let color: string = pick(PETAL_COLORS);

    if (layer === "near") {
      if (i % 2 === 0) { ref = "#sk-bl"; color = pick(BLOSSOM_COLORS); }
    } else if (layer === "mid") {
      if (i % 4 === 3) { ref = "#sk-bl"; color = pick(BLOSSOM_COLORS); }
      else if (i % 5 === 4) { ref = "#sk-st"; color = pick(STAR_COLORS); }
    } else if (i % 6 === 5) {
      ref = "#sk-st"; color = pick(STAR_COLORS);
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
        "--spin-dur": `${rnd(6, 14).toFixed(1)}s`,
        "--tw-dur": `${rnd(1.4, 2.6).toFixed(2)}s`,
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
  const rand = seeded(2503);
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

const INSET = 9;
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
    const rot = ((i * 37) % 60) - 30;
    const isBud = i % 4 === 3;
    out.push({
      key: `fi${i}`,
      ref: isBud ? "#sk-bud" : "#sk-bl",
      transform: `translate(${pt.x.toFixed(1)} ${pt.y.toFixed(1)}) rotate(${rot}) scale(${isBud ? 0.6 : 0.62})`,
      style: {
        "--color": FRAME_COLORS[i % FRAME_COLORS.length] as string,
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
      "--size": `${rnd(9, 16).toFixed(1)}px`,
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
.sk-overlay {
   opacity: 0.7 !important;
  position: fixed;
  inset: 0;
  z-index: 9996;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --sk-ink: #3b1630;
  --sk-gold: #ffcf4a;
  --sk-aura-1: rgba(255, 150, 195, 0.03);
  --sk-aura-2: rgba(255, 215, 230, 0.02);
  --sk-ray:   rgba(255, 130, 180, 0.001);   /* было 0.2 */
  --sk-ray-w: rgba(255, 255, 255, 0.001);   /* было 0.4 */
  --sk-tone:  rgba(255, 130, 180, 0.001);
}

:global(html[data-theme="dark"]) .sk-overlay,
:global(body.theme-dark) .sk-overlay {
  --sk-aura-1: rgba(255, 160, 205, 0.38);
  --sk-aura-2: rgba(255, 225, 238, 0.2);
  --sk-ray: rgba(255, 150, 195, 0.26);
  --sk-ray-w: rgba(255, 235, 245, 0.24);
  --sk-tone: rgba(255, 150, 195, 0.36);
}

.sk-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

/* ══════ Лепесток: заливка / тень / штрих / контур / блик ══════ */
.sk-p-fill { fill: var(--color, #ffb3d1); stroke: none; }
.sk-p-shade { fill: color-mix(in srgb, var(--color, #ffb3d1) 62%, #b0306a); }
.sk-p-hatch {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
.sk-p-vein {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #ffb3d1) 55%, #b0306a);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.8;
}
.sk-p-ink {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
.sk-p-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}
.sk-p-dot { fill: #fff; }

/* ══════ Цветок ══════ */
.sk-bp {
  fill: var(--color, #ffb3d1);
  stroke: var(--sk-ink);
  stroke-width: 3.4;
  stroke-linejoin: round;
}
.sk-bl-gloss path {
  fill: none;
  stroke: #fff;
  stroke-width: 1.4;
  stroke-linecap: round;
  opacity: 0.9;
}
.sk-bl-ring {
  fill: color-mix(in srgb, var(--color, #ffb3d1) 55%, #c0387a);
  stroke: none;
  opacity: 0.85;
}
.sk-bl-stamen path {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 1.1;
  stroke-linecap: round;
}
.sk-bl-tip {
  fill: var(--sk-gold);
  stroke: var(--sk-ink);
  stroke-width: 0.9;
}
.sk-bl-core {
  fill: var(--sk-gold);
  stroke: var(--sk-ink);
  stroke-width: 1.2;
}

/* ══════ Бутон ══════ */
.sk-bud-body { fill: var(--color, #ff8fbd); stroke: none; }
.sk-bud-shade { fill: color-mix(in srgb, var(--color, #ff8fbd) 58%, #b0306a); }
.sk-bud-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.sk-bud-cap {
  fill: #5fcf8a;
  stroke: var(--sk-ink);
  stroke-width: 1.4;
  stroke-linejoin: round;
}

/* ══════ Листик ══════ */
.sk-lf-body { fill: #6fdc8c; }
.sk-lf-shade { fill: #35a860; }
.sk-lf-vein {
  fill: none;
  stroke: #1d7a45;
  stroke-width: 1.2;
  stroke-linecap: round;
}
.sk-lf-ink {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
}

/* ══════ Звезда ══════ */
.sk-st-body {
  fill: var(--color, #fff6d6);
  stroke: var(--sk-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.sk-st-core { fill: #fff; }

/* ══════ Растр + линии скорости ══════ */
.sk-tone {
  position: absolute;
  inset: -40%;
  background-image: radial-gradient(circle, var(--sk-tone) 1.3px, transparent 1.7px);
  background-size: 9px 9px;
  transform: rotate(15deg);
  -webkit-mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  opacity: 0.75;
}

.sk-rays {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  animation: sk-rays-shake 0.5s steps(2, jump-none) infinite;
}
.sk-ray { fill: var(--sk-ray); }
.sk-ray-w { fill: var(--sk-ray-w); }

@keyframes sk-rays-shake {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(1.5px, -1px) scale(1.012); }
}

/* ══════ Аура ══════ */
.sk-aura {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(80vmin, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  animation: sk-aura-pulse 4.4s ease-in-out infinite;
}
.sk-aura-svg { width: 100%; height: 100%; overflow: visible; }
.sk-aura-flower { filter: blur(6px); }

@keyframes sk-aura-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.94) rotate(0deg); opacity: 0.8; }
  50%      { transform: translate(-50%, -50%) scale(1.06) rotate(7deg); opacity: 1; }
}

/* ══════ Вспышка ══════ */
.sk-flash {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, var(--sk-aura-1), transparent 60%),
    radial-gradient(ellipse at 70% 60%, var(--sk-aura-2), transparent 60%);
  opacity: 0;
  animation: sk-flash 24s linear infinite;
}
@keyframes sk-flash {
  0%, 92.5%, 94.5%, 100% { opacity: 0; }
  93%   { opacity: 1; }
  94%   { opacity: 0.5; }
}

/* ══════ Полосы ветра ══════ */
.sk-wind {
  position: absolute;
  left: 0;
  width: clamp(120px, 18vw, 240px);
  overflow: visible;
  opacity: 0;
  animation: sk-wind 11s ease-in-out infinite;
}
.sk-wind-1 { top: 24%; }
.sk-wind-2 { top: 54%; animation-delay: 3.6s; }
.sk-wind-3 { top: 78%; animation-delay: 7.2s; }

.sk-wind-ink {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 5;
  stroke-linecap: round;
  opacity: 0.55;
}
.sk-wind-line {
  fill: none;
  stroke: #fff;
  stroke-width: 2.2;
  stroke-linecap: round;
}

@keyframes sk-wind {
  0%   { opacity: 0; transform: translateX(-30vw); }
  12%  { opacity: 0.9; }
  70%  { opacity: 0.9; }
  100% { opacity: 0; transform: translateX(118vw); }
}

/* ══════ Лоза по периметру ══════ */
.sk-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.sk-vine-group {
  animation: sk-vine-sway 7s ease-in-out infinite alternate;
  will-change: transform;
}
@keyframes sk-vine-sway {
  from { transform: translateY(-1.2px); }
  to   { transform: translateY(1.2px); }
}
.sk-vine-ink {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 4.4;
  stroke-linecap: round;
}
.sk-vine-wood {
  fill: none;
  stroke: #a8705a;
  stroke-width: 1.9;
  stroke-linecap: round;
}
.sk-frame-i {
  animation: sk-frame-twinkle 3s ease-in-out infinite;
}
@keyframes sk-frame-twinkle {
  0%, 100% { opacity: 0.85; }
  50%      { opacity: 1; }
}

/* ══════ Уголки ══════ */
.sk-corner {
  position: absolute;
  width: clamp(120px, 18vw, 220px);
  height: clamp(120px, 18vw, 220px);
  overflow: visible;
}
.sk-corner-tl { top: 4px; left: 4px; }
.sk-corner-tr { top: 4px; right: 4px; transform: scaleX(-1); }
.sk-corner-bl { bottom: 4px; left: 4px; transform: scaleY(-1); }
.sk-corner-br { bottom: 4px; right: 4px; transform: scale(-1, -1); }

.sk-stem-ink {
  fill: none;
  stroke: var(--sk-ink);
  stroke-width: 8;
  stroke-linecap: round;
}
.sk-stem-wood {
  fill: none;
  stroke: #9a6450;
  stroke-width: 3.8;
  stroke-linecap: round;
}

.sk-corner-beat {
  transform-box: fill-box;
  transform-origin: center;
  animation: sk-corner-beat 2.2s ease-in-out infinite;
}
@keyframes sk-corner-beat {
  0%, 100% { transform: scale(1) rotate(0deg); }
  25%      { transform: scale(1.1) rotate(5deg); }
  50%      { transform: scale(0.98) rotate(0deg); }
  75%      { transform: scale(1.06) rotate(-4deg); }
}

.sk-corner-petal {
  transform-box: fill-box;
  transform-origin: center;
  animation: sk-corner-petal 3.2s ease-in-out infinite;
}
@keyframes sk-corner-petal {
  0%, 100% { opacity: 0.8; translate: 0 0; }
  50%      { opacity: 1;   translate: 4px 5px; }
}

.sk-corner-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: sk-corner-star 2.4s ease-in-out infinite;
}
@keyframes sk-corner-star {
  0%, 100% { opacity: 0.55; scale: 0.8; }
  50%      { opacity: 1;    scale: 1.2; }
}

/* ══════ Падающие предметы ══════ */
.sk-layer { position: absolute; inset: 0; }

.sk-item {
  position: absolute;
  top: calc(var(--size) * -2);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ffb3d1);
  opacity: 0;
  animation: sk-fall var(--dur) cubic-bezier(0.35, 0.05, 0.65, 0.95) var(--delay) infinite;
  will-change: transform, opacity;
}

@keyframes sk-fall {
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

.sk-item-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation:
    sk-sway var(--sway-dur) ease-in-out infinite alternate,
    sk-spin var(--spin-dur) ease-in-out infinite alternate,
    sk-twinkle var(--tw-dur, 1.8s) ease-in-out infinite;
}

@keyframes sk-sway {
  from { transform: translateX(calc(-1 * var(--sway-amp, 12px))); }
  to   { transform: translateX(var(--sway-amp, 12px)); }
}
@keyframes sk-spin {
  from { rotate: -40deg; }
  to   { rotate: 40deg; }
}
/* лепесток «переворачивается» на ветру */
@keyframes sk-twinkle {
  0%, 100% { scale: 1 1; }
  30%      { scale: 0.7 1.05; }
  55%      { scale: 1.05 0.96; }
  80%      { scale: 0.85 1; }
}

/* ══════ Звуковые эффекты ══════ */
.sk-sfx {
  position: absolute;
  width: clamp(110px, 15vw, 210px);
  overflow: visible;
}
.sk-sfx-1 { left: 3vw; top: 40%; rotate: -10deg; }
.sk-sfx-2 { right: 3vw; top: 60%; rotate: 8deg; }
.sk-sfx-2 .sk-sfx-pop { animation-delay: 4.5s; }

.sk-sfx-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: sk-sfx-pop 9s ease-in-out infinite;
}

.sk-sfx-outer,
.sk-sfx-text {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans JP", Impact, sans-serif;
  font-size: 52px;
  font-weight: 900;
  letter-spacing: 2px;
  stroke-linejoin: round;
}
.sk-sfx-outer {
  fill: #fff;
  stroke: #fff;
  stroke-width: 15;
}
.sk-sfx-text {
  fill: #ff7fb2;
  stroke: var(--sk-ink);
  stroke-width: 6;
  paint-order: stroke fill;
}
.sk-sfx-text-alt { fill: #8fe08a; }

@keyframes sk-sfx-pop {
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
.sk-sparks { position: absolute; inset: 0; }

.sk-spark {
  position: absolute;
  bottom: -20px;
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #fff6d6);
  opacity: 0;
  animation: sk-spark-rise var(--dur) linear var(--delay) infinite;
  will-change: transform, opacity;
}
.sk-spark-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: sk-spark-twinkle var(--tw, 1.6s) ease-in-out infinite alternate;
}
@keyframes sk-spark-rise {
  0%   { transform: translate3d(0, 0, 0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.85; }
  100% { transform: translate3d(var(--drift), -108vh, 0); opacity: 0; }
}
@keyframes sk-spark-twinkle {
  from { scale: 0.55; rotate: 0deg; }
  to   { scale: 1.15; rotate: 45deg; }
}

/* ══════ Доступность и печать ══════ */
@media (prefers-reduced-motion: reduce) {
  .sk-overlay { display: none; }
}
@media print {
  .sk-overlay { display: none; }
}
</style>