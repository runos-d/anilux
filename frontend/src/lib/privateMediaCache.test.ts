import { expect, it } from 'vitest';
import { isPrivateCachePath } from './privateMediaCache';

it('excludes API media and old private public URLs, including encoded paths', () => {
  for (const path of ['/api/social/chat-media/a.png', '/api/users/me/', '/media/attachments/a.png',
    '/data/media/message_media/a.jpg', '/data/media/chat_backups/a.zip', '/media/%61ttachments/a.png', '/media/posts/a.jpg', '/data/media/posts/a.jpg']) {
    expect(isPrivateCachePath(path)).toBe(true);
  }
});

it('keeps public avatars and assets cacheable', () => {
  for (const path of ['/assets/app.js', '/data/media/avatars/a.png']) {
    expect(isPrivateCachePath(path)).toBe(false);
  }
});
