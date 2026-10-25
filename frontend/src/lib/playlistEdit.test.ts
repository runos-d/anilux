import { describe, expect, it } from 'vitest';
import { playlistEditPlan } from './playlistEdit';

describe('playlist editor and real item identifiers', () => {
  it('keeps unchanged items when the API supplies anime_id rather than anime', () => {
    expect(playlistEditPlan([{ id: 701, anime_id: 202 }], [{ id: 202 }])).toEqual({ toAdd: [], toRemove: [] });
  });
  it('removes only the deselected item and adds the chosen anime', () => {
    const old = { id: 701, anime_id: 202 };
    expect(playlistEditPlan([old, { id: 702, anime_id: 203 }], [{ id: 203 }, { id: 204 }])).toEqual({ toAdd: [{ id: 204 }], toRemove: [old] });
  });
  it('supports legacy nested anime data and never deletes a row with no anime identity', () => {
    expect(playlistEditPlan([{ id: 701, anime: { id: 202 } }, { id: 702 }], [{ id: 202 }])).toEqual({ toAdd: [], toRemove: [] });
  });
});
