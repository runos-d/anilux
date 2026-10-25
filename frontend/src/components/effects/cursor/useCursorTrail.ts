import { onBeforeUnmount, onMounted, ref, type CSSProperties } from "vue";

export interface CursorParticle {
  id: number;
  kind: string;
  ref: string;
  style: CSSProperties;
  born: number;
  life: number;
}

export interface CursorTrailOptions {
  maxParticles?: number;
  spawnIntervalMs?: number;
  minMovePx?: number;
  makeParticle: () => {
    kind: string;
    ref: string;
    vars: Record<string, string>;
    life: number;
  };
}

export const rnd = (min: number, max: number): number =>
  min + Math.random() * (max - min);

export const pick = <T>(items: readonly T[]): T =>
  items[Math.floor(Math.random() * items.length)] as T;

export function useCursorTrail(options: CursorTrailOptions) {
  const { maxParticles = 30, spawnIntervalMs = 60, minMovePx = 22 } = options;

  const particles = ref<CursorParticle[]>([]);

  let nextId = 0;
  let lastX = 0;
  let lastY = 0;
  let hasLast = false;
  let lastSpawn = 0;
  let frame: number | null = null;
  let pruneTimer: ReturnType<typeof setInterval> | null = null;

  const prune = (): void => {
    const now = performance.now();
    particles.value = particles.value.filter((p) => now - p.born < p.life);
  };

  const onMove = (event: PointerEvent): void => {
    const x = event.clientX;
    const y = event.clientY;

    if (frame !== null) {
      lastX = x;
      lastY = y;
      hasLast = true;
      return;
    }

    frame = requestAnimationFrame(() => {
      frame = null;
      const now = performance.now();
      const dist = hasLast ? Math.hypot(lastX - x, lastY - y) : 0;
      hasLast = true;
      lastX = x;
      lastY = y;

      if (dist === 0) return;

      const elapsed = now - lastSpawn;
      const canSpawn =
        dist >= minMovePx
          ? elapsed >= spawnIntervalMs
          : elapsed >= spawnIntervalMs * 4;
      if (!canSpawn) return;

      lastSpawn = now;
      prune();
      const built = options.makeParticle();
      particles.value.push({
        id: nextId++,
        kind: built.kind,
        ref: built.ref,
        born: now,
        life: built.life,
        style: { left: `${x}px`, top: `${y}px`, ...built.vars } as CSSProperties,
      });
      if (particles.value.length > maxParticles) {
        particles.value.splice(0, particles.value.length - maxParticles);
      }
    });
  };

  onMounted(() => {
    window.addEventListener("pointermove", onMove, { passive: true });
    pruneTimer = setInterval(prune, 400);
  });

  onBeforeUnmount(() => {
    window.removeEventListener("pointermove", onMove);
    if (frame !== null) cancelAnimationFrame(frame);
    if (pruneTimer !== null) clearInterval(pruneTimer);
    particles.value = [];
  });

  return { particles };
}