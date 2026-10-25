import { describe, it, expect } from 'vitest';
import { notificationIcon } from './notificationIcon';
import { ICON_NAMES } from '@/components/icons/SakuraIcon.vue';
describe('legacy notification icon metadata', () => {
  it('maps old backend emoji to an SVG name', () => { expect(notificationIcon('system','⚙️')).toBe('settings'); });
  it('uses the type when metadata is unsupported', () => {
    expect(notificationIcon('comment','unsupported')).toBe('message');
    expect(notificationIcon('new-type','🫠')).toBe('bell');
  });
  it('preserves recognized SVG names', () => { expect(notificationIcon('system','star')).toBe('star'); });
  it('renders every notification settings type with a registered SVG', () => {
    for (const type of ['like','dislike','comment','reply','mention','follow','repost','message','group_message','achievement','contest','contest_vote','contest_results','contest_win','reminder_episode','system','warning','security']) {
      expect(ICON_NAMES, type).toContain(notificationIcon(type));
    }
  });
});
