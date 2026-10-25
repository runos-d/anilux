import { describe, expect, it } from 'vitest';
import { chatNotificationsEnabled } from './chatNotificationPreferences';
describe('chat alerts', () => {
  it('excludes muted private chats, groups and discussions', () => {
    expect(chatNotificationsEnabled({ user_settings: { notifications: false } })).toBe(false);
    expect(chatNotificationsEnabled({ user_member_settings: { notifications_enabled: false } })).toBe(false);
    expect(chatNotificationsEnabled({ user_member_settings: { is_muted: true } })).toBe(false);
    expect(chatNotificationsEnabled({ user_settings: { muted_until: new Date(Date.now() + 10000).toISOString() } })).toBe(false);
  });
  it('allows enabled chats and expired mute periods', () => {
    expect(chatNotificationsEnabled({ user_settings: { muted_until: new Date(Date.now() - 10000).toISOString() } })).toBe(true);
    expect(chatNotificationsEnabled({})).toBe(true);
  });
});
