import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ExcerptPlayback } from './excerptPlayback';
import { parseExcerptTime, type Excerpt } from '@/api/excerpts';

const excerpt = { start: 10.25, end: 11.75, episode: 3, season: 2, translation_id: 77 } as Excerpt;
describe('Excerpt playback', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());
  function setup() {
    const player = { play: vi.fn(), pause: vi.fn(), seek: vi.fn(), getTime: vi.fn() }, fail = vi.fn();
    const controller = new ExcerptPlayback(excerpt, player, fail);
    controller.episode({ episode: 3, season: 2, translation: { id: 77 } }); controller.durationUpdate(1200);
    return { player, fail, controller };
  }
  it('does not autoplay and stops on fractional time, with no automatic repeat', () => {
    const { player, controller } = setup();
    expect(player.play).not.toHaveBeenCalled(); expect(player.seek).toHaveBeenCalledWith(10.25);
    controller.play(); controller.roundedTime(); controller.preciseTime(11.7);
    expect(player.pause).not.toHaveBeenCalled(); controller.preciseTime(11.8);
    expect(player.pause).toHaveBeenCalledOnce(); expect(player.seek).toHaveBeenLastCalledWith(11.75);
    vi.advanceTimersByTime(2000); expect(player.play).not.toHaveBeenCalled();
    controller.play(); expect(player.pause).toHaveBeenCalledTimes(2);
    controller.repeat(); expect(player.seek).toHaveBeenLastCalledWith(10.25);
    controller.preciseTime(11.75); expect(player.play).not.toHaveBeenCalled();
    controller.pause(); // asynchronous pause event must not cancel seek verification
    controller.preciseTime(10.25); expect(player.play).toHaveBeenCalledOnce();
    controller.dispose();
  });
  it('fails closed when a replay seek never becomes visible in get_time', () => {
    const { controller, fail, player } = setup();
    controller.repeat();
    for (let i = 0; i < 22; i++) { controller.preciseTime(11.75); vi.advanceTimersByTime(100); }
    expect(fail).toHaveBeenCalledOnce(); expect(player.play).not.toHaveBeenCalled(); controller.dispose();
  });
  it('measures polling stop error under bounded 20ms message latency', () => {
    const { player, controller } = setup();
    const started = Date.now(); let pauseAt = 0;
    player.pause.mockImplementation(() => { pauseAt = Date.now(); });
    player.getTime.mockImplementation(() => {
      const time = 10.25 + (Date.now() - started) / 1000;
      setTimeout(() => controller.preciseTime(time), 20);
    });
    controller.play(); vi.advanceTimersByTime(2000);
    expect(pauseAt - started - 1500).toBe(20); // measured, simulated latency only
    controller.dispose();
  });
  it.each([{ episode: 4, season: 2, translation: { id: 77 } }, { episode: 3, season: 3, translation: { id: 77 } }, { episode: null, season: null, translation: { id: 78 } }])('fails closed on material change %j', value => {
    const { player, fail, controller } = setup(); controller.play(); controller.episode(value);
    expect(fail).toHaveBeenCalledOnce(); expect(player.pause).toHaveBeenCalledOnce();
    controller.repeat(); expect(player.play).not.toHaveBeenCalled(); controller.dispose();
  });
  it('supports documented null identity for the direct episode link', () => {
    const { controller, fail } = setup(); controller.episode({ episode: null, season: null, translation: { id: 77 } }); expect(fail).not.toHaveBeenCalled(); controller.dispose();
  });
  it('ends without switching or autoplay and fails closed on missing time or short duration', () => {
    const { controller, player, fail } = setup(); controller.play(); vi.advanceTimersByTime(1600);
    expect(fail).toHaveBeenCalledOnce(); expect(player.pause).toHaveBeenCalled();
    controller.repeat(); expect(player.play).not.toHaveBeenCalled(); controller.dispose();
    const second = setup(); second.controller.durationUpdate(11); expect(second.fail).toHaveBeenCalled(); second.controller.dispose();
    const third = setup(); third.controller.play(); third.controller.ended(); vi.advanceTimersByTime(2000); expect(third.player.play).not.toHaveBeenCalled(); third.controller.dispose();
  });
  it('parses editable ranges without accepting invalid time components', () => {
    expect(parseExcerptTime('1:02.25')).toBe(62.25); expect(parseExcerptTime('1:02:03')).toBe(3723);
    for (const value of ['-1', 'NaN', '1:99', '', 'Infinity']) expect(parseExcerptTime(value)).toBeNaN();
  });
});
