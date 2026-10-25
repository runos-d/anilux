/** API responses and legacy private chat files must never enter runtime caches. */
export function isPrivateCachePath(path: string): boolean {
  try { path = decodeURIComponent(path); } catch { /* malformed URLs remain unchanged */ }
  return /^\/api(?:\/|$)/.test(path) ||
    /^\/(?:data\/)?media\/(?:attachments|message_media|scheduled_messages|chat_backups|posts)(?:\/|$)/.test(path);
}
