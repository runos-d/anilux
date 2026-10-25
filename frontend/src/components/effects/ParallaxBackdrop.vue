<template>
  <div ref="rootEl" class="parallax-backdrop" aria-hidden="true">
    <span class="orb orb--1"></span>
    <span class="orb orb--2"></span>
    <span class="orb orb--3"></span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";

/**
 * Параллакс-эффект: размытые акцентные «шары» на разной глубине смещаются
 * за курсором и прокруткой. Включается переключателем «Параллакс-эффект»
 * в настройках оформления.
 */
const rootEl = ref<HTMLElement | null>(null);

let frame = 0;
let mx = 0;
let my = 0;
let sy = 0;

const flush = () => {
  frame = 0;
  const el = rootEl.value;
  if (!el) return;
  el.style.setProperty("--mx", mx.toFixed(3));
  el.style.setProperty("--my", my.toFixed(3));
  el.style.setProperty("--sy", sy.toFixed(0));
};

const schedule = () => {
  if (!frame) frame = window.requestAnimationFrame(flush);
};

const onPointerMove = (event: PointerEvent) => {
  mx = (event.clientX / window.innerWidth - 0.5) * 2;
  my = (event.clientY / window.innerHeight - 0.5) * 2;
  schedule();
};

const onScroll = () => {
  sy = window.scrollY;
  schedule();
};

onMounted(() => {
  sy = window.scrollY;
  schedule();
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("scroll", onScroll, { passive: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("scroll", onScroll);
  if (frame) window.cancelAnimationFrame(frame);
});
</script>

<style scoped>
.parallax-backdrop {
  --mx: 0;
  --my: 0;
  --sy: 0;
  position: fixed;
  inset: 0;
  z-index: 1;
  overflow: hidden;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.16;
  transition: transform 0.9s var(--ease-petal, ease-out);
  will-change: transform;
}

.orb--1 {
  top: -8%;
  left: -6%;
  width: 46vmax;
  height: 46vmax;
  background: var(--accent);
  transform: translate3d(
    calc(var(--mx) * 42px),
    calc(var(--my) * 42px + var(--sy) * -0.1px),
    0
  );
}

.orb--2 {
  right: -10%;
  bottom: 4%;
  width: 38vmax;
  height: 38vmax;
  background: var(--accent-2, var(--accent));
  transform: translate3d(
    calc(var(--mx) * -64px),
    calc(var(--my) * -64px + var(--sy) * -0.18px),
    0
  );
}

.orb--3 {
  top: 38%;
  left: 42%;
  width: 26vmax;
  height: 26vmax;
  background: var(--accent-3, var(--accent));
  opacity: 0.1;
  transform: translate3d(
    calc(var(--mx) * 26px),
    calc(var(--my) * 26px + var(--sy) * -0.05px),
    0
  );
}

</style>
