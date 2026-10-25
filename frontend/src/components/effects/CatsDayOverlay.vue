<template>
  <div class="ct-overlay" aria-hidden="true">
    <!-- ── Определения ── -->
    <svg class="ct-defs" width="0" height="0" focusable="false">
      <defs>
        <!-- Пушистая голова: уши + пучки шерсти на щёчках -->
        <path
          id="ct-chp"
          d="M-11,-5 L-13.5,-16.5 L-5,-11.2 Q0,-12.8 5,-11.2 L13.5,-16.5 L11,-5 Q15.2,-3 14.6,0 L17,2.2 Q14.8,3.6 15.4,5.4 L16.6,8.6 Q13.4,8.4 12.2,10.6 Q9.4,13.4 6,12.2 Q3,14.2 0,12.8 Q-3,14.2 -6,12.2 Q-9.4,13.4 -12.2,10.6 Q-13.4,8.4 -16.6,8.6 L-15.4,5.4 Q-14.8,3.6 -17,2.2 L-14.6,0 Q-15.2,-3 -11,-5 Z"
        />
        <clipPath id="ct-cclip"><use href="#ct-chp" /></clipPath>

        <!-- Белый пушистый котик (голова) -->
        <g id="ct-c">
          <use href="#ct-chp" class="ct-c-fill" />
          <g clip-path="url(#ct-cclip)">
            <path class="ct-c-shade" d="M18,-18 L18,14 L2,14 C9,9 11,-2 8.5,-13 Z" />
            <path class="ct-c-ear" d="M-11.4,-13 L-7.4,-10 L-11.8,-7 Z M11.4,-13 L7.4,-10 L11.8,-7 Z" />
            <path class="ct-c-fur" d="M-3,-10 L-1.8,-6.6 M0,-11 L0,-6.4 M3,-10 L1.8,-6.6" />
            <path class="ct-c-fur ct-c-fur-soft" d="M-13.6,5 L-10.8,5.6 M-13,8 L-10.6,7.8 M13.6,5 L10.8,5.6 M13,8 L10.6,7.8" />
          </g>
          <use href="#ct-chp" class="ct-c-ink" />
          <!-- глаза -->
          <ellipse class="ct-c-eye" cx="-5.2" cy="1.4" rx="2.7" ry="3.5" />
          <ellipse class="ct-c-eye" cx="5.2" cy="1.4" rx="2.7" ry="3.5" />
          <ellipse class="ct-c-iris" cx="-5.2" cy="2.6" rx="1.9" ry="1.8" />
          <ellipse class="ct-c-iris" cx="5.2" cy="2.6" rx="1.9" ry="1.8" />
          <circle class="ct-c-glint" cx="-6.2" cy="0.1" r="1.3" />
          <circle class="ct-c-glint" cx="4.2" cy="0.1" r="1.3" />
          <circle class="ct-c-glint ct-c-glint-s" cx="-4.1" cy="3.5" r="0.6" />
          <circle class="ct-c-glint ct-c-glint-s" cx="6.3" cy="3.5" r="0.6" />
          <!-- румянец, носик, ротик ω -->
          <ellipse class="ct-c-blush" cx="-9.6" cy="6.2" rx="2.3" ry="1.2" />
          <ellipse class="ct-c-blush" cx="9.6" cy="6.2" rx="2.3" ry="1.2" />
          <path class="ct-c-nose" d="M-1.2,4.4 Q0,4 1.2,4.4 Q0.9,5.6 0,5.9 Q-0.9,5.6 -1.2,4.4 Z" />
          <path class="ct-c-mouth" d="M0,5.9 L0,6.7 M0,6.7 Q-1.5,8.3 -3,7.1 M0,6.7 Q1.5,8.3 3,7.1" />
          <!-- бантик -->
          <path class="ct-c-bow" d="M-9,-8.4 L-14.2,-11.4 L-13.6,-5.6 Z M-9,-8.4 L-3.8,-5.8 L-4.4,-11.2 Z" />
          <circle class="ct-c-bow" cx="-9" cy="-8.4" r="1.6" />
        </g>

        <!-- Тело сидящего котёнка (без хвоста и головы) -->
        <path
          id="ct-kbp"
          d="M-13,7 Q-19,17 -16.6,27 Q-15,33.6 -8,34 L8,34 Q15,33.6 16.6,27 Q19,17 13,7 Z"
        />
        <clipPath id="ct-kclip"><use href="#ct-kbp" /></clipPath>
        <g id="ct-kit">
          <use href="#ct-kbp" class="ct-c-fill" />
          <g clip-path="url(#ct-kclip)">
            <path class="ct-c-shade" d="M20,5 L20,37 L5,37 C13,28 15,16 11.5,5 Z" />
            <path class="ct-c-fur" d="M-3,18 L-1.6,21.4 M0,17 L0,21.4 M3,18 L1.6,21.4" />
          </g>
          <use href="#ct-kbp" class="ct-c-ink" />
          <ellipse class="ct-k-paw" cx="-5.6" cy="33" rx="4.6" ry="3.3" />
          <ellipse class="ct-k-paw" cx="5.6" cy="33" rx="4.6" ry="3.3" />
          <path class="ct-k-toe" d="M-7.4,31.8 L-7.4,34.4 M-4.2,31.8 L-4.2,34.4 M4.2,31.8 L4.2,34.4 M7.4,31.8 L7.4,34.4" />
          <use href="#ct-c" />
        </g>

        <!-- Лапка-ручка (для позы «щёчки на лапках») -->
        <path id="ct-hpp" d="M-5.2,-4 Q-6,5 -3,6.6 Q0,7.6 3,6.6 Q6,5 5.2,-4 Q0,-6 -5.2,-4 Z" />
        <g id="ct-hp">
          <use href="#ct-hpp" class="ct-c-fill" />
          <path class="ct-k-toe" d="M-1.8,2.4 L-1.8,6.6 M1.8,2.4 L1.8,6.6" />
          <use href="#ct-hpp" class="ct-c-ink" />
        </g>

        <!-- Отпечаток лапки -->
        <g id="ct-pw">
          <path
            class="ct-pw-part"
            d="M0,1.5 C-5,1.5 -9,6 -7.5,10 C-6,12.5 -2.5,11 0,11 C2.5,11 6,12.5 7.5,10 C9,6 5,1.5 0,1.5 Z"
          />
          <circle class="ct-pw-part" cx="-8" cy="-1.5" r="3.2" />
          <circle class="ct-pw-part" cx="-3" cy="-6.5" r="3.4" />
          <circle class="ct-pw-part" cx="3" cy="-6.5" r="3.4" />
          <circle class="ct-pw-part" cx="8" cy="-1.5" r="3.2" />
          <path class="ct-pw-gloss" d="M-4,6 C-3,4.6 -1.4,4.2 -0.2,4.4" />
        </g>

        <!-- Сердечко -->
        <path
          id="ct-htp"
          d="M0,10.5 C-10,3.5 -15.5,-1.5 -15.5,-7.5 C-15.5,-12 -12,-14.5 -8.2,-14.5 C-4.6,-14.5 -1.6,-12.4 0,-9 C1.6,-12.4 4.6,-14.5 8.2,-14.5 C12,-14.5 15.5,-12 15.5,-7.5 C15.5,-1.5 10,3.5 0,10.5 Z"
        />
        <g id="ct-ht">
          <use href="#ct-htp" class="ct-ht-fill" />
          <use href="#ct-htp" class="ct-ht-ink" />
          <path class="ct-ht-gloss" d="M-11.2,-8 C-11.2,-10.6 -9.4,-12 -7,-11.4" />
        </g>

        <!-- Малый клубок (падающий / на шнуре) -->
        <clipPath id="ct-ybclip"><circle cx="0" cy="0" r="10" /></clipPath>
        <g id="ct-yb">
          <path class="ct-yb-thread-ink" d="M7,7 C14,10 12,17 4,16" />
          <path class="ct-yb-thread" d="M7,7 C14,10 12,17 4,16" />
          <circle class="ct-yb-fill" cx="0" cy="0" r="10" />
          <g clip-path="url(#ct-ybclip)">
            <path class="ct-yb-shade" d="M14,-2 C14,10 6,14 -2,14 C8,8 10,2 7,-10 L14,-10 Z" />
            <path class="ct-yb-line" d="M-11,-3 Q0,3 11,-6 M-11,2 Q0,8 11,-1 M-8,-9 Q-2,0 -4,11 M2,-11 Q6,0 3,11" />
          </g>
          <circle class="ct-yb-ink" cx="0" cy="0" r="10" />
          <path class="ct-yb-gloss" d="M-6.6,-4 C-6,-6.6 -4,-8 -1.6,-8" />
        </g>

        <!-- Большой катящийся клубок: общий клип -->
        <clipPath id="ct-rbclip"><circle cx="0" cy="0" r="16" /></clipPath>

        <!-- Звезда-искра -->
        <g id="ct-st">
          <path
            class="ct-st-body"
            d="M0,-11 C1,-3.5 3.5,-1 11,0 C3.5,1 1,3.5 0,11 C-1,3.5 -3.5,1 -11,0 C-3.5,-1 -1,-3.5 0,-11 Z"
          />
          <circle class="ct-st-core" r="2" />
        </g>
      </defs>
    </svg>

    <!-- ── Скринтон ── -->
    <div class="ct-tone"></div>

    <!-- ── Линии скорости ── -->
    <svg class="ct-rays" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="xMidYMid slice">
      <path
        v-for="r in rays"
        :key="r.key"
        :d="r.d"
        :class="r.white ? 'ct-ray ct-ray-w' : 'ct-ray'"
      />
    </svg>

    <!-- ── Аура ── -->
    <!-- <div class="ct-aura">
      <svg viewBox="-100 -100 200 200" class="ct-aura-svg">
        <defs>
          <radialGradient id="ct-aura-grad" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stop-color="#ffc2dc" stop-opacity="0.38" />
            <stop offset="55%" stop-color="#c9b8ff" stop-opacity="0.14" />
            <stop offset="100%" stop-color="#c9b8ff" stop-opacity="0" />
          </radialGradient>
        </defs>
        <use
          class="ct-aura-cat"
          href="#ct-chp"
          fill="url(#ct-aura-grad)"
          transform="translate(0 2) scale(5)"
        />
      </svg>
    </div> -->

    <!-- <div class="ct-flash"></div> -->

    <!-- ── Шнур по периметру ── -->
    <svg class="ct-frame" :viewBox="`0 0 ${w} ${h}`" preserveAspectRatio="none">
      <g class="ct-cord-group">
        <path :d="framePath" class="ct-cord-ink" />
        <path :d="framePath" class="ct-cord-col" />
      </g>
      <g v-for="f in frameItems" :key="f.key" :transform="f.transform">
        <use :href="f.ref" class="ct-frame-i" :style="f.style" />
      </g>
    </svg>

    <!-- ── Уголки ── -->
    <svg
      v-for="c in corners"
      :key="c.n"
      :class="`ct-corner ct-corner-${c.n}`"
      viewBox="0 0 200 200"
    >
      <!-- верхние: мордочка на лапках -->
      <template v-if="c.top">
        <g transform="translate(78 72)">
          <g class="ct-corner-tilt">
            <use href="#ct-c" transform="scale(3.3)" style="--color:#ffffff" />
          </g>
        </g>
        <use href="#ct-hp" transform="translate(52 122) rotate(8) scale(2.6)" style="--color:#ffffff" />
        <use href="#ct-hp" transform="translate(104 122) rotate(-8) scale(2.6)" style="--color:#ffffff" />
        <use
          v-for="(p, i) in TOP_PAWS"
          :key="`tp${i}`"
          href="#ct-pw"
          class="ct-corner-pulse"
          :transform="`translate(${p.x} ${p.y}) rotate(${p.r}) scale(${p.s})`"
          :style="{ '--color': p.c, animationDelay: p.d + 's' }"
        />
        <use
          v-for="(s, i) in TOP_DECOR"
          :key="`td${i}`"
          :href="s.ref"
          class="ct-corner-pulse"
          :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
          :style="{ '--color': s.c, animationDelay: s.d + 's' }"
        />
      </template>

      <!-- нижние: сидящий котёнок с хвостиком -->
      <template v-else>
        <g transform="translate(70 66) scale(3.3)">
          <g class="ct-tail-wag">
            <path class="ct-k-tail-ink" d="M13,30 C26,32 29,20 23,13" />
            <path class="ct-k-tail" d="M13,30 C26,32 29,20 23,13" />
          </g>
          <g class="ct-breathe">
            <use href="#ct-kit" style="--color:#ffffff" />
          </g>
        </g>
        <use
          v-for="(s, i) in BOT_DECOR"
          :key="`bd${i}`"
          :href="s.ref"
          class="ct-corner-pulse"
          :transform="`translate(${s.x} ${s.y}) scale(${s.s})`"
          :style="{ '--color': s.c, animationDelay: s.d + 's' }"
        />
      </template>
    </svg>

    <!-- ── Дальний слой ── -->
    <div class="ct-layer ct-far">
      <span v-for="it in items.far" :key="it.id" class="ct-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ct-item-svg"><use :href="it.ref" /></svg>
      </span>
    </div>

    <!-- ── Средний слой ── -->
    <div class="ct-layer ct-mid">
      <span v-for="it in items.mid" :key="it.id" class="ct-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ct-item-svg"><use :href="it.ref" /></svg>
      </span>
    </div>

    <!-- ── Ближний слой ── -->
    <div class="ct-layer ct-near">
      <span v-for="it in items.near" :key="it.id" class="ct-item" :style="it.style">
        <svg viewBox="-18 -18 36 36" class="ct-item-svg"><use :href="it.ref" /></svg>
      </span>
    </div>

    <!-- ── Нитка: один сплошной путь, контейнер открывает его до клубка ── -->
    <div ref="trailEl" class="ct-trail" :style="trailStyle">
      <svg
        class="ct-trail-svg"
        :width="trailW"
        height="24"
        :viewBox="`0 0 ${trailW} 24`"
      >
        <path :d="trailPath" class="ct-tr-ink" />
        <path :d="trailPath" class="ct-tr-col" />
      </svg>
    </div>

    <!-- ── Катящийся клубок: уменьшается по пути и выкатывается за край ── -->
    <div
      ref="ballEl"
      class="ct-roll"
      :style="{ width: rollSize + 'px', height: rollSize + 'px', '--color': '#ff8ac2' }"
    >
      <!-- вращающийся моток -->
      <svg ref="spinEl" class="ct-rb-svg ct-rb-spin" viewBox="-20 -20 40 40">
        <g clip-path="url(#ct-rbclip)">
          <circle class="ct-rb-fill" r="16" />
          <path class="ct-rb-dark" d="M-16,3 Q0,11 16,1 M-12,-11 Q-4,0 -7,14 M-15,9 Q-5,5 6,12" />
          <path class="ct-rb-light" d="M-16,-4 Q0,4 16,-6 M4,-15 Q9,0 5,15 M-6,-15 Q-12,-4 -9,6" />
        </g>
      </svg>
      <!-- неподвижный слой: тень, контур, блик -->
      <svg class="ct-rb-svg" viewBox="-20 -20 40 40">
        <ellipse class="ct-rb-ground" cx="0" cy="18" rx="12" ry="1.6" />
        <g clip-path="url(#ct-rbclip)">
          <path class="ct-rb-shade" d="M20,-20 L20,20 L-2,20 C10,12 13,0 10,-14 Z" />
        </g>
        <circle class="ct-rb-ink" r="16" />
        <path class="ct-rb-gloss" d="M-10.4,-4.6 C-9.6,-8.4 -6.6,-11 -2.8,-11.6" />
        <circle class="ct-rb-dot" cx="-11.8" cy="0.4" r="1" />
      </svg>
    </div>

    <!-- ── Звуковые эффекты ── -->
    <svg class="ct-sfx ct-sfx-1" viewBox="0 0 240 100">
      <g class="ct-sfx-pop">
        <text x="108" y="66" text-anchor="middle" class="ct-sfx-outer">МЯЯУ!</text>
        <text x="108" y="66" text-anchor="middle" class="ct-sfx-text">МЯЯУ!</text>
        <use href="#ct-c" transform="translate(212 36) rotate(12) scale(1.2)" style="--color:#ffffff" />
      </g>
    </svg>
    <svg class="ct-sfx ct-sfx-2" viewBox="0 0 240 100">
      <g class="ct-sfx-pop">
        <text x="108" y="66" text-anchor="middle" class="ct-sfx-outer">МУРР~</text>
        <text x="108" y="66" text-anchor="middle" class="ct-sfx-text ct-sfx-text-alt">МУРР~</text>
        <use href="#ct-ht" transform="translate(214 34) rotate(-12) scale(1.1)" style="--color:#ff9ab8" />
      </g>
    </svg>

    <!-- ── Искры ── -->
    <div class="ct-sparks">
      <span v-for="s in sparks" :key="`s${s.id}`" class="ct-spark" :style="s.style">
        <svg viewBox="-14 -14 28 28" class="ct-spark-svg"><use href="#ct-st" /></svg>
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

const CAT_COLORS = ["#ffffff", "#ffffff", "#fff7f2", "#f6f3ff"] as const;
const PAW_COLORS = ["#ffc9dc", "#ff9ab8", "#fff0f6"] as const;
const HEART_COLORS = ["#ff9ab8", "#ff7fa8", "#ffc9dc", "#ffffff"] as const;
const YARN_COLORS = ["#ff8ac2", "#7be0ff", "#b98bff", "#ffd166", "#8affd1"] as const;
const STAR_COLORS = ["#ffd166", "#fff6d6", "#ffc9dc", "#ffffff"] as const;
const FRAME_REFS = ["#ct-c", "#ct-pw", "#ct-ht", "#ct-yb", "#ct-st"] as const;

const colorFor = (ref: string): string => {
  switch (ref) {
    case "#ct-c": return pick(CAT_COLORS);
    case "#ct-pw": return pick(PAW_COLORS);
    case "#ct-ht": return pick(HEART_COLORS);
    case "#ct-yb": return pick(YARN_COLORS);
    default: return pick(STAR_COLORS);
  }
};

const corners = [
  { n: "tl", top: true },
  { n: "tr", top: true },
  { n: "bl", top: false },
  { n: "br", top: false },
] as const;

const w = ref(1280);
const h = ref(720);
let resizeRaf = 0;
const measure = () => {
  w.value = document.documentElement.clientWidth || window.innerWidth;
  h.value = window.innerHeight;
};
const onResize = () => {
  cancelAnimationFrame(resizeRaf);
  resizeRaf = requestAnimationFrame(measure);
};

const counts = computed(() => {
  const small = w.value < 640;
  return {
    far: small ? 10 : 16,
    mid: small ? 8 : 12,
    near: small ? 4 : 7,
    sparks: small ? 8 : 14,
    frame: small ? 20 : 32,
    rays: small ? 38 : 64,
  };
});

const ballEl = ref<HTMLElement | null>(null);
const spinEl = ref<SVGSVGElement | null>(null);
const trailEl = ref<HTMLElement | null>(null);

const rollSize = computed(() => (w.value < 640 ? 46 : 62));

const trailW = computed(() => Math.ceil(w.value + 240));
const trailPath = computed(() => {
  const n = Math.ceil(trailW.value / 32) + 1;
  let d = "M0,12 Q16,-4 32,12";
  for (let i = 2; i <= n; i++) d += ` T${i * 32},12`;
  return d;
});

const trailStyle = computed(() => ({
  bottom: `${(20 + rollSize.value * 0.1 - 12).toFixed(1)}px`,
}));

const SHRINK = 0.62;
const SPEED = 120;
const TRAIL_FADE = 1.6;
const PAUSE = 0.7;
const smooth = (x: number) => x * x * (3 - 2 * x);

onMounted(() => {
  measure();
  window.addEventListener("resize", onResize, { passive: true });
  const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
});
onBeforeUnmount(() => {
  cancelAnimationFrame(resizeRaf);
  window.removeEventListener("resize", onResize);
});

const TOP_PAWS = [
  { x: 156, y: 34, r: 22, s: 0.9, c: "#ffc9dc", d: 0 },
  { x: 176, y: 70, r: 12, s: 0.8, c: "#ff9ab8", d: 0.7 },
  { x: 154, y: 106, r: 26, s: 0.7, c: "#fff0f6", d: 1.4 },
] as const;

const TOP_DECOR = [
  { ref: "#ct-st", x: 178, y: 12, s: 0.9, c: "#ffd166", d: 0 },
  { ref: "#ct-ht", x: 138, y: 14, s: 0.5, c: "#ff9ab8", d: 0.8 },
  { ref: "#ct-ht", x: 20, y: 56, s: 0.5, c: "#ffc9dc", d: 1.2 },
  { ref: "#ct-st", x: 18, y: 140, s: 0.6, c: "#ffffff", d: 1.6 },
  { ref: "#ct-ht", x: 138, y: 150, s: 0.45, c: "#ff7fa8", d: 0.4 },
] as const;

const BOT_DECOR = [
  { ref: "#ct-ht", x: 178, y: 70, s: 0.6, c: "#ff9ab8", d: 0.3 },
  { ref: "#ct-st", x: 176, y: 108, s: 0.8, c: "#ffd166", d: 1.0 },
  { ref: "#ct-st", x: 14, y: 40, s: 0.6, c: "#ffffff", d: 1.5 },
  { ref: "#ct-ht", x: 22, y: 150, s: 0.45, c: "#ffc9dc", d: 0.6 },
  { ref: "#ct-st", x: 124, y: 16, s: 0.5, c: "#ffc9dc", d: 1.9 },
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

    let ref: string;
    if (layer === "near") ref = (["#ct-c", "#ct-yb", "#ct-ht", "#ct-c"] as const)[i % 4] as string;
    else if (layer === "mid") ref = (["#ct-pw", "#ct-c", "#ct-ht", "#ct-st", "#ct-yb"] as const)[i % 5] as string;
    else ref = (["#ct-st", "#ct-pw", "#ct-ht", "#ct-st", "#ct-pw"] as const)[i % 5] as string;

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

const rays = computed(() => {
  const W = w.value, H = h.value;
  const cx = W / 2, cy = H / 2;
  const rOut = Math.hypot(W, H) * 0.6;
  const rIn = rOut * 0.5;
  const rand = seeded(222);
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

const INSET = 16;
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
      "--color": pick(STAR_COLORS),
      "--tw": `${rnd(1.2, 2.4).toFixed(2)}s`,
    } as Vars,
  })),
);
</script>

<style scoped>
.ct-overlay {
  position: fixed;
  inset: 0;
  z-index: 9994;
  pointer-events: none;
  overflow: hidden;
  user-select: none;
  --ct-ink: #34202e;
  --ct-gold: #ffd166;
  --ct-aura-1: rgba(255, 190, 220, 0.3);
  --ct-aura-2: rgba(200, 185, 255, 0.18);
  --ct-ray: rgba(255, 150, 190, 0.001);
  --ct-ray-w: rgba(255, 255, 255, 0.001);
  --ct-tone: rgba(255, 160, 200, 0.001);
}

:global(html[data-theme="dark"]) .ct-overlay,
:global(body.theme-dark) .ct-overlay {
  --ct-aura-1: rgba(255, 190, 225, 0.38);
  --ct-aura-2: rgba(210, 195, 255, 0.2);
  --ct-ray: rgba(255, 170, 205, 0.26);
  --ct-ray-w: rgba(255, 235, 245, 0.24);
  --ct-tone: rgba(255, 175, 210, 0.36);
}

.ct-defs {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

/* ══════ Котик ══════ */
.ct-c-fill { fill: var(--color, #fff); stroke: none; }
.ct-c-shade { fill: color-mix(in srgb, var(--color, #fff) 68%, #8fa6e6); }
.ct-c-ear { fill: #ffb3cb; stroke: none; }
.ct-c-fur {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #fff) 55%, #8fa6e6);
  stroke-width: 1.2;
  stroke-linecap: round;
}
.ct-c-fur-soft { opacity: 0.8; }
.ct-c-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: calc(var(--sw, 2.6) * 1px);
  stroke-linejoin: round;
}
.ct-c-eye { fill: var(--ct-ink); }
.ct-c-iris { fill: #7f93ff; opacity: 0.9; }
.ct-c-glint { fill: #fff; }
.ct-c-glint-s { opacity: 0.85; }
.ct-c-blush { fill: #ff8fb4; opacity: 0.6; }
.ct-c-nose {
  fill: #ff8fb4;
  stroke: var(--ct-ink);
  stroke-width: 0.6;
  stroke-linejoin: round;
}
.ct-c-mouth {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 0.9;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ct-c-bow {
  fill: #ff7fa8;
  stroke: var(--ct-ink);
  stroke-width: 1.2;
  stroke-linejoin: round;
}

.ct-k-paw {
  fill: var(--color, #fff);
  stroke: var(--ct-ink);
  stroke-width: calc(var(--sw, 2.6) * 0.8px);
}
.ct-k-toe {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 0.9;
  stroke-linecap: round;
  opacity: 0.7;
}
.ct-k-tail-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: calc(3.6px + var(--sw, 2.6) * 2px);
  stroke-linecap: round;
}
.ct-k-tail {
  fill: none;
  stroke: #fff;
  stroke-width: 3.6;
  stroke-linecap: round;
}

/* ══════ Лапка-отпечаток ══════ */
.ct-pw-part {
  fill: var(--color, #ffc9dc);
  stroke: var(--ct-ink);
  stroke-width: calc(var(--sw, 2.2) * 1px);
  stroke-linejoin: round;
}
.ct-pw-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.5;
  stroke-linecap: round;
}

/* ══════ Сердечко ══════ */
.ct-ht-fill { fill: var(--color, #ff9ab8); }
.ct-ht-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: calc(var(--sw, 2.6) * 1px);
  stroke-linejoin: round;
}
.ct-ht-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}

/* ══════ Малый клубок ══════ */
.ct-yb-fill { fill: var(--color, #ff8ac2); }
.ct-yb-shade { fill: color-mix(in srgb, var(--color, #ff8ac2) 58%, #3a1a60); }
.ct-yb-line {
  fill: none;
  stroke: #fff;
  stroke-width: 1.3;
  stroke-linecap: round;
  opacity: 0.6;
}
.ct-yb-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: calc(var(--sw, 2.6) * 1px);
}
.ct-yb-thread-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 4.2;
  stroke-linecap: round;
}
.ct-yb-thread {
  fill: none;
  stroke: var(--color, #ff8ac2);
  stroke-width: 1.8;
  stroke-linecap: round;
}
.ct-yb-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 1.8;
  stroke-linecap: round;
}

/* ══════ Звезда ══════ */
.ct-st-body {
  fill: var(--color, #ffd166);
  stroke: var(--ct-ink);
  stroke-width: 1.8;
  stroke-linejoin: round;
}
.ct-st-core { fill: #fff; }

/* ══════ Растр + линии скорости ══════ */
.ct-tone {
  position: absolute;
  inset: -40%;
  background-image: radial-gradient(circle, var(--ct-tone) 1.3px, transparent 1.7px);
  background-size: 9px 9px;
  transform: rotate(15deg);
  -webkit-mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  mask-image: radial-gradient(ellipse 38% 34% at 50% 50%, transparent 55%, #000 100%);
  opacity: 0.75;
}

.ct-rays {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  mask-image: radial-gradient(ellipse at center, transparent 40%, #000 88%);
  animation: ct-rays-shake 0.5s steps(2, jump-none) infinite;
}
.ct-ray { fill: var(--ct-ray); }
.ct-ray-w { fill: var(--ct-ray-w); }

@keyframes ct-rays-shake {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(1.5px, -1px) scale(1.012); }
}

/* ══════ Аура ══════ */
.ct-aura {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(80vmin, 720px);
  aspect-ratio: 1;
  transform: translate(-50%, -50%);
  animation: ct-aura-pulse 4.4s ease-in-out infinite;
}
.ct-aura-svg { width: 100%; height: 100%; overflow: visible; }
.ct-aura-cat { filter: blur(6px); }

@keyframes ct-aura-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(0.94); opacity: 0.8; }
  50%      { transform: translate(-50%, -50%) scale(1.06); opacity: 1; }
}

/* ══════ Вспышка ══════ */
.ct-flash {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, var(--ct-aura-1), transparent 60%),
    radial-gradient(ellipse at 70% 60%, var(--ct-aura-2), transparent 60%);
  opacity: 0;
  animation: ct-flash 24s linear infinite;
}
@keyframes ct-flash {
  0%, 92.5%, 94.5%, 100% { opacity: 0; }
  93%   { opacity: 1; }
  94%   { opacity: 0.5; }
}

/* ══════ Шнур по периметру ══════ */
.ct-frame {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.ct-cord-group {
  animation: ct-cord-sway 7s ease-in-out infinite alternate;
  will-change: transform;
}
@keyframes ct-cord-sway {
  from { transform: translateY(-1.2px); }
  to   { transform: translateY(1.2px); }
}
.ct-cord-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 4.4;
  stroke-linecap: round;
}
.ct-cord-col {
  fill: none;
  stroke: #ffb3cf;
  stroke-width: 1.9;
  stroke-linecap: round;
  stroke-dasharray: 10 6;
}
.ct-frame-i { animation: ct-frame-twinkle 3s ease-in-out infinite; }
@keyframes ct-frame-twinkle {
  0%, 100% { opacity: 0.85; }
  50%      { opacity: 1; }
}

/* ══════ Уголки ══════ */
.ct-corner {
  --sw: 1.6;
  position: absolute;
  width: clamp(120px, 18vw, 220px);
  height: clamp(120px, 18vw, 220px);
  overflow: visible;
}
.ct-corner-tl { top: 4px; left: 4px; }
.ct-corner-tr { top: 4px; right: 4px; transform: scaleX(-1); }
.ct-corner-bl { bottom: 4px; left: 4px; }
.ct-corner-br { bottom: 4px; right: 4px; transform: scaleX(-1); }

.ct-corner-tilt {
  transform-box: fill-box;
  transform-origin: 50% 100%;
  animation: ct-corner-tilt 2.8s ease-in-out infinite;
}
@keyframes ct-corner-tilt {
  0%, 100% { transform: rotate(0deg); }
  25%      { transform: rotate(-4deg); }
  60%      { transform: rotate(3.5deg); }
}

.ct-tail-wag {
  transform-box: fill-box;
  transform-origin: 0% 100%;
  animation: ct-tail-wag 1.8s ease-in-out infinite alternate;
}
@keyframes ct-tail-wag {
  from { transform: rotate(-9deg); }
  to   { transform: rotate(9deg); }
}

.ct-breathe {
  transform-box: fill-box;
  transform-origin: 50% 100%;
  animation: ct-breathe 3.2s ease-in-out infinite;
}
@keyframes ct-breathe {
  0%, 100% { transform: scale(1, 1); }
  50%      { transform: scale(1.015, 1.025); }
}

.ct-corner-pulse {
  transform-box: fill-box;
  transform-origin: center;
  animation: ct-corner-pulse 2.6s ease-in-out infinite;
}
@keyframes ct-corner-pulse {
  0%, 100% { opacity: 0.6; scale: 0.88; }
  50%      { opacity: 1;   scale: 1.12; }
}

/* ══════ Падающие предметы ══════ */
.ct-layer { position: absolute; inset: 0; }

.ct-item {
  position: absolute;
  top: calc(var(--size) * -2);
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #fff);
  opacity: 0;
  animation: ct-fall var(--dur) cubic-bezier(0.35, 0.05, 0.65, 0.95) var(--delay) infinite;
  will-change: transform, opacity;
}

@keyframes ct-fall {
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

.ct-item-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation:
    ct-sway var(--sway-dur) ease-in-out infinite alternate,
    ct-spin var(--spin-dur) ease-in-out infinite alternate,
    ct-twinkle var(--tw-dur, 1.6s) ease-in-out infinite;
}

@keyframes ct-sway {
  from { transform: translateX(calc(-1 * var(--sway-amp, 12px))); }
  to   { transform: translateX(var(--sway-amp, 12px)); }
}
@keyframes ct-spin {
  from { rotate: -16deg; }
  to   { rotate: 16deg; }
}
@keyframes ct-twinkle {
  0%, 100% { scale: 1; }
  20%      { scale: 1.1; }
  40%      { scale: 0.97; }
  60%      { scale: 1.05; }
}

/* ══════ Нитка и катящийся клубок (движение задаёт JS) ══════ */
.ct-trail {
  position: absolute;
  left: 0;
  width: 0;
  height: 24px;
  overflow: hidden;
  opacity: 0;
  will-change: width, opacity;
}
.ct-trail-svg {
  display: block;
  max-width: none;
}
.ct-tr-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.ct-tr-col {
  fill: none;
  stroke: #ff8ac2;
  stroke-width: 2.2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.ct-roll {
  position: absolute;
  left: 0;
  bottom: 20px;
  opacity: 0;
  transform-origin: 50% 90%; /* масштаб относительно точки касания земли */
  will-change: transform, opacity;
}

.ct-rb-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.ct-rb-spin {
  transform-origin: 50% 50%;
  will-change: transform;
}

.ct-rb-fill { fill: var(--color, #ff8ac2); }
.ct-rb-dark {
  fill: none;
  stroke: color-mix(in srgb, var(--color, #ff8ac2) 55%, #3a1a60);
  stroke-width: 1.8;
  stroke-linecap: round;
}
.ct-rb-light {
  fill: none;
  stroke: #fff;
  stroke-width: 1.5;
  stroke-linecap: round;
  opacity: 0.65;
}
.ct-rb-shade { fill: color-mix(in srgb, var(--color, #ff8ac2) 40%, #2a0f50); opacity: 0.55; }
.ct-rb-ink {
  fill: none;
  stroke: var(--ct-ink);
  stroke-width: 2.6;
}
.ct-rb-gloss {
  fill: none;
  stroke: #fff;
  stroke-width: 2;
  stroke-linecap: round;
}
.ct-rb-dot { fill: #fff; }
.ct-rb-ground { fill: var(--ct-ink); opacity: 0.25; }

/* ══════ Звуковые эффекты ══════ */
.ct-sfx {
  position: absolute;
  width: clamp(110px, 15vw, 210px);
  overflow: visible;
}
.ct-sfx-1 { left: 3vw; top: 40%; rotate: -10deg; }
.ct-sfx-2 { right: 3vw; top: 60%; rotate: 8deg; }
.ct-sfx-2 .ct-sfx-pop { animation-delay: 4.5s; }

.ct-sfx-pop {
  transform-box: fill-box;
  transform-origin: center;
  opacity: 0;
  animation: ct-sfx-pop 9s ease-in-out infinite;
}

.ct-sfx-outer,
.ct-sfx-text {
  font-family: "Arial Black", "Segoe UI Black", "Noto Sans", "Roboto", "Helvetica Neue", Arial, sans-serif;
  font-size: 46px;
  font-weight: 900;
  letter-spacing: -1px;
  stroke-linejoin: round;
}
.ct-sfx-outer {
  fill: #fff;
  stroke: #fff;
  stroke-width: 14;
}
.ct-sfx-text {
  fill: #ff9ab8;
  stroke: var(--ct-ink);
  stroke-width: 6;
  paint-order: stroke fill;
}
.ct-sfx-text-alt { fill: #b9a8ff; }

@keyframes ct-sfx-pop {
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
.ct-sparks { position: absolute; inset: 0; }

.ct-spark {
  position: absolute;
  bottom: -20px;
  left: var(--left);
  width: var(--size);
  height: var(--size);
  color: var(--color, #ffd166);
  opacity: 0;
  animation: ct-spark-rise var(--dur) linear var(--delay) infinite;
  will-change: transform, opacity;
}
.ct-spark-svg {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
  transform-origin: 50% 50%;
  animation: ct-spark-twinkle var(--tw, 1.6s) ease-in-out infinite alternate;
}
@keyframes ct-spark-rise {
  0%   { transform: translate3d(0, 0, 0); opacity: 0; }
  10%  { opacity: 1; }
  90%  { opacity: 0.85; }
  100% { transform: translate3d(var(--drift), -108vh, 0); opacity: 0; }
}
@keyframes ct-spark-twinkle {
  from { scale: 0.55; rotate: 0deg; }
  to   { scale: 1.15; rotate: 45deg; }
}

/* ══════ Доступность и печать ══════ */
@media (prefers-reduced-motion: reduce) {
  .ct-overlay { display: none; }
}
@media print {
  .ct-overlay { display: none; }
}
</style>