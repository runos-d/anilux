export type Presence = { is_online: boolean; last_seen?: string };

/** Reconcile a complete snapshot without overwriting newer socket events. */
export function reconcilePresence(
  current: Map<number, Presence>, before: Map<number, Presence>,
  onlineIds: number[], update: (id: number, online: boolean) => void, ownId?: number,
) {
  const online = new Set(onlineIds);
  for (const id of new Set([...current.keys(), ...online])) {
    if (id === ownId || current.get(id) !== before.get(id)) continue;
    const next = online.has(id);
    if ((current.get(id)?.is_online ?? false) !== next) update(id, next);
  }
}
