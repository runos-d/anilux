import type { EffectsManager } from "@/lib/EffectsManager";

export interface CursorTheme {
  name: string;
  spawnIntervalMs: number;
  maxParticles: number;
  particleLifeMs: { min: number; max: number };
  particleSizePx: { min: number; max: number };
  colors: string[];
  interactionRadius: number; // radius for particle-cursor interaction
  windNoise: number; // amplitude of random wind per frame
}

export interface CursorParticle {
  id: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  born: number;
  color: string;
  size: number;
  kind: string;
}

export class CursorFx {
  private manager: EffectsManager;
  private registry: Map<string, CursorTheme>;
  private activeTheme: string | null = null;
  private particles: CursorParticle[] = [];
  private nextId = 0;
  private lastMoveTime = 0;
  private pointerPos = { x: 0, y: 0 };
  private running = false;

  constructor(manager: EffectsManager) {
    this.manager = manager;
    this.registry = new Map();
  }

  registerTheme(name: string, theme: CursorTheme): void {
    this.registry.set(name, theme);
  }

  setActiveTheme(name: string | null): void {
    if (this.activeTheme === name) return;
    this.activeTheme = name;
    if (name === null) {
    }
  }

  start(): void {
    this.running = true;
  }

  stop(): void {
    this.running = false;
    this.particles = [];
    this.activeTheme = null;
  }

  destroy(): void {
    this.stop();
    this.registry.clear();
    this.particles = [];
  }

  update(dt: number, pointer: { x: number; y: number }): void {
    const dist = Math.hypot(pointer.x - this.pointerPos.x, pointer.y - this.pointerPos.y);
    this.pointerPos = { ...pointer };
    if (!this.running || !this.activeTheme || dt <= 0) return;

    const theme = this.registry.get(this.activeTheme);
    if (!theme) return;

    const budget = this.manager.getBudget();
    const touchDisabled = typeof navigator !== "undefined" && navigator.maxTouchPoints > 0;
    const maxParticles = touchDisabled ? 0 : Math.min(theme.maxParticles, Math.floor(budget * 0.15)); // cursor gets subset of budget

    const now = performance.now();
    const canSpawn = dist > 0 && now - this.lastMoveTime >= theme.spawnIntervalMs;
    if (canSpawn && this.particles.length < maxParticles) {
      this.lastMoveTime = now;
      const color = theme.colors[Math.floor(Math.random() * theme.colors.length)] ?? '#ffffff';
      this.particles.push({
        id: this.nextId++,
        x: pointer.x,
        y: pointer.y,
        vx: (Math.random() - 0.5) * theme.windNoise,
        vy: -Math.random() * 10 - 5,
        life: theme.particleLifeMs.min + Math.random() * (theme.particleLifeMs.max - theme.particleLifeMs.min),
        born: now,
        color,
        size: theme.particleSizePx.min + Math.random() * (theme.particleSizePx.max - theme.particleSizePx.min),
        kind: this.activeTheme || "default",
      });
    }

    const interactionR = theme.interactionRadius;
    for (let i = this.particles.length - 1; i >= 0; i--) {
      const p = this.particles[i];
      if (!p) continue;
      p.x += p.vx * dt;
      p.y += p.vy * dt;

      const dx = pointer.x - p.x;
      const dy = pointer.y - p.y;
      const distToPointer = Math.hypot(dx, dy);
      if (distToPointer < interactionR && distToPointer > 1) {
        const force = (interactionR - distToPointer) / interactionR;
        p.vx += (dx / distToPointer) * force * 30 * dt;
        p.vy += (dy / distToPointer) * force * 30 * dt;
      }

      p.vx += (Math.random() - 0.5) * theme.windNoise * dt;
      p.vy += -Math.random() * theme.windNoise * 0.5 * dt;

      p.life -= dt * 1000;
      if (p.life <= 0) {
        this.particles.splice(i, 1);
      }
    }
  }

  getParticles(): CursorParticle[] {
    return this.particles;
  }
}
