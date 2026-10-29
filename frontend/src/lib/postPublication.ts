import apiClient from '@/api/client';
import { postAccountGuard } from './postAccount';
import { uploadPostFiles, forgetPostUploads, validatePostFiles, fileIdentity } from './postUploads';
import { postDraftGet, postDraftPut } from './postDrafts';
import { usePostStore } from '@/stores/posts';
import type { FeedPost } from '@/api/feed';
import { event as analyticsEvent } from '@/analytics';

const inFlight = new Map<string, Promise<FeedPost>>();

function mutate(owner: number | string, id: string, text: string, progress: (percent: number) => void,
  send: (ensureAccount: () => void, report: (percent: number) => void) => Promise<FeedPost>): Promise<FeedPost> {
  const key = `${owner}:${id}`;
  const existing = inFlight.get(key);
  if (existing) return existing;
  const ensureAccount = postAccountGuard(owner);
  ensureAccount();
  const store = usePostStore();
  store.uploads = [...store.uploads.filter(row => row.id !== id), { id, text, progress: 0 }];
  const operation = (async () => {
    try {
      const post = await send(ensureAccount, value => {
        ensureAccount();
        const row = store.uploads.find(row => row.id === id);
        if (row) row.progress = value;
        progress(value);
      });
      ensureAccount();
      store.uploads = store.uploads.filter(row => row.id !== id);
      return store.upsert(post);
    } catch (error) {
      const row = store.uploads.find(row => row.id === id);
      if (row) row.error = (error as Error).message || 'Не удалось отправить пост. Черновик сохранён.';
      throw error;
    } finally { inFlight.delete(key); }
  })();
  inFlight.set(key, operation);
  return operation;
}

export function publishPost(owner: number | string, clientId: string, data: FormData,
  files: File[], progress: (percent: number) => void): Promise<FeedPost> {
  validatePostFiles(files);
  return mutate(owner, clientId, String(data.get('text') || 'Публикация'), progress, async (ensureAccount, report) => {
  const previous = await apiClient.get('/social/posts/', { params: { mine: true, client_post_id: clientId }, _keepOnNavigation: true, _accountId: String(owner) });
  ensureAccount();
  let post: FeedPost = (previous.data.results || previous.data)[0];
  if (!post) {
    const ids = await uploadPostFiles(owner, files, report);
    ensureAccount();
    data.set('client_post_id', clientId);
    data.set('media_ids', JSON.stringify(ids));
    post = (await apiClient.post<FeedPost>('/social/posts/', data, { _accountId: String(owner) })).data;
    const mediaKinds = new Set(files.map(file => file.type.startsWith('video/') ? 'video' : 'image'));
    analyticsEvent('post_published', {
      attachment_category: mediaKinds.size > 1 ? 'mixed' : mediaKinds.has('video') ? 'video' : mediaKinds.has('image') ? 'image' : 'none',
    });
  }
  ensureAccount();
  await forgetPostUploads(owner, files).catch(() => undefined);
  await postDraftPut('drafts', `${owner}:create`).catch(() => undefined);
  ensureAccount();
  return post;
  });
}

export function updatePost(owner: number | string, postId: number | string, clientId: string, data: FormData,
  files: File[], retainedBytes: number, progress: (percent: number) => void): Promise<FeedPost> {
  validatePostFiles(files, retainedBytes);
  return mutate(owner, `edit:${postId}:${clientId}`, 'Редактирование поста', progress, async (ensureAccount, report) => {
    const key = `${owner}:edit-send:${postId}:${clientId}`;
    const fingerprints = await Promise.all(files.map((file, index) => fileIdentity(owner, file, index)));
    ensureAccount();
    const previous = await postDraftGet<{ fingerprints: string[]; ids: string[] }>('uploads', key).catch(() => undefined);
    const ids = previous && JSON.stringify(previous.fingerprints) === JSON.stringify(fingerprints)
      ? previous.ids : await uploadPostFiles(owner, files, report);
    ensureAccount();
    await postDraftPut('uploads', key, { fingerprints, ids }).catch(() => undefined);
    data.set('media_ids', JSON.stringify(ids));
    data.set('client_edit_id', clientId);
    const response = await apiClient.put<FeedPost | { post: FeedPost }>(`/social/posts/${postId}/edit/`, data, { _accountId: String(owner) });
    ensureAccount();
    const post = 'post' in response.data ? response.data.post : response.data;
    await forgetPostUploads(owner, files).catch(() => undefined);
    await postDraftPut('uploads', key).catch(() => undefined);
    await postDraftPut('drafts', `${owner}:edit:${postId}`).catch(() => undefined);
    return post;
  });
}
