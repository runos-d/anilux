import { ICON_NAMES } from '@/components/icons/SakuraIcon.vue';
import { getIconName } from '@/utils/emojiToIcon';

const names = new Set(ICON_NAMES);
const icons: Record<string, string> = {
  like: 'thumbs-up', dislike: 'thumbs-down', heart: 'heart', comment: 'message',
  reply: 'reply', mention: 'at-sign', follow: 'users', repost: 'refresh',
  message: 'mail', group_message: 'users', group_invite: 'inbox', achievement: 'trophy',
  contest: 'medal', contest_vote: 'ballot-box', contest_results: 'chart', contest_win: 'crown',
  reminder_episode: 'clock', reminder_event: 'calendar', reminder_contest: 'hourglass',
  reminder: 'clock', system: 'settings', warning: 'warning', security: 'lock',
};

/** Legacy API emoji metadata becomes an SVG name; notification content stays intact. */
export function notificationIcon(type?: string, icon?: string): string {
  const candidate = icon && (getIconName(icon) || icon);
  return candidate && names.has(candidate) ? candidate : icons[type || ''] || 'bell';
}
