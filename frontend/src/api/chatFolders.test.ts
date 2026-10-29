import { beforeEach, expect, it, vi } from 'vitest';
const runtime = vi.hoisted(() => ({ owner: 1, get: vi.fn() }));
vi.mock('./client', async importOriginal => { const actual = await importOriginal<typeof import('./client')>(); return { ...actual, default: { get: runtime.get }, isRequestCancelled: () => false }; });
vi.mock('@/stores/auth', () => ({ useAuthStore: () => ({ user: { id: runtime.owner } }) }));
import { queryClient } from '@/lib/queryClient';
import { chatFoldersApi } from './chatFolders';
beforeEach(() => { queryClient.clear(); runtime.owner = 1; runtime.get.mockReset().mockResolvedValue({ data: { results: [] } }); });
it('shares discussion reads with the canonical group list cache', async () => {
  await Promise.all([chatFoldersApi.getPreview(-4), chatFoldersApi.getFolderChats(-4)]);
  expect(runtime.get).toHaveBeenCalledTimes(1);
  expect(queryClient.getQueryData(['read', '1', 'group-chats'])).toEqual({ results: [] });
});
it('keeps discussion cache isolated by account', async () => {
  await chatFoldersApi.getPreview(-4);
  runtime.owner = 2;
  await chatFoldersApi.getFolderChats(-4);
  expect(runtime.get).toHaveBeenCalledTimes(2);
});

it('resolves relative discussion posters through the shared media origin', async () => {
  vi.stubEnv('VITE_BASE_URL', '');
  try {
    runtime.get.mockResolvedValue({ data: { results: [{ id:1, anime_id:1, anime_title:'Title', anime_poster:'/media/poster.jpg' }] } });
    const preview=await chatFoldersApi.getPreview(-4);
    const chat=preview.chats[0];
    if (!chat || chat.type !== 'group') throw new Error('Expected a discussion group');
    expect(new URL(chat.avatar_url!, window.location.origin).href).toBe(window.location.origin+'/media/poster.jpg');
    expect(new URL(chat.anime_poster!, window.location.origin).href).toBe(window.location.origin+'/media/poster.jpg');
  } finally { vi.unstubAllEnvs(); }
});
