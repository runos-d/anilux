import apiClient from '@/api/client';
import type { Excerpt } from '@/api/excerpts';

type Entry = { id: number; token?: string; owner: boolean; visible: boolean; callback: (value: Excerpt | null) => void };
const entries = new Map<string, Entry>();
let timer: ReturnType<typeof setInterval> | undefined;
let pending = false;
let sequence = 0;
async function refresh() {
  if (pending || document.hidden) return;
  const active = [...entries].filter(([, entry]) => entry.visible);
  if (!active.length) return;
  pending = true;
  try {
    const groups = new Map<string, typeof active>();
    for (const item of active) {
      const signature = JSON.stringify([item[1].id, item[1].owner, item[1].token]);
      const group = groups.get(signature) || [];
      group.push(item); groups.set(signature, group);
    }
    const unique = [...groups.values()];
    for (let offset = 0; offset < unique.length; offset += 100) {
      const batchGroups = unique.slice(offset, offset + 100);
      const batch = batchGroups.map(group => group[0]!);
      const { data } = await apiClient.post<{ results: { key: string; excerpt: Excerpt | null }[] }>('/anime/excerpts/check/', {
        items: batch.map(([key, entry]) => ({ id: entry.id, token: entry.token, owner: entry.owner, key })),
      });
      for (const row of data.results) {
        const group = batchGroups.find(items => items[0]![0] === row.key) || [];
        for (const [key, expected] of group) if (entries.get(key) === expected) expected.callback(row.excerpt);
      }
    }
  } catch { /* A transient failure keeps the last validated snapshot. */ }
  finally { pending = false; }
}

export function registerExcerptCheck(excerpt: Excerpt, owner: boolean, callback: Entry['callback']) {
  const key = String(++sequence);
  const entry: Entry = { id: excerpt.id, token: excerpt.share_path?.split('/').pop(), owner, callback, visible: false };
  entries.set(key, entry);
  if (!timer) timer = setInterval(() => void refresh(), 60_000);
  return {
    visible: (value: boolean) => { entry.visible = value; },
    stop: () => { entries.delete(key); if (!entries.size) { clearInterval(timer); timer = undefined; } },
  };
}
