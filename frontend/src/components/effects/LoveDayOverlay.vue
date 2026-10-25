<template>
  <div class="vd-overlay" aria-hidden="true">
    <!-- ── Определения (рисуются один раз, используются через <use>) ── -->
    <svg class="vd-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Контур сердца -->
        <path
          id="vd-hp"
          d="M0,10.5 C-10,3.5 -15.5,-1.5 -15.5,-7.5 C-15.5,-12 -12,-14.5 -8.2,-14.5 C-4.6,-14.5 -1.6,-12.4 0,-9 C1.6,-12.4 4.6,-14.5 8.2,-14.5 C12,-14.5 15.5,-12 15.5,-7.5 C15.5,-1.5 10,3.5 0,10.5 Z"
        />
        <clipPath id="vd-hclip"><use href="#vd-hp" /></clipPath>

        <!-- Сердце в стиле манги: заливка → тень → штриховка → жирный контур → блик -->
        <g id="vd-h">
          <use href="#vd-hp" class="vd-h-fill" />
          <g clip-path="url(#vd-hclip)">
            <path class="vd-h-shade" d="M18,-8 C18,3 10,9 -1,12 C9,5 11,-3 8.5,-16 L18,-16 Z" />
            <path class="vd-h-hatch" d="M6.2,3.2 L9.8,-0.6 M3.4,6.4 L7.8,2.2 M9,-3 L12.4,-5.6" />
          </g>
          <use href="#vd-hp" class="vd-h-ink" />
          <path class="vd-h-gloss" d="M-11.6,-8.2 C-11.6,-10.8 -9.6,-12.2 -7.2,-11.6" />
          <circle class="vd-h-dot" cx="-12.4" cy="-4.4" r="0.95" />
        </g>

        <!-- Четырёхконечная звезда-искра -->
        <g id="vd-s">
          <path
            class="vd-s-body"
            d="M0,-11 C1,-3.5 3.5,-1 11,0 C3.5,1 1,3.5 0,11 C-1,3.5 -3.5,1 -11,0 C-3.5,-1 -1,-3.5 0,-11 Z"
          />
          <circle class="vd-s-core" r="2" />
        </g>

        <!-- Любовное письмо с сердцем-печатью -->
        <g id="vd-e">
          <rect class="vd-e-body" x="-15" y="-10.5" width="30" height="21" rx="2.4" />
          <path class="vd-e-flap" d="M-15,-10.5 L0,3 L15,-10.5" />
          <path class="vd-e-fold" d="M-15,10.5 L-5,0.5 M15,10.5 L5,0.5" />
          <use href="#vd-h" transform="translate(0 2.4) scale(0.52)" style="--color:#ff3b5c" />
        </g>
      </defs>
    </svg>

    <!-- ── Растровые полутона (скринтон) по краям ── -->
    <div class="vd-tone"></div>

    <!-- ── Манга-линии скорости (фокус на центр) ── -->
    <svg class="vd-rays" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="xMidYMid slice">
      <path
        v-for="r in rays"
        :key="r.key"
        :d="r.d"
        :class="r.white ? 'vd-ray vd-ray-w' : 'vd-ray'"
      />
    </svg>

    <!-- ── Аура ── -->
    <!-- <div class="vd-aura">
      <svg viewBox="-100 -100 200 200" class="vd-aura-svg">
        <defs>
          <radialGradient id="vd-aura-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#ff8ac2" stop-opacity="0.32" />
            <stop offset="55%" stop-color="#ff5fa2" stop-opacity="0.1" />
            <stop offset="100%" stop-color="#ff5fa2" stop-opacity="0" />
          </radialGradient>
        </defs>
        <path
          class="vd-aura-heart"
          fill="url(#vd-aura-grad)"
          d="M0,55 C-55,15 -85,-15 -85,-50 C-85,-78 -62,-92 -40,-92 C-20,-92 -8,-78 0,-62 C8,-78 20,-92 40,-92 C62,-92 85,-78 85,-50 C85,-15 55,15 0,55 Z"
        />
      </svg>
    </div> -->

    <!-- Мягкая вспышка -->
    <!-- <div class="vd-flash"></div> -->

    <!-- ── Гирлянда по периметру: чернильная нить + сердечки ── -->
    <!-- <svg class="vd-frame" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="none">
      <path :d="framePath" class="vd-wire-ink" />
      <path :d="framePath" class="vd-wire-pink" />
      <g v-for="f in frameHearts" :key="f.key" :transform="f.transform">
        <use href="#vd-h" class="vd-frame-h" :style="f.style" />
      </g>
    </svg> -->

    <!-- ── Уголки: завитки + сердце (со стрелой Купидона только сверху) ── -->
    <!-- <svg
      v-for="c in corners"
      :key="c"
      :class="`vd-corner vd-corner-${c}`"
      viewBox="0 0 200 200"
    >
      <template v-for="d in VINES" :key="d">
        <path class="vd-line-ink" :d="d" />
        <path class="vd-line-pink" :d="d" />
      </template>

      <g v-if="hasArrow(c)">
        <path class="vd-arrow-ink" d="M38,21 L70,44" />
        <path class="vd-arrow-gold" d="M38,21 L70,44" />
        <path class="vd-fletch vd-fletch-a" d="M42,25 L56,35 L59,26 L46,16 Z" />
        <path class="vd-fletch vd-fletch-b" d="M42,25 L56,35 L50,43 L37,34 Z" />
      </g>

      <g :transform="`translate(104 84) ${UNFLIP[c]}`">
        <g class="vd-corner-beat">
          <use href="#vd-h" transform="scale(3.1)" style="--color:#ff4f93" />
        </g>
      </g>

      <g v-if="hasArrow(c)">
        <path class="vd-arrow-ink" d="M108,82 L140,105" />
        <path class="vd-arrow-gold" d="M108,82 L140,105" />
        <path class="vd-arrow-tip" d="M142,106.6 L123.8,102.7 L132.6,90.5 Z" />
      </g>
      
      <use
        v-for="(m, i) in SMALL_HEARTS"
        :key="`m${i}`"
        href="#vd-h"
        :transform="`translate(${m.x} ${m.y}) ${UNFLIP[c]} rotate(${m.r}) scale(${m.s})`"
        :style="{ '--color': m.c }"
      />

      <use
        v-for="(s, i) in CORNER_STARS"
        :key="i"
        href="#vd-s"
        class="vd-corner-star"
        :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
        :style="{ '--color': s.c, animationDelay: s.d + 's' }"
      />
    </svg> -->

    <!-- ── Дальний слой ── -->
    <div class="vd-layer vd-far">
      <span v-for="it in items.far" :key="it.id" class="vd-heart" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="vd-heart-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Средний слой ── -->
    <div class="vd-layer vd-mid">
      <span v-for="it in items.mid" :key="it.id" class="vd-heart" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="vd-heart-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Ближний слой: крупные сердца и письма ── -->
    <div class="vd-layer vd-near">
      <span v-for="it in items.near" :key="it.id" class="vd-heart vd-heart-big" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="vd-heart-svg">
          <use :href="it.ref" />
        </svg>
      </span>
    </div>

    <!-- ── Звуковые эффекты (ономато­пея) ── -->
    <!-- <svg class="vd-sfx vd-sfx-1" viewBox="0 0 240 100">
      <g class="vd-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="vd-sfx-outer">Няяяя</text>
        <text x="112" y="66" text-anchor="middle" class="vd-sfx-text">Няяяя</text>
        <use href="#vd-h" transform="translate(196 30) rotate(14) scale(1.3)" style="--color:#ff3b5c" />
      </g>
    </svg>
    <svg class="vd-sfx vd-sfx-2" viewBox="0 0 240 100">
      <g class="vd-sfx-pop">
        <text x="112" y="66" text-anchor="middle" class="vd-sfx-outer">Няяяя</text>
        <text x="112" y="66" text-anchor="middle" class="vd-sfx-text vd-sfx-text-alt">Няяяя</text>
        <use href="#vd-h" transform="translate(196 30) rotate(-12) scale(1.3)" style="--color:#ffcf4a" />
      </g>
    </svg> -->

    <!-- ── Искры-звёзды ── -->
    <div class="vd-sparks">
      <span v-for="s in sparks" :key="`s${s.id}`" class="vd-spark" :style="s.style">
        <svg viewBox="-14 -14 28 28" class="vd-spark-svg">
          <use href="#vd-s" />
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

interface HeartConf {
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
    frame: small ? 22 : 34,
    rays: small ? 38 : 64,
  };
});

const HEART_COLORS = ["#ff4f93", "#ff7eb6", "#ff3b5c", "#ffa3c8", "#fff0f6", "#ffcf4a"] as const;
const STAR_COLORS = ["#ffcf4a", "#fff0f6", "#ffa3c8"] as const;
const FRAME_COLORS = ["#ff4f93", "#fff0f6", "#ff7eb6", "#ffcf4a", "#ff3b5c"] as const;

const corners = ["tl", "tr", "bl", "br"] as const;
type Corner = (typeof corners)[number];

const hasArrow = (c: Corner) => c === "tl" || c === "tr";

const UNFLIP: Record<Corner, string> = {
  tl: "",
  tr: "scale(-1 1)",
  bl: "scale(1 -1)",
  br: "scale(-1 -1)",
};

const SMALL_HEARTS = [
  { x: 58, y: 106, r: -18, s: 0.95, c: "#ffcf4a" },
  { x: 22, y: 66, r: 12, s: 0.7, c: "#fff0f6" },
  { x: 84, y: 20, r: -10, s: 0.6, c: "#ff7eb6" },
] as const;

const VINES = [
  "M8,34 C44,30 78,46 94,74 C106,96 98,122 74,126 C56,128 46,112 58,102",
  "M34,8 C32,42 50,64 76,72",
  "M8,58 C22,56 34,62 40,74",
] as const;

const CORNER_STARS = [
  { x: 162, y: 30, s: 1.2, c: "#ffcf4a", d: 0 },
  { x: 178, y: 78, s: 0.7, c: "#fff0f6", d: 0.8 },
  { x: 30, y: 154, s: 0.85, c: "#ffcf4a", d: 1.4 },
  { x: 118, y: 168, s: 0.6, c: "#fff0f6", d: 0.4 },
  { x: 126, y: 18, s: 0.55, c: "#ffa3c8", d: 1.9 },
] as const;

const LAYERS: Record<"far" | "mid" | "near", HeartConf> = {
  far: {
    size: [11, 17], dur: [24, 36], driftX: [12, 24],
    sway: [3.4, 5.2], op: [0.55, 0.75], amp: [6, 12],
  },
  mid: {
    size: [18, 28], dur: [18, 28], driftX: [18, 36],
    sway: [2.8, 4.4], op: [0.85, 1], amp: [10, 20],
  },
  near: {
    size: [30, 46], dur: [14, 22], driftX: [24, 48],
    sway: [2.2, 3.6], op: [0.95, 1], amp: [14, 26],
  },
};

const buildItems = (count: number, layer: "far" | "mid" | "near") => {
  const conf = LAYERS[layer];
  const out: { id: string; ref: string; style: Vars }[] = [];
  for (let i = 0; i < count; i++) {
    const size = rnd(conf.size[0], conf.size[1]);
    const dur = rnd(conf.dur[0], conf.dur[1]);

    let ref = "#vd-h";
    let color: string = pick(HEART_COLORS);
    if (layer === "near" && i % 3 === 2) {
      ref = "#vd-e";
    } else if (layer !== "near" && i % 5 === 4) {
      ref = "#vd-s";
      color = pick(STAR_COLORS);
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
        "--beat-dur": `${rnd(0.9, 1.5).toFixed(2)}s`,
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
  const rand = seeded(1402);
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

const frameHearts = computed(() => {
  const W = w.value, H = h.value;
  const x0 = INSET, x1 = W - INSET;
  const y0 = INSET, y1 = H - INSET;
  const total = counts.value.frame;
  const per = 2 * (x1 - x0) + 2 * (y1 - y0);
  const topLen = x1 - x0;
  const rightLen = y1 - y0;
  const out: { key: string; transform: string; style: Vars }[] = [];
  for (let i = 0; i < total; i++) {
    const d = ((i + 0.5) / total) * per;
    let pt: Pt;
    if (d < topLen) pt = { x: x0 + d, y: y0 };
    else if (d < topLen + rightLen) pt = { x: x1, y: y0 + (d - topLen) };
    else if (d < topLen * 2 + rightLen) pt = { x: x1 - (d - topLen - rightLen), y: y1 };
    else pt = { x: x0, y: y1 - (d - topLen * 2 - rightLen) };
    const rot = ((i * 37) % 30) - 15;
    out.push({
      key: `fh${i}`,
      transform: `translate(${pt.x.toFixed(1)} ${pt.y.toFixed(1)}) rotate(${rot}) scale(0.62)`,
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
.vd-overlay {
  position: fixed;
  opacity: 0.5!important;
  inset: 0;
  z-index: 9998;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --vd-ink: #3a0a26;
  --vd-gold: #ffcf4a;
  --vd-aura-1: rgba(255, 120, 180, 0.32);
  --vd-aura-2: rgba(255, 200, 220, 0.16);
  --vd-ray: rgba(255, 79, 147, 0.001);
  --vd-ray-w: rgba(255, 255, 255, 0.001);
  --vd-tone: rgba(255, 79, 147, 0.001);
}

:global(html[data-theme="dark"]) .vd-overlay,
:global(body.theme-dark) .vd-overlay {
  --vd-aura-1: rgba(255, 140, 200, 0.38);
  --vd-aura-2: rgba(255, 220, 235, 0.18);
  --vd-ray: rgba(255, 110, 170, 0.26);
  --vd-ray-w: rgba(255, 230, 242, 0.22);
  --vd-tone: rgba(255, 130, 190, 0.38);
}

.vd-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

/* ══════ Сердце в стиле One Piece: заливка / тень / штрих / контур / блик ══════ */
.vd-h-fill { fill: var(--color, #ff4f93); stroke: none; }
.vd-h-shade { fill: color-mix(in srgb, var(--color, #ff4f93) 60%, #8a0f48); }
.vd-h-hatch {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 0.8;
  stroke-linecap: round;
  opacity: 0.4;
}
.vd-h-ink {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
.vd-h-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2.2;
  stroke-linecap: round;
}
.vd-h-dot { fill: #fff; }

/* звезда-искра */
.vd-s-body {
  fill: var(--color, #ffcf4a);
  stroke: var(--vd-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.vd-s-core { fill: #fff; }

/* письмо */
.vd-e-body {
  fill: #fff6fa;
  stroke: var(--vd-ink);
  stroke-width: 2.4;
  stroke-linejoin: round;
}
.vd-e-flap {
  fill: #ffd6e8;
  stroke: var(--vd-ink);
  stroke-width: 2.2;
  stroke-linejoin: round;
  stroke-linecap: round;
}
.vd-e-fold {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 1.4;
  stroke-linecap: round;
  opacity: 0.55;
}

/* ══════ Растр + линии скорости ══════ */
.vd-tone {
  position: absolute;
  inset: -40%;
  background-image: radial-gradient(circle, var(--vd-tone) 1.3px, transparent 1.7px);
  background-size: 9px 9px;
  transform: rotate(15deg);
  -webkit-mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  opacity: 0.75;
}

.vd-rays {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  animation: vd-rays-shake 0.5s steps(2, jump-none) infinite;
}
.vd-ray { fill: var(--vd-ray); }
.vd-ray-w { fill: var(--vd-ray-w); }

@keyframes vd-rays-shake {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(1.5px, -1px) scale(1.012); }
}

/* ══════ Аура ══════ */
.vd-aura {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(80vmin, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  animation: vd-aura-pulse 4.4s ease-in-out infinite;
}
.vd-aura-svg { width: 100%; height: 100%; overflow: visible; }
.vd-aura-heart { filter: blur(6px); }

@keyframes vd-aura-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.94); opacity: 0.8; }
  50%      { transform: translate(-50%, -50%) scale(1.06); opacity: 1; }
}

/* ══════ Вспышка ══════ */
.vd-flash {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, var(--vd-aura-1), transparent 60%),
    radial-gradient(ellipse at 70% 60%, var(--vd-aura-2), transparent 60%);
  opacity: 0;
  animation: vd-flash 24s linear infinite;
}
@keyframes vd-flash {
  0%, 92.5%, 94.5%, 100% { opacity: 0; }
  93%   { opacity: 1; }
  94%   { opacity: 0.5; }
}

/* ══════ Гирлянда ══════ */
.vd-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.vd-wire-ink {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 4.2;
  stroke-linecap: round;
}
.vd-wire-pink {
  fill: none;
  stroke: #ff9ec9;
  stroke-width: 1.8;
  stroke-linecap: round;
}
.vd-frame-h {
  animation: vd-frame-twinkle 3s ease-in-out infinite;
}
@keyframes vd-frame-twinkle {
  0%, 100% { opacity: 0.8; }
  50%      { opacity: 1; }
}

/* ══════ Уголки ══════ */
.vd-corner {
  position: absolute;
  width: clamp(110px, 17vw, 210px);
  height: clamp(110px, 17vw, 210px);
  overflow: visible;
}
.vd-corner-tl { top: 4px; left: 4px; }
.vd-corner-tr { top: 4px; right: 4px; transform: scaleX(-1); }
.vd-corner-bl { bottom: 4px; left: 4px; transform: scaleY(-1); }
.vd-corner-br { bottom: 4px; right: 4px; transform: scale(-1, -1); }

.vd-line-ink {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 6.5;
  stroke-linecap: round;
}
.vd-line-pink {
  fill: none;
  stroke: #ffb3d4;
  stroke-width: 3;
  stroke-linecap: round;
}

.vd-arrow-ink {
  fill: none;
  stroke: var(--vd-ink);
  stroke-width: 7;
  stroke-linecap: round;
}
.vd-arrow-gold {
  fill: none;
  stroke: var(--vd-gold);
  stroke-width: 3.2;
  stroke-linecap: round;
}
.vd-arrow-tip {
  fill: var(--vd-gold);
  stroke: var(--vd-ink);
  stroke-width: 3;
  stroke-linejoin: round;
}
.vd-fletch {
  stroke: var(--vd-ink);
  stroke-width: 2.6;
  stroke-linejoin: round;
}
.vd-fletch-a { fill: #ff4f93; }
.vd-fletch-b { fill: #fff6fa; }

.vd-corner-beat {
  transform-box: fill-box;
  transform-origin: center;
  animation: vd-corner-beat 1.6s ease-in-out infinite;
}
@keyframes vd-corner-beat {
  0%, 100% { transform: scale(1); }
  14%      { transform: scale(1.09); }
  28%      { transform: scale(0.98); }
  42%      { transform: scale(1.05); }
  60%      { transform: scale(1); }
}

.vd-corner-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: vd-corner-star 2.4s ease-in-out infinite;
}
@keyframes vd-corner-star {
  0%, 100% { opacity: 0.55; scale: 0.8; }
  50%      { opacity: 1;    scale: 1.2; }
}

/* ══════ Падающие предметы ══════ */
.vd-layer { position: absolute; inset: 0; }

.vd-heart {
  position: absolute;
  top: calc(var(--size) * -2);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ff4f93);
  opacity: 0;
  animation: vd-fall var(--dur) cubic-bezier(0.35, 0.05, 0.65, 0.95) var(--delay) infinite;
  will-change: transform, opacity;
}

@keyframes vd-fall {
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

.vd-heart-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  animation:
    vd-sway var(--sway-dur) ease-in-out infinite alternate,
    vd-spin var(--spin-dur) linear infinite,
    vd-beat var(--beat-dur, 1.2s) ease-in-out infinite;
  transform-origin: 50% 50%;
}

@keyframes vd-sway {
  from { transform: translateX(calc(-1 * var(--sway-amp, 12px))); }
  to   { transform: translateX(var(--sway-amp, 12px)); }
}
@keyframes vd-spin {
  from { rotate: -14deg; }
  to   { rotate: 14deg; }
}
/* «сердцебиение» -аниме-пульсация */
@keyframes vd-beat {
  0%, 100% { scale: 1; }
  15%      { scale: 1.13; }
  30%      { scale: 0.97; }
  45%      { scale: 1.07; }
  60%      { scale: 1; }
}

/* ══════ Звуковые эффекты ══════ */
.vd-sfx {
  position: absolute;
  width: clamp(110px, 15vw, 210px);
  overflow: visible;
}
.vd-sfx-1 { left: 3vw; top: 40%; rotate: -10deg; }
.vd-sfx-2 { right: 3vw; top: 60%; rotate: 8deg; }
.vd-sfx-2 .vd-sfx-pop { animation-delay: 4.5s; }

.vd-sfx-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: vd-sfx-pop 9s ease-in-out infinite;
}

.vd-sfx-outer,
.vd-sfx-text {
  font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Meiryo", "Noto Sans JP", Impact, sans-serif;
  font-size: 52px;
  font-weight: 900;
  letter-spacing: -5px;
  stroke-linejoin: round;
}
.vd-sfx-outer {
  fill: #fff;
  stroke: #fff;
  stroke-width: 15;
}
.vd-sfx-text {
  fill: #ff4f93;
  stroke: var(--vd-ink);
  stroke-width: 6;
  paint-order: stroke fill;
}
.vd-sfx-text-alt { fill: #ffcf4a; }

@keyframes vd-sfx-pop {
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
.vd-sparks { position: absolute; inset: 0; }

.vd-spark {
  position: absolute;
  bottom: -20px;
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ffcf4a);
  opacity: 0;
  animation: vd-spark-rise var(--dur) linear var(--delay) infinite;
  will-change: transform, opacity;
}
.vd-spark-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: vd-spark-twinkle var(--tw, 1.6s) ease-in-out infinite alternate;
}
.vd-spark-svg :deep(use) { --color: currentColor; }

@keyframes vd-spark-rise {
  0%   { transform: translate3d(0, 0, 0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.85; }
  100% { transform: translate3d(var(--drift), -108vh, 0); opacity: 0; }
}
@keyframes vd-spark-twinkle {
  from { scale: 0.55; rotate: 0deg; }
  to   { scale: 1.15; rotate: 45deg; }
}

/* ══════ Доступность и печать ══════ */
@media (prefers-reduced-motion: reduce) {
  .vd-overlay { display: none; }
}
@media print {
  .vd-overlay { display: none; }
}
</style>