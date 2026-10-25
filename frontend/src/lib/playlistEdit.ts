interface ExistingItem {
  id: number;
  anime_id?: number | string | null;
  anime?: unknown;
  notes?: string;
}

export function playlistItemAnimeId(item: ExistingItem): number {
  const legacy = typeof item.anime === 'object' && item.anime !== null
    ? (item.anime as { id?: unknown }).id : item.anime;
  const id = Number(item.anime_id ?? legacy);
  return Number.isSafeInteger(id) && id > 0 ? id : 0;
}

export function playlistEditPlan<T extends { id: number }>(items: readonly ExistingItem[], selected: readonly T[]) {
  const existing = new Set(items.map(playlistItemAnimeId).filter(Boolean));
  const wanted = new Set(selected.map(item => item.id));
  return {
    toAdd: selected.filter(item => !existing.has(item.id)),
    toRemove: items.filter(item => { const id = playlistItemAnimeId(item); return id && !wanted.has(id); }),
  };
}
