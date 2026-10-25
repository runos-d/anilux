import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
  inviteLinksApi,
  reactionsApi,
  attachmentsApi,
  messageActionsApi,
  unreadApi,
  searchApi,
  type ChatInviteLink,
  type ChatInviteLinkCreate,
  type Reaction,
  type Attachment,
  type UnreadChat,
} from "@/api/chats";
import type { Message } from "@/types/chat";
import type { NotificationItem } from "@/api/notifications";
import apiClient, { isRequestCancelled } from "@/api/client";

export const useChatExtrasStore = defineStore("chatExtras", () => {
  const invites = ref<ChatInviteLink[]>([]);
  const loadingInvites = ref(false);
  const messageReactions = ref<Map<number, Reaction[]>>(new Map());
  const loadingReactions = ref(false);
  const messageAttachments = ref<Map<number, Attachment[]>>(new Map());
  const loadingAttachments = ref(false);
  const pinnedMessages = ref<Message[]>([]);
  const loadingPinned = ref(false);
  const unreadCount = ref(0);
  const unreadChats = ref<UnreadChat[]>([]);
  const loadingUnread = ref(false);
  const searchResults = ref<Array<Record<string, unknown>>>([]);
  const searching = ref(false);
  const unreadChatsLoadingPromise = ref<Promise<unknown> | null>(null);
  const unreadChatsLastLoadedAt = ref<number | null>(null);
  let unreadChatsGeneration = 0;
  const UNREAD_CHATS_DEDUPE_MS = 30000

  const loadInvites = async (chatId?: number) => {
    loadingInvites.value = true;
    try {
      const response = await inviteLinksApi.list(chatId);
      const data = response.data as
        | ChatInviteLink[]
        | { results: ChatInviteLink[] };
      invites.value = Array.isArray(data) ? data : data.results;
    } catch (error) {
      console.error("Error loading invites:", error);
    } finally {
      loadingInvites.value = false;
    }
  };

  const createInvite = async (data: ChatInviteLinkCreate) => {
    try {
      const response = await inviteLinksApi.create(data);
      invites.value.push(response.data);
      return response.data;
    } catch (error) {
      console.error("Error creating invite:", error);
      throw error;
    }
  };

  const deleteInvite = async (inviteId: number) => {
    try {
      await inviteLinksApi.delete(inviteId);
      invites.value = invites.value.filter((i) => i.id !== inviteId);
    } catch (error) {
      console.error("Error deleting invite:", error);
      throw error;
    }
  };

  const regenerateInvite = async (inviteId: number) => {
    try {
      const old = invites.value.find((i) => i.id === inviteId);
      await inviteLinksApi.revoke(inviteId);
      const response = await inviteLinksApi.create({
        chat: old?.chat as number,
        name: old?.name,
      });
      const index = invites.value.findIndex((i) => i.id === inviteId);
      if (index !== -1) {
        invites.value[index] = response.data;
      } else {
        invites.value.push(response.data);
      }
      return response.data;
    } catch (error) {
      console.error("Error regenerating invite:", error);
      throw error;
    }
  };

  const revokeInvite = async (inviteId: number) => {
    try {
      await inviteLinksApi.revoke(inviteId);
      const invite = invites.value.find((i) => i.id === inviteId);
      if (invite) {
        invite.is_revoked = true;
      }
    } catch (error) {
      console.error("Error revoking invite:", error);
      throw error;
    }
  };

  const joinByToken = async (token: string) => {
    try {
      const response = await inviteLinksApi.join(token);
      return response.data;
    } catch (error) {
      console.error("Error joining chat:", error);
      throw error;
    }
  };

  const loadMessageReactions = async (messageId: number) => {
    loadingReactions.value = true;
    try {
      const response = await reactionsApi.getForMessage(messageId);
      messageReactions.value.set(messageId, response.data);
      return response.data;
    } catch (error) {
      console.error("Error loading reactions:", error);
      return [];
    } finally {
      loadingReactions.value = false;
    }
  };

  const toggleReaction = async (messageId: number, emoji: string) => {
    try {
      const response = await reactionsApi.toggle(messageId, emoji);
      await loadMessageReactions(messageId);
      return response.data;
    } catch (error) {
      console.error("Error toggling reaction:", error);
      throw error;
    }
  };

  const getReactionsForMessage = (messageId: number) => {
    return messageReactions.value.get(messageId) || [];
  };

  const hasUserReacted = (messageId: number, emoji: string, userId: number) => {
    const reactions = messageReactions.value.get(messageId) || [];
    return reactions.some((r) => r.emoji === emoji && r.user.id === userId);
  };

  const getReactionCount = (messageId: number, emoji: string) => {
    const reactions = messageReactions.value.get(messageId) || [];
    return reactions.filter((r) => r.emoji === emoji).length;
  };

  const loadMessageAttachments = async (messageId: number) => {
    loadingAttachments.value = true;
    try {
      const response = await attachmentsApi.list(messageId);
      messageAttachments.value.set(messageId, response.data);
      return response.data;
    } catch (error) {
      console.error("Error loading attachments:", error);
      return [];
    } finally {
      loadingAttachments.value = false;
    }
  };

  const uploadAttachment = async (messageId: number, file: File) => {
    try {
      const response = await attachmentsApi.uploadToMessage(messageId, file);
      const attachments = messageAttachments.value.get(messageId) || [];
      messageAttachments.value.set(messageId, [...attachments, response.data]);
      return response.data;
    } catch (error) {
      console.error("Error uploading attachment:", error);
      throw error;
    }
  };

  const deleteAttachment = async (attachmentId: number, messageId: number) => {
    try {
      await attachmentsApi.delete(attachmentId);
      const attachments = messageAttachments.value.get(messageId) || [];
      messageAttachments.value.set(
        messageId,
        attachments.filter((a) => a.id !== attachmentId),
      );
    } catch (error) {
      console.error("Error deleting attachment:", error);
      throw error;
    }
  };

  const getAttachmentsForMessage = (messageId: number) => {
    return messageAttachments.value.get(messageId) || [];
  };

  const loadPinnedMessages = async (chatId: number) => {
    loadingPinned.value = true;
    try {
      const response = await messageActionsApi.getPinned(chatId);
      pinnedMessages.value = response.data.results || response.data;
      return response.data;
    } catch (error) {
      console.error("Error loading pinned messages:", error);
      return [];
    } finally {
      loadingPinned.value = false;
    }
  };

  const pinMessage = async (messageId: number) => {
    try {
      const response = await messageActionsApi.pin(messageId);
      return response.data;
    } catch (error) {
      console.error("Error pinning message:", error);
      throw error;
    }
  };

  const unpinMessage = async (messageId: number) => {
    try {
      const response = await messageActionsApi.unpin(messageId);
      pinnedMessages.value = pinnedMessages.value.filter(
        (m) => m.id !== messageId,
      );
      return response.data;
    } catch (error) {
      console.error("Error unpinning message:", error);
      throw error;
    }
  };

  const loadUnreadCount = async (chatId?: number) => {
    loadingUnread.value = true;
    try {
      const response = await unreadApi.getCount(chatId);
      unreadCount.value = response.data.unread_count;
      return response.data;
    } catch (error) {
      console.error("Error loading unread count:", error);
      return { unread_count: 0 };
    } finally {
      loadingUnread.value = false;
    }
  };

  const loadUnreadChats = async (force = false) => {
    const token = localStorage.getItem('anilux_access_token_v1');
    if (!token) { unreadChats.value = []; return []; }
    const now = Date.now();

    if (!force && unreadChatsLoadingPromise.value) {
      return unreadChatsLoadingPromise.value;
    }

    if (
      !force &&
      unreadChatsLastLoadedAt.value &&
      now - unreadChatsLastLoadedAt.value < UNREAD_CHATS_DEDUPE_MS
    ) {
      return Promise.resolve(unreadChats.value);
    }

    const generation = ++unreadChatsGeneration;
    loadingUnread.value = true;
    unreadChatsLoadingPromise.value = (async () => {
      try {
          const response = await unreadApi.getUnreadChats();
          if (generation !== unreadChatsGeneration || token !== localStorage.getItem('anilux_access_token_v1')) return [];
        const data = response.data as UnreadChat[] | { results: UnreadChat[] };
        unreadChats.value = "results" in data ? data.results : data;
        unreadChatsLastLoadedAt.value = Date.now();
        return data;
      } catch (error) {
        if (!isRequestCancelled(error)) {
          console.error("Error loading unread chats:", error);
        }
        return [];
      } finally {
          if (generation === unreadChatsGeneration) {
            loadingUnread.value = false;
            unreadChatsLoadingPromise.value = null;
          }
      }
    })();

    return unreadChatsLoadingPromise.value;
  };

  const decrementUnreadCount = (chatId: number, count: number) => {
    const idx = unreadChats.value.findIndex((c) => c.id === chatId);
    if (idx >= 0) {
      const chat = unreadChats.value[idx]!;
      const newCount = Math.max(0, (chat.unread_count || 0) - count);
      if (newCount <= 0) {
        unreadChats.value = unreadChats.value.filter((c) => c.id !== chatId);
      } else {
        unreadChats.value[idx] = { ...chat, unread_count: newCount } as UnreadChat;
      }
    }
    unreadCount.value = Math.max(0, unreadCount.value - count);
  };

  const markAsRead = async (chatId: number, messageId?: number) => {
    try {
      await unreadApi.markAsRead(chatId, messageId);
      unreadCount.value = 0;
      unreadChats.value = unreadChats.value.filter((c) => c.id !== chatId);
    } catch (error) {
      console.error("Error marking as read:", error);
      throw error;
    }
  };

  const getUnreadCountForChat = (chatId: number) => {
    const chat = unreadChats.value.find((c) => c.id === chatId);
    return chat?.unread_count || 0;
  };

  const notifications = ref<NotificationItem[]>([]);
  const loadingNotifications = ref(false);

  const loadNotifications = async () => {
    loadingNotifications.value = true;
    try {
      const response = await apiClient.get("/notifications/notifications/");
      const data = response.data.results || response.data;
      notifications.value = data;
      window.dispatchEvent(
        new CustomEvent("notificationsUpdated", { detail: data }),
      );
      return data;
    } catch (error) {
      console.error("Error loading notifications:", error);
      return [];
    } finally {
      loadingNotifications.value = false;
    }
  };

  const searchMessages = async (
    query: string,
    filters?: {
      chat_id?: string;
      type?: 'private' | 'group';
      topic_id?: number;
      media_type?: string;
      date_from?: string;
      date_to?: string;
    },
  ) => {
    searching.value = true;
    try {
      const response = await searchApi.searchMessages({
        q: query,
        ...filters,
      });
      const data = Array.isArray(response.data) ? { query, results: response.data, count: response.data.length } : response.data;
      searchResults.value = data.results;
      return data;
    } catch (error) {
      console.error("Error searching messages:", error);
      return { query, count: 0, results: [] };
    } finally {
      searching.value = false;
    }
  };

  const clearMessageData = (messageId: number) => {
    messageReactions.value.delete(messageId);
    messageAttachments.value.delete(messageId);
  };

  const clearAllData = () => {
    ++unreadChatsGeneration;
    unreadChatsLoadingPromise.value = null;
    unreadChatsLastLoadedAt.value = null;
    loadingUnread.value = false;
    invites.value = [];
    messageReactions.value.clear();
    messageAttachments.value.clear();
    pinnedMessages.value = [];
    unreadCount.value = 0;
    unreadChats.value = [];
    searchResults.value = [];
  };

  const hasUnreadChats = computed(() => unreadChats.value.length > 0);
  const totalUnreadCount = computed(() => {
    return unreadChats.value.reduce((sum, chat) => sum + chat.unread_count, 0);
  });

  return {
    invites,
    loadingInvites,
    messageReactions,
    loadingReactions,
    messageAttachments,
    loadingAttachments,
    pinnedMessages,
    loadingPinned,
    unreadCount,
    unreadChats,
    loadingUnread,
    searchResults,
    searching,
    notifications,
    loadingNotifications,
    hasUnreadChats,
    totalUnreadCount,
    loadInvites,
    createInvite,
    deleteInvite,
    regenerateInvite,
    revokeInvite,
    joinByToken,
    loadMessageReactions,
    toggleReaction,
    getReactionsForMessage,
    hasUserReacted,
    getReactionCount,
    loadMessageAttachments,
    uploadAttachment,
    deleteAttachment,
    getAttachmentsForMessage,
    loadPinnedMessages,
    pinMessage,
    unpinMessage,
    loadUnreadCount,
    loadUnreadChats,
    markAsRead,
    decrementUnreadCount,
    getUnreadCountForChat,
    loadNotifications,
    searchMessages,
    clearMessageData,
    clearAllData,
  };
});
