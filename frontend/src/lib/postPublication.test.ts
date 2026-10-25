import { beforeEach, describe, expect, it, vi } from 'vitest';

const state = vi.hoisted(() => ({
  get: vi.fn(), post: vi.fn(), put: vi.fn(), upload: vi.fn(), forget: vi.fn(),
  records: new Map<string, unknown>(),
  store: { uploads: [] as { id: string; text: string; progress: number; error?: string }[], upsert: vi.fn((post: unknown) => post) },
}));
vi.mock('@/api/client', () => ({ default: { get: state.get, post: state.post, put: state.put } }));
vi.mock('./postAccount', () => ({ postAccountGuard: () => () => undefined }));
vi.mock('@/stores/posts', () => ({ usePostStore: () => state.store }));
vi.mock('./postDrafts', () => ({
  postDraftGet: async (_store: string, key: string) => state.records.get(key),
  postDraftPut: async (_store: string, key: string, value?: unknown) => {
    if (value === undefined) state.records.delete(key); else state.records.set(key, value);
  },
}));
vi.mock('./postUploads', async importOriginal => ({
  ...await importOriginal<typeof import('./postUploads')>(),
  uploadPostFiles: state.upload, forgetPostUploads: state.forget,
  fileIdentity: async (_owner: string, file: File, index: number) => `${file.name}:${file.size}:${index}`,
}));
import { publishPost, updatePost } from './postPublication';

beforeEach(() => {
  vi.clearAllMocks(); state.records.clear(); state.store.uploads = [];
  state.get.mockResolvedValue({ data: { results: [] } });
  state.post.mockResolvedValue({ data: { id: '8', version: 1 } });
  state.put.mockResolvedValue({ data: { id: '8', version: 2 } });
  state.upload.mockResolvedValue(['upload-1']); state.forget.mockResolvedValue(undefined);
});

describe('shared post submission', () => {
  it('coalesces two simultaneous submissions with the same account and key', async () => {
    const data = new FormData(); data.set('text', 'Once');
    const first = publishPost(4, 'same', data, [], vi.fn());
    const second = publishPost(4, 'same', data, [], vi.fn());
    expect(first).toBe(second);
    await Promise.all([first, second]);
    expect(state.post).toHaveBeenCalledTimes(1);
    expect(state.upload).toHaveBeenCalledTimes(1);
    expect(state.store.uploads).toHaveLength(0);
  });

  it('retries a lost edit response with the original media IDs and edit key', async () => {
    const data = new FormData(); data.set('version', '1');
    const files = [new File(['photo'], 'photo.png')];
    state.put.mockRejectedValueOnce(new Error('Response lost'));
    await expect(updatePost(4, '8', 'retry', data, files, 0, vi.fn())).rejects.toThrow('Response lost');
    expect(state.store.uploads[0]?.error).toBe('Response lost');
    await updatePost(4, '8', 'retry', data, files, 0, vi.fn());
    expect(state.upload).toHaveBeenCalledTimes(1);
    expect(state.put).toHaveBeenCalledTimes(2);
    expect(data.get('media_ids')).toBe('["upload-1"]');
    expect(data.get('client_edit_id')).toBe('retry');
    expect(state.store.uploads).toHaveLength(0);
  });

  it('checks new and retained bytes before attempting an edit', () => {
    expect(() => updatePost(4, '8', 'oversize', new FormData(),
      [new File(['x'], 'photo.png')], 250 * 1024 * 1024, vi.fn())).toThrow('250 МБ');
    expect(state.put).not.toHaveBeenCalled();
    expect(state.upload).not.toHaveBeenCalled();
  });
});
