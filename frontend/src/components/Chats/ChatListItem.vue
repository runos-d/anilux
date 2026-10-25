<template>
  <div
    class="chat-list-item"
    :class="{ active: isActive }"
    @click="$emit('click')"
    @contextmenu="$emit('contextmenu', $event)"
  >
    <div class="chat-item-content">
      <div class="chat-avatar-wrap">
        <UserAvatar
          :src="displayAvatar"
          :alt="chat.name"
          size="md"
          class="chat-avatar"
        />
        <span
          v-if="chat.type === 'private'"
          class="status-dot"
          :class="statusClass"
        ></span>
      </div>

      <div class="chat-item-body">
        <div class="chat-item-top">
          <h3 class="chat-item-name">
            <span class="chat-item-title">{{ chat.name }}</span>
            <SakuraIcon
              v-if="chat.isPinned"
              name="star"
              :size="13"
              class="pin-icon"
            />
          </h3>
          <span class="chat-item-time">{{
            formatTime(chat.lastMessage?.timestamp)
          }}</span>
        </div>

        <div class="chat-item-bottom">
          <p class="chat-item-preview">
            <span v-if="groupSender && !isTyping" class="preview-sender">{{
              groupSender
            }}</span>
            <span class="preview-text">{{
              formatLastMessage(chat.lastMessage)
            }}</span>
          </p>

          <span
            v-if="chat.type === 'group' && chat.membersCount"
            class="members-count"
          >
            <SakuraIcon name="users" :size="12" />
            {{ chat.membersCount }}
          </span>

          <span
            v-if="chat.isMuted"
            class="muted-icon"
            title="Уведомления заглушены"
          >
            <SakuraIcon name="bell-off" :size="13" />
          </span>

          <span
            v-if="chat.unreadCount > 0"
            class="unread-badge"
            :class="{ 'unread-badge--muted': chat.isMuted }"
          >
            {{ chat.unreadCount > 99 ? "99+" : chat.unreadCount }}
          </span>
        </div>
      </div>
      <button class="chat-item-menu" type="button" :aria-label="`Действия чата ${chat.name}`" @click.stop="$emit('contextmenu', $event)">
        <SakuraIcon name="more-horizontal" :size="18" />
      </button>
    </div>

    <div v-if="isTyping" class="typing-indicator-block">
      <span class="typing-dot"></span>
      <span class="typing-dot typing-dot--2"></span>
      <span class="typing-dot typing-dot--3"></span>
      <span class="typing-label">печатает...</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import UserAvatar from '@/components/ui/UserAvatar.vue';
import { getMediaUrl } from "@/api/client";

interface Chat {
  id: number;
  type: "private" | "group";
  name: string;
  avatar?: string | null;
  avatar_url?: string | null;
  anime_id?: number | null;
  anime_title?: string | null;
  anime_poster?: string | null;
  anime_slug?: string | null;
  franchise_id?: number | null;
  franchise_slug?: string | null;
  discussion_type?: string | null;
  lastMessage?: {
    text: string;
    timestamp: string;
    sender: string;
  };
  unreadCount: number;
  isPinned: boolean;
  isArchived: boolean;
  isMuted: boolean;
  status?: string;
  membersCount?: number;
  onlineCount?: number;
}

interface Props {
  chat: Chat;
  isActive?: boolean;
  isTyping?: boolean;
}

const props = defineProps<Props>();

defineEmits<{
  click: [];
  contextmenu: [event: MouseEvent];
}>();

const displayAvatar = computed(() => {
  const isFranchiseDiscussion = props.chat.franchise_id || props.chat.discussion_type === "franchise";
  if (props.chat.anime_id || props.chat.anime_title || isFranchiseDiscussion) {
    const animePoster = props.chat.anime_poster;
    if (
      animePoster &&
      typeof animePoster === "string" &&
      animePoster.trim() !== ""
    ) {
      return getMediaUrl(animePoster);
    }
    const avatarUrl = props.chat.avatar_url;
    if (avatarUrl && typeof avatarUrl === "string" && avatarUrl.trim() !== "") {
      return getMediaUrl(avatarUrl);
    }
  }

  const avatar = props.chat.avatar || props.chat.avatar_url;
  if (avatar && typeof avatar === "string" && avatar.trim() !== "") {
    return getMediaUrl(avatar);
  }
  return "/default-avatar.png";
});

const statusClass = computed(() => {
  switch (props.chat.status) {
    case "online":
      return "status-dot--online";
    case "away":
      return "status-dot--away";
    case "busy":
      return "status-dot--busy";
    default:
      return "status-dot--offline";
  }
});

const groupSender = computed(() => {
  if (props.chat.type !== "group") return "";
  return props.chat.lastMessage?.sender || "";
});

const formatTime = (timestamp?: string) => {
  if (!timestamp) return "";

  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  if (diff < 60000) {
    return "сейчас";
  }

  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000);
    return `${minutes} мин`;
  }

  if (diff < 86400000) {
    return date.toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return date.toLocaleDateString("ru-RU", { month: "short", day: "numeric" });
};

const formatLastMessage = (lastMessage?: Chat["lastMessage"]) => {
  if (!lastMessage) return "Нет сообщений";

  const text = lastMessage.text || "";
  if (!text.trim()) return "Нет сообщений";

  return text;
};
</script>

<style scoped>
.chat-item-menu { flex-shrink: 0; width: 40px; height: 40px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border: 0; border-radius: var(--radius-md); background: transparent; color: var(--text-secondary); cursor: pointer; }
.chat-item-menu:hover, .chat-item-menu:focus-visible { background: rgb(from var(--accent) r g b / 0.4); color: var(--text-primary); }
.chat-list-item {
  position: relative;
  border-radius: var(--radius-lg);
  background: transparent;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}

.chat-item-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  border-radius: inherit;
  transition: background var(--duration-base) var(--ease-petal);
}

.chat-list-item:hover .chat-item-content {
  background: var(--surface-4);
}

.chat-list-item.active .chat-item-content {
  background: linear-gradient(
    135deg,
    var(--accent) 0%,
    var(--accent-press) 100%
  );
  box-shadow: var(--shadow-sm-petal-sm);
}

.chat-list-item.active::before {
  content: "";
  position: absolute;
  left: 0;
  top: 25%;
  bottom: 25%;
  width: 3px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: linear-gradient(180deg, var(--accent), var(--accent-press));
}

.chat-avatar-wrap {
  position: relative;
  flex-shrink: 0;
  align-self: flex-start;
  margin-top: 0.15rem;
}

.chat-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  object-fit: cover;
  background: var(--surface-4);
  border: 2px solid var(--border-default);
  transition: all var(--duration-base) var(--ease-petal);
}

.chat-list-item.active .chat-avatar {
  border-color: rgba(255, 255, 255, 0.35);
}

.chat-list-item:hover .chat-avatar {
  border-color: var(--accent-subtle);
}

.status-dot {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--surface-2);
}

.status-dot--online {
  background: var(--success);
  box-shadow: 0 0 0px var(--success);
}

.status-dot--away {
  background: var(--warning);
}

.status-dot--busy {
  background: var(--danger);
}

.status-dot--offline {
  background: var(--text-tertiary);
}

.chat-item-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.chat-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.chat-item-name {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  font-weight: 600;
  font-size: 0.9375rem;
  color: var(--text-primary);
}

.chat-item-title {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-list-item.active .chat-item-name {
  color: var(--text-on-accent);
}

.pin-icon {
  color: var(--accent);
  flex-shrink: 0;
}

.chat-list-item.active .pin-icon {
  color: rgba(255, 255, 255, 0.9);
}

.chat-item-time {
  flex-shrink: 0;
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-tertiary);
}

.chat-list-item.active .chat-item-time {
  color: rgba(255, 255, 255, 0.75);
}

.chat-item-bottom {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  min-width: 0;
}

.chat-item-preview {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  min-width: 0;
  flex: 1;
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.35;
  color: var(--text-secondary);
}

.preview-sender {
  flex-shrink: 1;
  color: var(--accent);
  font-weight: 500;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  max-width: 40%;
}

.preview-text {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chat-list-item.active .chat-item-preview,
.chat-list-item.active .preview-text {
  color: rgba(255, 255, 255, 0.85);
}

.chat-list-item.active .preview-sender {
  color: rgba(255, 255, 255, 0.95);
}

.members-count {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  flex-shrink: 0;
  font-size: 0.6875rem;
  color: var(--text-tertiary);
}

.chat-list-item.active .members-count {
  color: rgba(255, 255, 255, 0.75);
}

.muted-icon {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.chat-list-item.active .muted-icon {
  color: rgba(255, 255, 255, 0.8);
}

.unread-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  flex-shrink: 0;
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  color: var(--text-on-accent);
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm-petal-sm);
}

.unread-badge--muted {
  background: var(--surface-5);
  color: var(--text-tertiary);
  box-shadow: none;
}

.chat-list-item.active .unread-badge {
  background: rgba(255, 255, 255, 0.92);
  color: var(--accent-press);
  box-shadow: none;
}

.typing-indicator-block {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 0.15rem 0.75rem 0.6rem;
  color: var(--text-tertiary);
}

.typing-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  animation: typing-bounce 1.2s var(--ease-petal) infinite;
}

.typing-dot--2 {
  animation-delay: 0.15s;
}

.typing-dot--3 {
  animation-delay: 0.3s;
}

.typing-label {
  margin-left: 0.35rem;
  font-size: 0.75rem;
  font-weight: 500;
  font-style: italic;
}

@keyframes typing-bounce {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}
</style>
