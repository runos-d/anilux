import { describe, it, expect } from 'vitest';
import type { AnimeCard, PlaylistCard, MediaFile } from '@/api/feed';
import { postAttachments, processingPercent } from './postAttachments';

describe('canonical post attachments', () => {
  it('deduplicates the primary playlist and repeated attachment aliases, including string IDs', () => {
    const playlist = { id: 21, title: 'Favorites' } as PlaylistCard;
    const anime = { id: 7, title_ru: 'One Piece' } as AnimeCard;
    const legacyPlaylist = JSON.parse('{"id":"21","title":"Favorites"}') as PlaylistCard;
    const result = postAttachments({ playlist, anime, attachments_data: [
      { id: '1', object_id: 21, content_type: 'playlist', playlist_data: legacyPlaylist },
      { id: '2', object_id: 21, content_type: 'playlist', playlist_data: playlist },
      { id: '3', object_id: 7, content_type: 'anime', anime_data: anime },
    ] });
    expect(result.playlists).toEqual([playlist]);
    expect(result.anime).toEqual([anime]);
    expect(postAttachments({ playlist }).playlists).toEqual([playlist]);
    expect(postAttachments({ playlist, attachments_data: [
      { id: '4', object_id: 21, content_type: 'playlist', playlist_data: JSON.parse('{"id":"00000021"}') as PlaylistCard },
    ] }).playlists).toEqual([playlist]);
  });

  it('uses actual preparation progress and accounts for all retained replacement files', () => {
    const media = (id: string, state: MediaFile['processing_state'], progress: number, size: number) =>
      ({ id, processing_state: state, processing_progress: progress, file_size: size }) as MediaFile;
    expect(processingPercent({ media_files: [media('old', 'ready', 100, 1)], processing_media: [
      media('new', 'processing', 40, 3), media('other', 'ready', 0, 1),
    ] })).toBe(55);
    expect(processingPercent({ media_files: [media('a', 'queued', 0, 10)] })).toBe(0);
    expect(processingPercent({ media_files: [media('a', 'ready', 0, 10)] })).toBe(100);
  });
});
