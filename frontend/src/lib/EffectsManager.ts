import type { CursorFx } from "./CursorFx";

export interface EffectModule {
  name: string;
  init: (ctx: { canvas?: HTMLCanvasElement }) => void;
  update: (dt: number, pointer: { x: number; y: number }) => void;
  draw: (ctx: CanvasRenderingContext2D) => void;
  resize: () => void;
  destroy: () => void;
}

export interface EffectsManagerOptions {
  maxParticlesDesktop?: number;
  maxParticlesMobile?: number;
  particleScaleMobile?: number;
  dtCapMs?: number;
  adaptiveQualityFrames?: number;
}

export class EffectsManager {
  private rAFId: number | null = null;
  private lastTime = 0;
  private dt = 0;
  private running = false;
  private paused = false;
  private registry = new Map<string, EffectModule>();
  private pointer = { x: 0, y: 0 };
  public cursorFx?: CursorFx;
  private options: Required<EffectsManagerOptions>;
  private averageDt = 0;
  private dtHistory: number[] = [];
  private budgetParticles = 150;
  private visibilityHandler?: () => void;
  private reducedMotionQuery?: MediaQueryList;
  private reducedMotionHandler?: (event: MediaQueryListEvent) => void;
  private reducedMotion = false;

  constructor(options?: EffectsManagerOptions) {
    this.options = {
      maxParticlesDesktop: 150,
      maxParticlesMobile: 60,
      particleScaleMobile: 0.4,
      dtCapMs: 50,
      adaptiveQualityFrames: 10,
      ...options,
    };
    this.budgetParticles = this.isMobile() ? this.options.maxParticlesMobile : this.options.maxParticlesDesktop;
  }

  private isMobile = (): boolean =>
    typeof window !== "undefined" && (window.innerWidth < 640 || navigator.maxTouchPoints > 0);

  private isLowHardware = (): boolean =>
    typeof navigator !== "undefined" &&
    "hardwareConcurrency" in navigator &&
    (navigator as { hardwareConcurrency?: number }).hardwareConcurrency !== undefined &&
    (navigator as { hardwareConcurrency: number }).hardwareConcurrency <= 4;

  register(name: string, module: EffectModule): void {
    this.registry.set(name, module);
  }

  unregister(name: string): void {
    const mod = this.registry.get(name);
    if (mod) mod.destroy();
    this.registry.delete(name);
  }

  start(): void {
    if (this.running) return;
    this.running = true;
    this.setupAutoPause();
    this.resumeAnimation();
  }

  stop(): void {
    this.running = false;
    if (this.rAFId !== null) cancelAnimationFrame(this.rAFId);
    this.rAFId = null;
    this.teardownAutoPause();
  }

  destroy(): void {
    this.stop();
    this.running = false;
    this.paused = true;
    for (const mod of this.registry.values()) {
      try { mod.destroy(); } catch { /* ignore */ }
    }
    this.registry.clear();
    this.pointer = { x: 0, y: 0 };
  }

  private tick = (): void => {
    if (!this.running || this.paused) return;
    const now = performance.now();
    let dt = (now - this.lastTime) / 1000;
    this.lastTime = now;

    if (dt > this.options.dtCapMs / 1000) dt = this.options.dtCapMs / 1000;

    this.dtHistory.push(dt * 1000);
    if (this.dtHistory.length > this.options.adaptiveQualityFrames) this.dtHistory.shift();
    this.averageDt = this.dtHistory.reduce((a, b) => a + b, 0) / this.dtHistory.length;
    if (this.averageDt > 20 && this.budgetParticles > 60) {
      this.budgetParticles = Math.max(60, Math.floor(this.budgetParticles * 0.8));
    } else if (this.averageDt < 16) {
      this.budgetParticles = Math.min(
        this.isMobile() ? this.options.maxParticlesMobile : this.options.maxParticlesDesktop,
        Math.floor(this.budgetParticles * 1.1),
      );
    }

    if (this.cursorFx && this.running && !this.paused) {
      try { this.cursorFx.update(dt, this.pointer); } catch { /* ignore */ }
    }

    for (const mod of this.registry.values()) {
      try { mod.update(dt, this.pointer); } catch { /* ignore per-module errors */ }
    }

    this.rAFId = requestAnimationFrame(this.tick);
  };

  getBudget(): number {
    const area = typeof window !== "undefined" ? window.innerWidth * window.innerHeight : 1280 * 720;
    const desktopArea = 1280 * 720;
    const scaled = Math.floor(this.budgetParticles * Math.sqrt(area / desktopArea));
    return Math.max(this.isMobile() ? this.options.maxParticlesMobile : 30, Math.min(scaled, this.isMobile() ? this.options.maxParticlesMobile : this.options.maxParticlesDesktop));
  }

  getAverageDt(): number {
    return this.averageDt;
  }

  onPointerMove = (e: PointerEvent): void => {
    this.pointer = { x: e.clientX, y: e.clientY };
  };

  private setupAutoPause = (): void => {
    if (this.visibilityHandler) return;

    this.visibilityHandler = () => {
      if (document.hidden) this.pauseAnimation();
      else this.resumeAnimation();
    };
    document.addEventListener("visibilitychange", this.visibilityHandler);

    this.reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    this.reducedMotion = this.reducedMotionQuery.matches;
    this.reducedMotionHandler = (event: MediaQueryListEvent) => {
      this.reducedMotion = event.matches;
      if (event.matches) this.pauseAnimation();
      else this.resumeAnimation();
    };
    this.reducedMotionQuery.addEventListener("change", this.reducedMotionHandler);

    if (document.hidden || this.reducedMotion) this.pauseAnimation();
  };

  private teardownAutoPause = (): void => {
    if (this.visibilityHandler) {
      document.removeEventListener("visibilitychange", this.visibilityHandler);
      this.visibilityHandler = undefined;
    }
    if (this.reducedMotionQuery && this.reducedMotionHandler) {
      this.reducedMotionQuery.removeEventListener("change", this.reducedMotionHandler);
    }
    this.reducedMotionQuery = undefined;
    this.reducedMotionHandler = undefined;
    this.reducedMotion = false;
  }

  private pauseAnimation(): void {
    this.paused = true;
    if (this.rAFId !== null) cancelAnimationFrame(this.rAFId);
    this.rAFId = null;
  }

  private resumeAnimation(): void {
    if (!this.running || document.hidden || this.reducedMotion || this.rAFId !== null) return;
    this.paused = false;
    this.lastTime = performance.now();
    this.tick();
  }
}
