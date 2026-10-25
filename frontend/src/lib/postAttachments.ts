import type { AnimeCard, FeedPost, MediaFile, PlaylistCard } from '@/api/feed';

function unique<T extends { id: number | string }>(items: (T | null | undefined)[], key = (item: T) => String(item.id)): T[] {
  const seen = new Set<string>();
  return items.filter((item): item is T => {
    if (!item || seen.has(key(item))) return false;
    seen.add(key(item));
    return true;
  });
}

export function postAttachments(post: Partial<Pick<FeedPost, 'anime' | 'playlist' | 'attachments_data' | 'media_files'>>) {
  const attachments = post.attachments_data || [];
  return {
    anime: unique<AnimeCard>([post.anime, ...attachments.filter(row => row.content_type === 'anime').map(row => row.anime_data)]),
    playlists: unique<PlaylistCard>([post.playlist, ...attachments.filter(row => row.content_type === 'playlist').map(row => row.playlist_data)],
      item => /^\d{1,8}$/.test(String(item.id)) ? String(item.id).padStart(8, '0') : String(item.id)),
    media: unique<MediaFile>(post.media_files || []),
  };
}

export function processingPercent(post: Pick<FeedPost, 'media_files' | 'processing_media'>): number {
  const files = post.processing_media?.length ? post.processing_media : post.media_files;
  if (!files?.length) return 0;
  const total = files.reduce((sum, file) => sum + Math.max(1, file.file_size || 0), 0);
  const done = files.reduce((sum, file) => sum + Math.max(1, file.file_size || 0) *
    (file.processing_state === 'ready' ? 100 : Math.max(0, Math.min(99, file.processing_progress || 0))), 0);
  return Math.round(done / total);
}
