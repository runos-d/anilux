export interface User {
  id: number;
  username: string;
  display_name?: string;
  avatar?: string;
  avatar_url?: string;
}

export interface Message {
  topic_id?: number | null;
  reactions?: Record<string, number[]>;
  client_message_id?: string | null;
  seq?: number;
  version?: number;
  can_edit?: boolean;
  conversation_id?: number;
  chat_type?: "private" | "group";
  is_deleted?: boolean;
  send_status?: "pending" | "failed" | "sent";
  id: number;
  text: string;
  sender_id: number;
  sender?: User;
  sender_username?: string;
  sender_avatar?: string;
  chat_id: number;
  created_at: string;
  updated_at: string;
  is_read_by_other?: boolean;
  read_count?: number;
  is_read: boolean;
  reply_to?: number;
  reply_to_message?: {
    id: number;
    topic_id?: number | null;
    topic_slug?: string;
    sender_id: number;
    sender_username: string;
    sender_avatar?: string;
    text: string;
    created_at: string;
    media?: string | null;
    media_type?: string | null;
  };
  attachments?: Attachment[];
  media?: string | null;
  media_type?: string | null;
  is_pinned?: boolean;
  is_edited?: boolean;
  pinned_at?: string | null;
  pinned_by_username?: string | null;
  shared_post_data?: {
    id: number;
    author_username: string;
    text?: string;
    image_url?: string | null;
    created_at: string;
  } | null;
  shared_anime_data?: {
    id: number;
    title_ru?: string;
    title_en?: string;
    poster_url?: string | null;
    year?: number | null;
    kind?: string | null;
    episodes?: number | null;
    slug?: string;
  } | null;
  shared_playlist_data?: {
    id: number;
    title: string;
    cover_image?: string | null;
    items_count?: number;
  } | null;
  shared_shorts_data?: {
    id: number;
    title?: string;
    image_url?: string | null;
  } | null;
  location_latitude?: number | null;
  location_longitude?: number | null;
  location_name?: string | null;
  scheduled_at?: string | null;
  is_recurring?: boolean;
  recurring_interval?: number | null;
  [key: string]: unknown;
}

export interface Attachment {
  id: number;
  /** Файловые вложения: image | video | file | audio.
   *  Контентные карточки: anime | playlist | shorts | post */
  type: string;
  object_id?: number;
  data?: {
    id: number;
    title_ru?: string;
    title_en?: string;
    poster_url?: string | null;
    posters?: string[];
    kind?: string | null;
    year?: number | null;
    items_count?: number;
    title?: string;
    description?: string | null;
    text?: string;
    video_url?: string | null;
    thumbnail_url?: string | null;
    anime?: { id: number; title_ru?: string } | null;
    author?: { id: number; username?: string; avatar_url?: string | null } | null;
    likes_count?: number;
    comments_count?: number;
    views_count?: number;
  } | null;
  url?: string;
  file?: string | null;
  file_url?: string | null;
  filename?: string;
  file_name?: string;
  size?: number;
  file_size?: number;
  mime_type?: string;
  thumbnail?: string | null;
  thumbnail_url?: string | null;
}

export interface PrivateChat {
  id: number;
  code?: string;
  type: "private";
  other_user: User;
  last_message?: Message;
  unread_count: number;
  created_at: string;
  updated_at: string;
  is_pinned: boolean;
  is_archived: boolean;
  is_muted: boolean;
  isMuted?: boolean;
}

export interface GroupChatMember {
  id: number;
  user: User;
  role: "owner" | "admin" | "member";
  joined_at: string;
}

export interface MemberSettings {
  is_pinned: boolean;
  is_archived: boolean;
  is_muted: boolean;
  muted_until?: string;
  notifications_enabled: boolean;
}

export interface GroupChat {
  id: number;
  code?: string;
  type: "group";
  name: string;
  description?: string;
  avatar?: string;
  avatar_url?: string;

  anime_id?: number | null;
  anime_title?: string | null;
  anime_poster?: string | null;
  members_count: number;
  members: GroupChatMember[];
  owner: User;
  last_message?: Message;
  unread_count: number;
  created_at: string;
  updated_at: string;
  is_pinned: boolean;
  is_archived: boolean;
  is_public: boolean;
  invite_token?: string;
  user_member_settings?: MemberSettings;
  isMuted?: boolean;
}

export type Chat = PrivateChat | GroupChat;

export interface UnifiedChat {
  id: number;
  type: "private" | "group";
  title: string;
  avatar?: string;
  avatar_url?: string;
  last_message?: Message;
  unread_count: number;
  is_pinned: boolean;
  is_archived: boolean;
  is_muted: boolean;
  updated_at: string;
}

export interface ChatFolderRules {
  include_private: boolean;
  include_groups: boolean;
  include_bots: boolean;
  exclude_keywords: string[];
  include_keywords: string[];
  exclude_user_ids: number[];
  only_unread?: boolean;
  only_pinned?: boolean;
  include_anime_discussions?: boolean;
}

export interface ChatFolder {
  id: number;
  name: string;
  icon: string;
  color?: string;
  position: number;
  is_system: boolean;
  rules: ChatFolderRules;
  created_at: string;
  updated_at: string;
}

export interface CreateFolderData {
  name: string;
  icon: string;
  color?: string;
  rules: Partial<ChatFolderRules>;
}

export interface UpdateFolderData {
  name?: string;
  icon?: string;
  color?: string;
  rules?: Partial<ChatFolderRules>;
}

export interface FolderPreview {
  folder_id: number;
  chat_count: number;
  unread_count: number;
  chats: Chat[];
}

export interface ChatWallpaper {
  id?: string;
  wallpaper_type: "solid" | "gradient" | "pattern" | "image";
  wallpaper_color: string;
  wallpaper_color2?: string;
  gradient_angle?: number;
  pattern_type?: string;
  pattern_color?: string;
  pattern_opacity?: number;
  wallpaper_image?: string;
  wallpaper_blur?: number;
  wallpaper_intensity?: number;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export interface ChatTheme {
  id?: string;
  message_color_mine?: string;
  message_color_other?: string;
  message_text_color_mine?: string;
  message_text_color_other?: string;
  bubble_style?: string;
  bubble_border_radius?: number;
  bubble_shadow?: boolean;
  font_family?: string;
  font_size?: string;
  font_size_px?: number;
  font_weight?: number;
  line_height?: number;
  time_format?: string;
  time_color?: string;
  background_color?: string;
  header_color?: string;
  input_color?: string;
  input_text_color?: string;
  accent_color?: string;
  link_color?: string;
  message_animation?: string;
  reaction_animation?: string;
  typing_animation?: string;
  emoji_set?: string;
  emoji_size?: string;
  show_avatars?: boolean;
  show_usernames?: boolean;
  compact_mode?: boolean;
  show_read_status?: boolean;
  show_typing_indicator?: boolean;
  message_grouping?: boolean;
  custom_css?: string;
  created_at?: string;
  updated_at?: string;
  [key: string]: unknown;
}

export const SYSTEM_FOLDERS: Partial<ChatFolder>[] = [
  {
    id: 0,
    name: "Все чаты",
    icon: "message-circle",
    is_system: true,
    position: 0,
    rules: {
      include_private: true,
      include_groups: true,
      include_bots: true,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: [],
    },
  },
  {
    id: -1,
    name: "Личные",
    icon: "user",
    is_system: true,
    position: 1,
    rules: {
      include_private: true,
      include_groups: false,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: [],
    },
  },
  {
    id: -2,
    name: "Группы",
    icon: "users",
    is_system: true,
    position: 2,
    rules: {
      include_private: false,
      include_groups: true,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: [],
      exclude_user_ids: [],
    },
  },
  {
    id: -4,
    name: "Обсуждения",
    icon: "play",
    is_system: true,
    position: 3,
    rules: {
      include_private: false,
      include_groups: true,
      include_bots: false,
      exclude_keywords: [],
      include_keywords: ["Обсуждение:", "Аниме:"],
      exclude_user_ids: [],
      only_unread: false,
      only_pinned: false,
      include_anime_discussions: true,
    },
  },
];

export const FOLDER_ICONS = [
  "🗯️",
  "👤",
  "👥",
  "📦",
  "🏢",
  "🏠",
  "⭐",
  "❤️",
  "🔥",
  "💡",
  "📌",
  "🎯",
  "🚀",
  "💼",
  "🎮",
  "🎨",
  "📚",
  "🎵",
  "🎬",
  "📷",
  "🏆",
  "🌟",
  "✨",
  "🔔",
  "📊",
  "📈",
  "💰",
  "🎁",
  "🌈",
  "☀️",
  "🌙",
  "⚡",
];

export const FOLDER_COLORS = [
  "#3B82F6",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#8B5CF6",
  "#EC4899",
  "#06B6D4",
  "#84CC16",
  "#6366F1",
  "#F97316",
];
export interface ChatContentCardData {
  id?: number;
  title_ru?: string;
  title_en?: string;
  title?: string;
  poster_url?: string | null;
  posters?: string[];
  kind?: string | null;
  year?: number | null;
  items_count?: number;
  text?: string;
  thumbnail_url?: string | null;
  author?: { username?: string } | null;
  author_username?: string;
  anime?: { title_ru?: string } | null;
}
