<template>
  <div class="chat-list">
    <div class="chat-list-search">
      <div class="search-row">
        <button
          class="archive-toggle"
          type="button"
          :class="{ active: showArchived }"
          :aria-pressed="showArchived"
          :title="showArchived ? 'Показать все чаты' : 'Открыть архив'"
          :aria-label="showArchived ? 'Показать все чаты' : 'Открыть архив'"
          @click="showArchived = !showArchived"
        >
          <SakuraIcon :name="showArchived ? 'chat' : 'package'" :size="16" />
        </button>
        <div class="search-field">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.3-4.3" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск..."
            class="search-input"
          />
          <button
            v-if="searchQuery"
            class="search-clear"
            type="button"
            aria-label="Очистить поиск"
            @click="searchQuery = ''"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
        <button
          v-if="chatMode !== 'support'"
          class="new-chat-btn"
          type="button"
          title="Новый чат"
          aria-label="Новый чат"
          @click="showNewChat = true"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </button>
      </div>
    </div>

    <p v-if="listError" role="alert">{{ listError }}</p>
    <div
      ref="chatListContent"
      class="chat-list-content"
    >
        <div v-if="displayPinnedChats.length > 0" class="mb-3">
          <!-- <div class="pinned-section-label">
            <SakuraIcon name="pin" :size="13" />
            Закрепленные чаты
          </div> -->
          <div class="space-y-1">
            <ChatListItem
              v-for="chat in displayPinnedChats"
              :key="chat.type + '_' + chat.id"
              :chat="chat"
              :is-active="isActiveChat(chat)"
              @click="selectChat(chat)"
              @contextmenu="showContextMenu($event, chat)"
            />
          </div>
        </div>

        <div v-if="displayChats.length > 0" class="mb-3">
          <div class="space-y-1">
            <ChatListItem
              v-for="chat in displayChats"
              :key="chat.type + '_' + chat.id"
              :chat="chat"
              :is-active="isActiveChat(chat)"
              @click="selectChat(chat)"
              @contextmenu="showContextMenu($event, chat)"
            />
          </div>
        </div>

        <div
          v-if="
            displayChats.length === 0 && displayPinnedChats.length === 0
          "
          class="empty-state"
        >
          <SakuraIcon name="chat" :size="44" class="empty-state-icon" />
          <p>
            {{ searchQuery ? "Чаты не найдены" : showArchived ? "В архиве пока нет чатов" : "Пока нет чатов" }}
          </p>
        </div>
    </div>

    <ContextMenu
      :is-open="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      @close="contextMenu.visible = false"
    >
      <template
        v-for="(item, index) in contextMenuItems"
        :key="item.id || index"
      >
        <button
          v-if="item.type !== 'divider'"
          type="button"
          :class="['context-menu-item', { danger: item.danger }]"
          @click="handleContextAction(item.action)"
        >
          <span>{{ item.label }}</span>
        </button>
        <div v-else class="context-menu-divider"></div>
      </template>
    </ContextMenu>

    <NewChatModal
      :show="showNewChat"
      @close="showNewChat = false"
      @created="handleChatCreated"
    />

    <MuteChatModal
      v-if="showMuteModal"
      @close="showMuteModal = false"
      @muted="handleMuteDuration"
    />

    <GlobalChatStyleModal
      v-if="showGlobalStyle"
      @close="showGlobalStyle = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import ChatListItem from "./ChatListItem.vue";
import ContextMenu from "./ContextMenu.vue";
import MuteChatModal from "./MuteChatModal.vue";
import GlobalChatStyleModal from "./GlobalChatStyleModal.vue";
import NewChatModal from "@/components/modal/chats/NewChatModalReal.vue";
import { usePrivateChatStore } from "@/stores/privateChat";
import { useAuthStore } from "@/stores/auth";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { useChatFoldersStore } from "@/stores/chatFolders";
import { chatFoldersApi } from "@/api/chatFolders";
import { useAvatar } from "@/composables/useAvatar";
import { useOnlineStatus } from "@/composables/useOnlineStatus";
import apiClient from "@/api/client";
import { useGroupChatStore } from "@/stores/groupChat";
import type { GroupChat } from "@/stores/groupChat";

interface GroupChatData {
  id: number;
  public_id?: number;
  name: string;
  avatar_url?: string | null;
  anime_poster?: string | null;
  anime_title?: string | null;
  anime_id?: number | null;
  anime_slug?: string | null;
  franchise_id?: number | null;
  franchise_slug?: string | null;
  discussion_type?: string | null;
  last_message?: {
    text?: string;
    created_at?: string;
    sender?: { username?: string };
  } | null;
  unread_count?: number;
  members_count?: number;
  online_count?: number;
  user_member_settings?: {
    is_pinned?: boolean;
    is_archived?: boolean;
    is_muted?: boolean;
    muted_until?: string | null;
  };
}

interface ContextMenuItem {
  id?: string;
  type?: string;
  label?: string;
  icon?: string;
  action?: string;
  danger?: boolean;
}

export type LocalChat = {
  id: number;
  public_id?: number;
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
  is_support?: boolean;
};

const emit = defineEmits<{
  chatSelected: [chat: LocalChat];
}>();

const props = withDefaults(defineProps<{
  activeChatId?: number | null;
  activeFranchiseId?: number | null;
  activeChatType?: "private" | "group" | null;
  chatMode?: "all" | "regular" | "support";
}>(), {
  chatMode: "all",
});

const privateChatStore = usePrivateChatStore();
const groupChatStore = useGroupChatStore();
const authStore = useAuthStore();
const chatExtrasStore = useChatExtrasStore();
const chatFoldersStore = useChatFoldersStore();
const { getAvatarUrl } = useAvatar();

const showNewChat = ref(false);
const showMuteModal = ref(false);
const showGlobalStyle = ref(false);
let pendingMuteChat: LocalChat | null = null;
const searchQuery = ref("");
const showArchived = ref(false);
const listError = ref('');
const folderChats = ref<GroupChatData[]>([]);
const searchChats = ref<GroupChatData[]>([]);
let searchTimer: ReturnType<typeof setTimeout> | undefined;
let searchController: AbortController | undefined;
let searchGeneration = 0;
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  chat: null as LocalChat | null,
});


const chatListContent = ref<HTMLElement | null>(null);
const { isUserOnline } = useOnlineStatus();

const allChats = computed((): LocalChat[] => {
  const chats: LocalChat[] = [];

  privateChatStore.chats.forEach((privateChat) => {
    if (props.chatMode === "support" && !privateChat.is_support) return;
    if (props.chatMode === "regular" && privateChat.is_support) return;
    let otherUserData: Record<string, unknown> | null = null;
    const currentUserId = authStore.user?.id;

    if (currentUserId) {
      if (privateChat.user1?.id === currentUserId) {
        otherUserData = privateChat.user2;
      } else if (privateChat.user2?.id === currentUserId) {
        otherUserData = privateChat.user1;
      }
    }
    otherUserData ||= privateChat.other_user || null;

    const userData = otherUserData as {
      id: number;
      username: string;
      avatar?: string;
      avatar_url?: string;
      display_name?: string;
      first_name?: string;
      last_name?: string;
      is_online?: boolean;
    };
    let chatName = privateChat.name || privateChat.other_user?.display_name || privateChat.other_user?.username || "Чат";

    if (userData && !privateChat.name) {
      chatName =
        userData?.display_name ||
        userData?.username ||
        (userData?.first_name
          ? `${userData.first_name} ${userData.last_name}`.trim()
          : "") ||
        chatName;
    }

    const isUser1 = currentUserId ? (typeof privateChat.user1 === 'number' ? privateChat.user1 : privateChat.user1?.id) === currentUserId : null;
    const settings = privateChat.user_settings || (isUser1 === null
      ? { notifications: false, muted_until: null as string | null, archived: false, pinned: false, blocked: false }
      : {
          notifications: isUser1 ? privateChat.user1_notifications : privateChat.user2_notifications,
          muted_until: isUser1 ? privateChat.user1_muted_until : privateChat.user2_muted_until,
          archived: isUser1 ? privateChat.user1_archived : privateChat.user2_archived,
          pinned: isUser1 ? privateChat.user1_pinned : privateChat.user2_pinned,
          blocked: isUser1 ? privateChat.user1_blocked : privateChat.user2_blocked,
        });

    chats.push({
      id: privateChat.id,
      type: "private",
      name: chatName.trim(),
      avatar: getAvatarUrl(userData?.avatar_url || userData?.avatar, userData?.id),
      lastMessage: (privateChat as { last_message?: string }).last_message
        ? {
            text: (privateChat as { last_message: { text: string } }).last_message.text,
            timestamp: (privateChat as { last_message: { created_at: string } }).last_message.created_at,
            sender: (privateChat as { last_message: { sender?: { username?: string } } }).last_message.sender?.username || "",
          }
        : undefined,
      unreadCount: (privateChat as { unread_count?: number }).unread_count || 0,
      isPinned: settings.pinned,
      isArchived: settings.archived,
      isMuted: settings.notifications === false || (!!settings.muted_until && new Date(settings.muted_until).getTime() > Date.now()),
      status: userData?.id && isUserOnline(userData.id) ? "online" : "offline",
      is_support: privateChat.is_support,
    });
  });
  
  if (props.chatMode === "support") return chats;

  const groups = new Map(
    [...groupChatStore.allGroupChats, ...searchChats.value]
      .filter(chat => !groupChatStore.isGroupChatDismissed(chat.id) && !groupChatStore.isGroupChatDismissed(chat.public_id))
      .map(chat => [String(chat.id), chat]),
  );
  groups.forEach((groupChat) => {
    const animePoster = groupChat.anime_poster;
    const hasAnimePoster =
      animePoster &&
      typeof animePoster === "string" &&
      animePoster.trim() !== "";
    const displayAvatar = hasAnimePoster
      ? animePoster
      : groupChat.avatar_url || undefined;
    const displayName = groupChat.anime_title || groupChat.name;

    chats.push({
      id: groupChat.id,
      type: "group",
      name: displayName,
      avatar: displayAvatar,
      avatar_url: displayAvatar,
      anime_id: groupChat.anime_id || null,
      anime_title: groupChat.anime_title || null,
      anime_poster: animePoster || null,
      anime_slug: groupChat.anime_slug || null,
      franchise_id: groupChat.franchise_id || null,
      franchise_slug: groupChat.franchise_slug || null,
      discussion_type: groupChat.discussion_type || null,
      lastMessage: groupChat.last_message
        ? {
            text: groupChat.last_message.text || "",
            timestamp: groupChat.last_message.created_at || "",
            sender: groupChat.last_message.sender?.username || "",
          }
        : undefined,
      unreadCount: groupChat.unread_count || 0,
      isPinned: groupChat.user_member_settings?.is_pinned || false,
      isArchived: groupChat.user_member_settings?.is_archived || false,
      isMuted: groupChat.user_member_settings?.is_muted || false,
      membersCount: groupChat.members_count,
      onlineCount: groupChat.online_count,
      public_id: groupChat.public_id || undefined,
    });
  });

  folderChats.value.forEach((folderChat) => {
    if (groupChatStore.isGroupChatDismissed(folderChat.id) || groupChatStore.isGroupChatDismissed(folderChat.public_id)) return;
    if (chats.find((c) => c.id === folderChat.id)) return;
    const animePoster = folderChat.anime_poster;
    const hasAnimePoster =
      animePoster &&
      typeof animePoster === "string" &&
      animePoster.trim() !== "";
    const displayAvatar = hasAnimePoster
      ? animePoster
      : folderChat.avatar_url || undefined;
    const displayName = folderChat.anime_title || folderChat.name;
    chats.push({
      id: folderChat.id,
      type: "group",
      name: displayName,
      avatar: displayAvatar,
      avatar_url: displayAvatar,
      anime_id: folderChat.anime_id || null,
      anime_title: folderChat.anime_title || null,
      anime_poster: animePoster || null,
      anime_slug: folderChat.anime_slug || null,
      franchise_id: folderChat.franchise_id || null,
      franchise_slug: folderChat.franchise_slug || null,
      discussion_type: folderChat.discussion_type || null,
      lastMessage: folderChat.last_message
        ? {
            text: folderChat.last_message.text || "",
            timestamp: folderChat.last_message.created_at || "",
            sender: folderChat.last_message.sender?.username || "",
          }
        : undefined,
      unreadCount: folderChat.unread_count || 0,
      isPinned: false,
      isArchived: false,
      isMuted: false,
      membersCount: folderChat.members_count,
      public_id: folderChat.public_id || undefined,
    });
  });

  return chats;
});

const filteredChats = computed(() => {
  let chats = allChats.value;

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase();
    chats = chats.filter(
      (chat) =>
        chat.name.toLowerCase().includes(query) ||
        (chat.type === 'group' && searchChats.value.some(row => String(row.id) === String(chat.id))) ||
        (chat.lastMessage &&
          chat.lastMessage.text.toLowerCase().includes(query)),
    );
  }

  return chats;
});

const displayChats = computed(() => {
  return filteredChats.value.filter(
    (chat) => !chat.isPinned && chat.isArchived === showArchived.value,
  );
});

const displayPinnedChats = computed(() => {
  return filteredChats.value.filter(
    (chat) => chat.isPinned && chat.isArchived === showArchived.value,
  );
});
const contextMenuItems = computed((): ContextMenuItem[] => {
  if (!contextMenu.value.chat) return [];

  const chat = contextMenu.value.chat;
  return [
    {
      id: "mark-read",
      label: "Отметить как прочитанное",
      icon: "check",
      action: "markRead",
    },
    { type: "divider" },
    { id: 'archive', label: chat.isArchived ? 'Вернуть из архива' : 'Архивировать', action: 'toggleArchive' },
    {
      id: "delete",
      label: chat.type === "group" ? "Выйти из группы" : "Удалить чат",
      icon: "trash",
      action: "delete",
      danger: true,
    },
  ];
});

const isActiveChat = (chat: LocalChat) => {
  if (props.activeChatId == null) return false;
  if (chat.type === "private") {
    return props.activeChatId === chat.id && props.activeChatType !== "group";
  }
  if (chat.type === "group") {
    return props.activeChatId === chat.id && props.activeChatType === "group";
  }
  return false;
};

const selectChat = (chat: LocalChat) => {
  console.log("[ChatList] selectChat called:", chat);
  emit("chatSelected", chat);
};

const showContextMenu = (event: MouseEvent, chat: LocalChat) => {
  event.preventDefault();
  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    chat,
  };
};

const handleContextAction = (action: string | undefined) => {
  if (!action) return; 
  const chat = contextMenu.value.chat;
  if (!chat) return;

  switch (action) {
    case "togglePin":
      togglePin(chat);
      break;
    case "toggleArchive":
      toggleArchive(chat);
      break;
    case "mute":
      muteChat(chat);
      break;
    case "markRead":
      markAsRead(chat);
      break;
    case "delete":
      deleteChat(chat);
      break;
  }

  contextMenu.value.visible = false;
};

const togglePin = async (chat: LocalChat) => {
  try {
    if (chat.type === "private") {
      const settings: Record<string, boolean | undefined> = {};
      if (chat.isPinned) {
        settings.pinned = false;
      } else {
        settings.pinned = true;
        settings.archived = false;
      }
      await privateChatStore.updateSettings(chat.id, settings);
    } else {
      const currentPinned = chat.isPinned;
      await apiClient.put(`/social/group-chats/${chat.id}/member-settings/`, {
        is_pinned: !currentPinned,
      });
      const groupChat = groupChatStore.allGroupChats.find((gc) => gc.id === chat.id);
      if (groupChat && groupChat.user_member_settings) {
        groupChat.user_member_settings.is_pinned = !currentPinned;
        if (!currentPinned) {
          groupChat.user_member_settings.is_archived = false;
        }
      }
    }
  } catch (error) {
    console.error("Error toggling pin:", error);
  }
};


const toggleArchive = async (chat: LocalChat) => {
  listError.value = '';
  try {
    if (chat.type === "private") {
      const settings: Record<string, boolean | undefined> = {};
      if (chat.isArchived) {
        settings.archived = false;
      } else {
        settings.archived = true;
        settings.pinned = false;
      }
      await privateChatStore.updateSettings(chat.id, settings);
    } else {
      const currentArchived = chat.isArchived;
      await apiClient.post(`/social/group-chats/${chat.id}/archive/`, {
        is_archived: !currentArchived,
      });
      const groupChat = groupChatStore.allGroupChats.find((gc) => gc.id === chat.id);
      if (groupChat && groupChat.user_member_settings) {
        groupChat.user_member_settings.is_archived = !currentArchived;
        if (!currentArchived) {
          groupChat.user_member_settings.is_pinned = false;
        }
      }
    }
  } catch (error) {
    listError.value = 'Не удалось изменить архив. Попробуйте ещё раз.';
    console.error("Error toggling archive:", error);
  }
};


const muteChat = (chat: LocalChat) => {
  pendingMuteChat = chat;
  showMuteModal.value = true;
};

const handleMuteDuration = async (until: string | null) => {
  const chat = pendingMuteChat;
  pendingMuteChat = null;
  if (!chat) return;

  const mutedUntil =
    until ??
    new Date(Date.now() + 100 * 365 * 24 * 60 * 60 * 1000).toISOString();
  try {
    if (chat.type === "private") {
      await privateChatStore.updateSettings(chat.id, {
        muted_until: mutedUntil,
      });
    } else {
      const durationMinutes = until
        ? Math.round((new Date(until).getTime() - Date.now()) / 60000)
        : null;
      await apiClient.post(`/social/group-chats/${chat.id}/mute/`, {
        duration: durationMinutes,
      });
      const groupChat = groupChatStore.allGroupChats.find((gc) => gc.id === chat.id);
      if (groupChat?.user_member_settings) {
        groupChat.user_member_settings.is_muted = true;
        groupChat.user_member_settings.muted_until = mutedUntil;
      }
    }
  } catch (error) {
    console.error("Error muting chat:", error);
  }
};

const markAsRead = async (chat: LocalChat) => {
  try {
    const endpoint =
      chat.type === "private"
        ? `/social/private-chats/${chat.id}/mark_as_read/`
        : `/social/group-chats/${chat.id}/mark_as_read/`;

    await apiClient.post(endpoint);
    await chatExtrasStore.markAsRead(chat.id);
  } catch (error) {
    console.error("Error marking as read:", error);
  }
};

const deleteChat = async (chat: LocalChat) => {
  const confirmMsg =
    chat.type === "group"
      ? "Выйти из этой группы? Это действие нельзя отменить."
      : "Удалить этот чат? Это действие нельзя отменить.";

  if (!confirm(confirmMsg)) return;

  try {
    if (chat.type === "private") {
      await apiClient.delete(`/social/private-chats/${chat.id}/`);
      privateChatStore.chats = privateChatStore.chats.filter((c) => c.id !== chat.id);
    } else {
      await apiClient.post(`/social/group-chats/${chat.id}/leave_group_chat/`);
      groupChatStore.removeGroupChatFromList(chat.id);
    }
    await chatExtrasStore.loadUnreadChats();
  } catch (error) {
    const status = (error as { response?: { status?: number } })?.response?.status;
    if (chat.type === "group" && (status === 404 || status === 410)) {
      groupChatStore.removeGroupChatFromList(chat.id);
      return;
    }
    console.error("Error deleting chat:", error);
    const err = error as {
      response?: { data?: { error?: string } };
      message?: string;
    };
    const errorMsg =
      err?.response?.data?.error ||
      err?.message ||
      "Не удалось выйти из чата";
    alert(`Ошибка: ${errorMsg}`);
  }
};

const handleChatCreated = async (data: { chatId: number; chatType: "private" | "group" }) => {
  await privateChatStore.loadChats();
  await groupChatStore.loadGroupChats();

  const newChat = allChats.value.find((c) => c.id === data.chatId && c.type === data.chatType);
  if (newChat) {
    emit("chatSelected", newChat);
  }
};

const debouncedSearch = () => {
  clearTimeout(searchTimer);
  searchController?.abort();
  searchChats.value = [];
  const current = ++searchGeneration;
  const search = searchQuery.value.trim();
  if (!search) return;
  searchTimer = setTimeout(async () => {
    const controller = searchController = new AbortController();
    try {
      const { data } = await apiClient.get('/social/group-chats/', { params: { search, page_size: 50 }, signal: controller.signal });
      if (current === searchGeneration) searchChats.value = Array.isArray(data) ? data : data.results || [];
    } catch {
      if (!controller.signal.aborted && current === searchGeneration) listError.value = 'Не удалось выполнить поиск обсуждений';
    }
  }, 200);
};
watch(() => authStore.user?.id, () => { searchQuery.value = ''; debouncedSearch(); });

watch(
  () => props.activeChatId,
  async (newId) => {
    if (!newId) return;
    const inPrivate = privateChatStore.chats.some((c) => c.id === newId);
    const inGroup = groupChatStore.allGroupChats.some((c) => c.id === newId);
    if (inPrivate || inGroup) return;
    try {
      const res = await apiClient.get(`/social/chats/${newId}/`);
      const chat = res.data || res.data?.results || res;
      if (chat && chat.id && !groupChatStore.allGroupChats.some(c => c.id === chat.id)) {
        groupChatStore.allGroupChats.push(chat as GroupChat);
      }
    } catch {
    }
  },
  { immediate: true },
);

watch(searchQuery, () => {
  debouncedSearch();
});

onMounted(async () => {
  try {
    await chatExtrasStore.loadUnreadChats();
    try {
      const preview = await chatFoldersApi.getPreview(-4);
      if (preview?.chats && Array.isArray(preview.chats)) {
        folderChats.value = preview.chats as GroupChatData[];
      }
    } catch (_) {}
  } catch (error) {
    console.error("Error initializing chat list extras:", error);
  }
});

const handleGroupChatsUpdated = (event: CustomEvent) => {
  console.log("Group chats updated via event", event.detail);
};
const refreshSettings = () => { void Promise.all([privateChatStore.loadChats(), groupChatStore.loadGroupChats()]).catch(() => { listError.value = 'Не удалось обновить список чатов'; }); };

onMounted(() => {
  window.addEventListener('chat-settings-updated', refreshSettings);
  window.addEventListener("groupChatsUpdated", handleGroupChatsUpdated as EventListener);
});

onUnmounted(() => {
  clearTimeout(searchTimer);
  searchController?.abort();
  searchGeneration++;
  window.removeEventListener('chat-settings-updated', refreshSettings);
  window.removeEventListener("groupChatsUpdated", handleGroupChatsUpdated as EventListener);
});

</script>

<style scoped>
.chat-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: transparent;
  min-height: 0;
}

.chat-list-search {
  padding: 0.5rem 0.75rem;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.search-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.archive-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: var(--surface-3);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.archive-toggle:hover,
.archive-toggle.active {
  border-color: var(--accent);
  background: var(--accent-subtle);
  color: var(--accent);
}

.search-field {
  position: relative;
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.search-icon {
  position: absolute;
  left: 0.75rem;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 0.55rem 2rem 0.55rem 2.25rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 0.875rem;
  outline: none;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.search-input::placeholder {
  color: var(--text-tertiary);
}

.search-clear {
  position: absolute;
  right: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  min-width: 22px;
  min-height: 22px; 
  flex-shrink: 0;
  border: none;
  border-radius: 50%;
  background: var(--surface-4);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
  box-sizing: border-box;
}

.search-clear:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  padding: 0;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-full);
  background: var(--surface-3);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
  color: var(--accent);
}

.chat-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.pinned-section-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.75rem;
  margin-bottom: 0.25rem;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-tertiary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 2rem;
  text-align: center;
  color: var(--text-tertiary);
}

.empty-state-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 0.75rem;
  color: var(--accent);
  opacity: 0.6;
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}
</style>
