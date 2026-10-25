import { beforeEach, describe, expect, it, vi } from 'vitest';
import apiClient from '@/api/client';
import { joinOpenedDiscussion } from './discussionMembership';

vi.mock('@/api/client', () => ({ default: { post: vi.fn() } }));
const post = vi.mocked(apiClient.post);
const signal = new AbortController().signal;
const discussion = { id: 123, type: 'group', is_public: true, discussion_type: 'anime', anime_id: 515, user_role: null };

describe('opening a discussion', () => {
  beforeEach(() => post.mockReset());

  it('joins an anime discussion before exposing the chat and its settings', async () => {
    post.mockResolvedValue({ data: { id: 123, members_count: 2, user_role: { is_admin: false } } });
    const result = await joinOpenedDiscussion(discussion, signal);
    expect(post).toHaveBeenCalledWith('/social/anime/515/discussion-group/join/', {}, { signal });
    expect(result).toMatchObject({ type: 'group', members_count: 2, user_role: { is_admin: false } });
  });

  it('joins a franchise discussion through its own endpoint', async () => {
    post.mockResolvedValue({ data: { id: 123, members_count: 2 } });
    await joinOpenedDiscussion({ ...discussion, discussion_type: 'franchise', franchise_id: 70 }, signal);
    expect(post).toHaveBeenCalledWith('/social/franchise/70/discussion/join/', {}, { signal });
  });

  it('keeps existing membership, private chats and ordinary groups unchanged', async () => {
    for (const detail of [
      { ...discussion, user_role: { is_admin: false } },
      { ...discussion, is_public: false }, { ...discussion, type: 'private' },
      { ...discussion, discussion_type: '' },
    ]) expect(await joinOpenedDiscussion(detail, signal)).toBe(detail);
    expect(post).not.toHaveBeenCalled();
  });

  it('does not expose a nonmember chat when joining is denied or the discussion changed', async () => {
    post.mockRejectedValueOnce(new Error('403'));
    await expect(joinOpenedDiscussion(discussion, signal)).rejects.toThrow('403');
    post.mockResolvedValue({ data: { id: 456 } });
    await expect(joinOpenedDiscussion(discussion, signal)).rejects.toThrow('Обсуждение изменилось');
  });
});
