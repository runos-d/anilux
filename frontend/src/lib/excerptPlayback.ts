import type { Excerpt } from '@/api/excerpts';

export interface ExcerptPlayer { play: () => void; pause: () => void; seek: (time: number) => void; getTime: () => void }
export type EpisodeEvent = { episode: number | null; season: number | null; translation: { id: number } };

/** Only instantiated by the excerpt page. Rounded time_update never defines a boundary. */
export class ExcerptPlayback {
  private active = false;
  private finished = false;
  private verified = false;
  private duration = 0;
  private invalid = false;
  private timer?: ReturnType<typeof setInterval>;
  private lastReply = Date.now();
  private awaitingStart = false;
  private seekStarted = 0;
  constructor(private excerpt: Excerpt, private player: ExcerptPlayer, private fail: (message: string) => void) {}

  episode(data: EpisodeEvent) {
    if (Number(data.translation.id) !== this.excerpt.translation_id ||
      (data.episode !== null && data.episode !== this.excerpt.episode) ||
      (data.season !== null && data.season !== this.excerpt.season)) {
      this.invalidate('Плеер сменил серию или озвучку. Откройте отрывок заново.'); return;
    }
    if (!this.verified) { this.verified = true; this.player.seek(this.excerpt.start); }
  }
  durationUpdate(duration: number) {
    this.duration = duration;
    if (!Number.isFinite(duration) || duration < this.excerpt.end) this.invalidate('Диапазон больше фактической длительности видео.');
  }
  play() {
    if (this.awaitingStart) return;
    if (this.invalid || this.finished) { this.player.pause(); return; }
    this.active = true;
    this.lastReply = Date.now();
    this.poll();
  }
  private poll() {
    clearInterval(this.timer);
    this.player.getTime();
    this.timer = setInterval(() => {
      if (this.awaitingStart && Date.now() - this.seekStarted > 2000) {
        this.invalidate('Плеер не подтвердил начало отрывка. Откройте его заново.'); return;
      }
      if (Date.now() - this.lastReply > 1500) { this.invalidate('Плеер перестал передавать время. Воспроизведение остановлено.'); return; }
      this.player.getTime();
    }, 100);
  }
  preciseTime(time: number) {
    if (!Number.isFinite(time)) return;
    this.lastReply = Date.now();
    if (this.awaitingStart && !this.invalid) {
      if (Math.abs(time - this.excerpt.start) <= 0.05) {
        this.awaitingStart = false;
        this.player.play();
        this.play();
      }
      return;
    }
    if (!this.active || this.invalid) return;
    if (!this.verified || !this.duration) { this.player.pause(); this.pause(); return; }
    if (time >= this.excerpt.end) {
      this.finished = true; this.player.pause(); this.player.seek(this.excerpt.end); this.pause();
    } else if (time < this.excerpt.start) this.player.seek(this.excerpt.start);
  }
  roundedTime() { if (this.active) this.player.getTime(); }
  pause() { this.active = false; if (!this.awaitingStart) clearInterval(this.timer); }
  ended() { this.awaitingStart = false; this.finished = true; this.player.pause(); this.pause(); }
  repeat() {
    if (this.invalid) return;
    this.finished = false;
    if (!this.verified || !this.duration) {
      this.player.seek(this.excerpt.start); this.player.play(); return;
    }
    this.player.pause(); this.active = false; this.awaitingStart = true;
    this.seekStarted = this.lastReply = Date.now();
    this.player.seek(this.excerpt.start); this.poll();
  }
  invalidate(message: string) { this.invalid = true; this.awaitingStart = false; this.player.pause(); this.pause(); this.fail(message); }
  dispose() { this.awaitingStart = false; this.player.pause(); this.pause(); }
}
