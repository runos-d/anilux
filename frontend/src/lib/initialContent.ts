import { queryClient } from './queryClient';

let ready = false;
let scheduled = false;
const pending = new Set<() => void>();
const visibleReads = new Set(['catalog', 'calendar', 'home', 'home-blocks', 'feed', 'post', 'profile', 'library', 'playlists', 'notifications', 'private-chats', 'group-chats']);
const release = () => {
  if (ready || scheduled) return;
  scheduled = true; clearTimeout(fallback); unsubscribe();
  requestAnimationFrame(() => requestAnimationFrame(() => {
    ready = true;
    for (const task of pending) task();
    pending.clear();
  }));
};
const unsubscribe = queryClient.getQueryCache().subscribe(event => {
  if (event.type !== 'updated' || event.action.type !== 'success') return;
  const key = event.query.queryKey;
  if (key[0] === 'recommendations' || key[0] === 'home' || (key[0] === 'read' && visibleReads.has(String(key[2])))) release();
});
const fallback = setTimeout(release, 1600);

export function afterInitialContent(task: () => void): void {
  if (ready) task(); else pending.add(task);
}
