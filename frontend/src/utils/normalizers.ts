import { getActivePinia } from 'pinia';
import { usePostStore } from '@/stores/posts';
import type { FeedPost } from '@/api/feed';
export function normalizePost<T = Record<string, unknown>>(raw: unknown): T {
  const post = (raw || {}) as FeedPost;
  return (getActivePinia() && post.id ? usePostStore().upsert(post) : post) as T;
}

export function normalizeComment(raw: unknown): Record<string, unknown> {
  return (raw || {}) as Record<string, unknown>
}

export function normalizeMessage(raw: unknown): Record<string, unknown> {
  return (raw || {}) as Record<string, unknown>
}

export function formatDuration(minutes?: number | null): string {
  if (!minutes || minutes <= 0) return "0 мин";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours === 0) return `${mins} мин`;
  if (mins === 0) return `${hours} ч`;
  return `${hours} ч ${mins} мин`;
}
