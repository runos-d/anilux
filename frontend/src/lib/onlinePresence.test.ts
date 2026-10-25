import { describe, expect, it } from 'vitest';
import { reconcilePresence, type Presence } from './onlinePresence';

describe('presence snapshots', () => {
  it('removes expired online states and revives users who reconnect', () => {
    const current = new Map<number, Presence>([[1, { is_online: true }], [2, { is_online: false }]]);
    reconcilePresence(current, new Map(current), [2], (id, is_online) => current.set(id, { is_online }));
    expect(current.get(1)?.is_online).toBe(false);
    expect(current.get(2)?.is_online).toBe(true);
  });

  it('preserves socket changes received while a snapshot is in flight', () => {
    const current = new Map<number, Presence>([[1, { is_online: true }]]);
    const before = new Map(current);
    current.set(1, { is_online: false });
    current.set(2, { is_online: true });
    reconcilePresence(current, before, [1], (id, is_online) => current.set(id, { is_online }));
    expect(current.get(1)?.is_online).toBe(false);
    expect(current.get(2)?.is_online).toBe(true);
  });
});
