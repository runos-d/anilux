import { beforeEach, expect, it } from 'vitest';
import { applyChatSummary, clearSummaryRevisions } from './chatSummaryEvents';
beforeEach(clearSummaryRevisions);
it('updates unread totals when an older unread message is deleted', () => {
  const row={unread_count:2,last_message:{id:4,seq:4,version:1}};
  expect(applyChatSummary('key',row,{action:'message_deleted',sequence:9,message_id:2,unread_count:1})).toBe('patched');
  expect(row.unread_count).toBe(1); expect(row.last_message.id).toBe(4);
  expect(applyChatSummary('key',row,{action:'unread_updated',sequence:8,unread_count:2})).toBe('ignored');
});
it('applies an authoritative unread count and message without another read', () => {
  const row={unread_count:0,last_message:undefined as unknown};
  const message={id:2,seq:2,text:'new',created_at:'2026-10-29T12:00:00Z',version:1};
  expect(applyChatSummary('1:group:4',row,{action:'new_message',sequence:8,message,unread_count:3})).toBe('patched');
  expect(row.unread_count).toBe(3); expect(row.last_message).toBe(message);
});
it('keeps a later read count when a new-message event arrives out of order', () => {
  const row={unread_count:1,last_message:{id:1,seq:1,version:1}};
  applyChatSummary('key',row,{action:'unread_updated',sequence:12,unread_count:0});
  applyChatSummary('key',row,{action:'new_message',sequence:11,unread_count:1,message:{id:2,seq:2,version:1}});
  expect(row.unread_count).toBe(0); expect(row.last_message.id).toBe(2);
});
it('does not let a delayed new-message frame overwrite an edited preview', () => {
  const row={unread_count:0,last_message:{id:2,seq:2,version:2,text:'edited'}};
  applyChatSummary('key',row,{action:'new_message',sequence:8,unread_count:1,message:{id:2,seq:2,version:1,text:'old'}});
  expect(row.last_message.text).toBe('edited');
  expect(applyChatSummary('key',row,{action:'message_deleted',message_id:2,sequence:9})).toBe('refresh');
});
it('asks for a snapshot for structural changes and older server events', () => {
  expect(applyChatSummary('key',{}, {action:'chat_updated'})).toBe('refresh');
  expect(applyChatSummary('key',{}, {action:'new_message',message:{id:1}})).toBe('refresh');
});
