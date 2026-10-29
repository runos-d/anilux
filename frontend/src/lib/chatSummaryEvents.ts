type Summary = { unread_count?: number; last_message?: unknown; last_message_at?: string | null };
const unreadRevisions = new Map<string, number>();
export function clearSummaryRevisions() { unreadRevisions.clear(); }

/** The event already contains the viewer-specific projection made by the server. */
export function applyChatSummary(key: string, row: Summary, event: Record<string, unknown>, viewer?: number): 'patched' | 'ignored' | 'refresh' {
  const sequence = typeof event.sequence === 'number' ? event.sequence : 0;
  const revision = unreadRevisions.get(key) || 0;
  const message = event.message as Record<string, unknown> | undefined;
  const previous = row.last_message as Record<string, unknown> | null | undefined;
  let changed = false;
  if (event.action === 'new_message') {
    if (!message || typeof event.unread_count !== 'number') return 'refresh';
    const same = previous?.id === message.id;
    const later = !previous || (typeof message.seq === 'number' && typeof previous.seq === 'number'
      ? message.seq > previous.seq : Date.parse(String(message.created_at)) > Date.parse(String(previous.created_at)));
    if (later || (same && Number(message.version || 0) >= Number(previous?.version || 0))) {
      row.last_message = message; row.last_message_at = String(message.created_at || ''); changed = true;
    }
    if (!sequence || sequence > revision) { row.unread_count = event.unread_count; changed = true; }
  } else if (event.action === 'unread_updated') {
    if (typeof event.unread_count !== 'number') return 'refresh';
    if (sequence && sequence <= revision) return 'ignored';
    row.unread_count = event.unread_count; changed = true;
  } else if (event.action === 'message_edited') {
    if (!message) return 'refresh';
    if (previous && previous.id === message.id && Number(message.version || 0) >= Number(previous.version || 0)) { row.last_message = message; changed = true; }
  } else if (event.action === 'message_deleted') {
    if (!previous?.id || previous.id === event.message_id) return 'refresh';
    if (typeof event.unread_count !== 'number') return 'refresh';
    if (!sequence || sequence > revision) { row.unread_count = event.unread_count; changed = true; }
  } else if (event.action === 'messages_read') {
    if (previous && event.user_id !== viewer && Array.isArray(event.message_ids) && event.message_ids.includes(previous.id)) {
      row.last_message = { ...previous, is_read_by_other:true }; changed = true;
    }
  } else return 'refresh';
  if (sequence > revision && ['new_message','unread_updated','message_deleted'].includes(String(event.action))) {
    unreadRevisions.set(key, sequence);
    if (unreadRevisions.size > 1000) unreadRevisions.delete(unreadRevisions.keys().next().value!);
  }
  return changed ? 'patched' : 'ignored';
}
