import { globalConnectionReady as isConnected, setGlobalSender } from "@/lib/realtimeStatus";
import { usePrivateChatStore } from "@/stores/privateChat";
import { useGroupChatStore } from "@/stores/groupChat";
import type { PrivateChat } from "@/stores/privateChat";
import type { GroupChat } from "@/stores/groupChat";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { useAuthStore } from "@/stores/auth";
import { ChatConnection, webSocketProtocols } from "@/lib/chatTimeline";
import apiClient, { getRefreshedAccessToken, getWebSocketUrl } from "@/api/client";
import { usePostStore } from '@/stores/posts';
import { invalidateQueryGroups } from '@/lib/queryClient';
import { applyChatSummary, clearSummaryRevisions } from '@/lib/chatSummaryEvents';
import { chatNotificationsEnabled } from "@/lib/chatNotificationPreferences";

export interface WebSocketMessage {
  action: string;
  [key: string]: unknown;
}

interface MessageData {
  data?: MessageData;
  chat_id?: number;
  message_id?: number;
  user_id?: number;
  username?: string;
  avatar?: string;
  is_typing?: boolean;
  notification?: unknown;
  from_user_id?: number;
  message?: {
    chat_id?: number;
    id?: number;
  };
}

type EventCallback = (data: WebSocketMessage) => void;

let connection: ChatConnection | null = null;
let connectionToken = '';
let authRetryTimer: ReturnType<typeof setTimeout> | undefined;
let connectionGeneration = 0;
const chatVersions = new Map<string, number>();
const eventListeners: Record<string, EventCallback[]> = {};
let reloadTimer: ReturnType<typeof setTimeout> | null = null;
const RELOAD_DEBOUNCE_MS = 300;
const refreshTimers = new Map<string, ReturnType<typeof setTimeout>>();
const refreshEvents = new Map<string, WebSocketMessage>();
const seenEvents = new Set<string>();
const startHeartbeatTimer = () => {};
const stopHeartbeatTimer = () => {};
const sendThrottled = (data: Record<string, unknown>) => connection?.send(data);

const scheduleReload = (includeLists = true) => {
  if (reloadTimer) clearTimeout(reloadTimer);
  reloadTimer = setTimeout(() => {
    reloadTimer = null;
    const privateChatStore = usePrivateChatStore();
    const groupChatStore = useGroupChatStore();
    const chatExtrasStore = useChatExtrasStore();
    if (includeLists || location.pathname.startsWith('/chats') || privateChatStore.chats.length || groupChatStore.allGroupChats.length) {
      privateChatStore.loadChats();
      groupChatStore.loadGroupChats();
    }
    chatExtrasStore.loadUnreadChats();
  }, RELOAD_DEBOUNCE_MS);
};

export function useGlobalWebSocket() {
  const authStore = useAuthStore();
  const privateChatStore = usePrivateChatStore();
  const groupChatStore = useGroupChatStore();
  const chatExtrasStore = useChatExtrasStore();

  const syncUnreadSummary = (row: { id: number; name?: string; avatar_url?: string | null; other_user?: { display_name?: string; username?: string; avatar_url?: string }; unread_count?: number; user_member_settings?: Parameters<typeof chatNotificationsEnabled>[0]['user_member_settings'] }, type: 'private' | 'group', event?: WebSocketMessage) => {
    const id = row.id;
    const remaining = chatExtrasStore.unreadChats.filter(c => !(c.id === id && c.type === type));
    const enabled = chatNotificationsEnabled(row);
    if ((row.unread_count || 0) > 0 && enabled) remaining.push({ id, type,
      name: row.name || row.other_user?.display_name || row.other_user?.username || '',
      unread_count: row.unread_count!, avatar_url: row.avatar_url || row.other_user?.avatar_url });
    chatExtrasStore.unreadChats = remaining;
    const message = event?.message as { id?: number; sender_id?: number; sender?: { id?: number }; text?: string; message_type?: string } | undefined;
    if (event?.action === 'new_message' && message && (message.sender_id ?? message.sender?.id) !== authStore.user?.id &&
        message.message_type !== 'system' && (row.unread_count || 0) > 0 && enabled) {
      window.dispatchEvent(new CustomEvent('browserAttention', { detail: {
        title: row.name || row.other_user?.display_name || row.other_user?.username || 'Новое сообщение',
        body: message.text || 'Новое вложение', url: `/chats/${id}?type=${type}`, tag: `message:${type}:${id}:${message.id}`,
      } }));
    }
  };

  const refreshChat = (data: WebSocketMessage) => {
    const id = Number(data.chat_id);
    const type = data.chat_type;
    if (!id || (type !== 'private' && type !== 'group')) { scheduleReload(); return; }
    const key = `${type}:${id}`;
    refreshEvents.set(key, data);
    if (refreshTimers.has(key)) return;
    refreshTimers.set(key, setTimeout(async () => {
      refreshTimers.delete(key);
      const latestEvent = refreshEvents.get(key) ?? data;
      refreshEvents.delete(key);
      const token = connectionToken;
      const generation = connectionGeneration, revision = chatVersions.get(key);
      try {
        const response = await apiClient.get(`/social/chats/${id}/`, { params: { type } });
        if (token !== connectionToken || generation !== connectionGeneration || revision !== chatVersions.get(key) || !authStore.isAuthenticated) return;
        const row = response.data;
        if (type === 'private') {
          const index = privateChatStore.chats.findIndex(c => c.id === id);
          if (index < 0) privateChatStore.chats.unshift(row as PrivateChat);
          else privateChatStore.chats[index] = row as PrivateChat;
        } else {
          const index = groupChatStore.allGroupChats.findIndex(c => c.id === id);
          if (index < 0) groupChatStore.allGroupChats.unshift(row as GroupChat);
          else groupChatStore.allGroupChats[index] = row as GroupChat;
        }
        syncUnreadSummary(row, type, latestEvent);
      } catch { /* A revoked chat is removed by access_revoked/chat_deleted. */ }
    }, 300));
  };

  const connect = () => {
    const token = localStorage.getItem('anilux_access_token_v1') || '';
    if (!token || !authStore.isAuthenticated) return;
    clearTimeout(authRetryTimer);
    if (connection && connectionToken === token) { connection.start(); return; }
    connection?.stop();
    ++connectionGeneration;
    connectionToken = token;
    connection = new ChatConnection({
      url: () => getWebSocketUrl('/ws/global/'),
      protocols: () => webSocketProtocols(connectionToken),
      state: value => {
        isConnected.value = value;
        setGlobalSender(value ? data => connection?.send(data) : null);
      },
      heartbeat: () => ({ action: 'ping', is_active: !document.hidden }),
      opened: () => scheduleReload(false),
      denied: async code => {
        if (code !== 4001) return;
        const expiredToken = connectionToken;
        try {
          await getRefreshedAccessToken();
          if (authStore.isAuthenticated && connectionToken === expiredToken) connect();
        } catch {
          if (authStore.isAuthenticated && localStorage.getItem('anilux_refresh_token_v1') && connectionToken === expiredToken)
            authRetryTimer = setTimeout(connect, 5000);
        }
      },
      message: data => handleEvent(data as WebSocketMessage),
    });
    connection.start();
  };

  const handleEvent = (data: WebSocketMessage) => {
    const { action } = data;
    const eventId = data.event_id ? String(data.event_id) : '';
    if (eventId) {
      if (seenEvents.has(eventId)) return;
      seenEvents.add(eventId);
      if (seenEvents.size > 2000) seenEvents.delete(seenEvents.values().next().value!);
    }
    if (action === 'new_post' || action.startsWith('post_')) {
      const payload = (data.data || data) as Record<string, unknown>;
      const id = String(payload.post_id || '');
      const store = usePostStore();
      const own = payload.author_id === authStore.user?.id;
      if (!store.applyRealtime(action, payload, authStore.user?.id) && id && (store.entities[id] || own)) void store.refresh(id);
      const original = String(payload.original_post_id || '');
      if (original && store.entities[original]) void store.refresh(original);
      if (own && ['new_post','post_updated','post_deleted'].includes(action)) void invalidateQueryGroups(['profile']);
    }
    if (data.protocol_version === 2 && ['new_message', 'message_edited', 'message_deleted', 'chat_cleared',
        'chat_created', 'chat_updated', 'chat_restored', 'unread_updated', 'messages_read', 'member_updated'].includes(action)) {
      const key = `${data.chat_type}:${data.chat_id}`;
      chatVersions.set(key, (chatVersions.get(key) ?? 0) + 1);
      const row = data.chat_type === 'private' ? privateChatStore.chats.find(c => c.id === Number(data.chat_id)) : groupChatStore.allGroupChats.find(c => c.id === Number(data.chat_id));
      const result = row ? applyChatSummary(`${authStore.user?.id}:${key}`, row, data, authStore.user?.id) : 'refresh';
      if (result === 'refresh') refreshChat(data);
      else if (result === 'patched' && row) syncUnreadSummary(row, data.chat_type as 'private' | 'group', data);
      eventListeners[action]?.forEach(callback => callback(data));
      return;
    }
    if (data.protocol_version === 2 && ['chat_deleted', 'access_revoked'].includes(action)) {
      const key = `${data.chat_type}:${data.chat_id}`;
      chatVersions.set(key, (chatVersions.get(key) ?? 0) + 1);
      const id = Number(data.chat_id);
      if (data.chat_type === 'private') privateChatStore.chats = privateChatStore.chats.filter(c => c.id !== id);
      else groupChatStore.allGroupChats = groupChatStore.allGroupChats.filter(c => c.id !== id);
      chatExtrasStore.unreadChats = chatExtrasStore.unreadChats.filter(c => !(c.id === id && c.type === data.chat_type));
      eventListeners[action]?.forEach(callback => callback(data));
      return;
    }

    if (eventListeners[action]) {
      eventListeners[action].forEach((callback) => callback(data));
    }

    switch (action) {
      case "chat_created": {
        const chatData = (data as { chat?: Record<string, unknown> }).chat;
        if (chatData && chatData.id) {
          const isPrivate = (chatData as Record<string, unknown>).user1 !== undefined;
          if (isPrivate) {
            const existingIndex = privateChatStore.chats.findIndex((c) => c.id === chatData.id);
            if (existingIndex !== -1) {
              privateChatStore.chats[existingIndex] = chatData as unknown as PrivateChat;
            } else {
              privateChatStore.chats.unshift(chatData as unknown as PrivateChat);
            }
          } else {
            const existingIndex = groupChatStore.allGroupChats.findIndex((c) => c.id === chatData.id);
            if (existingIndex !== -1) {
              groupChatStore.allGroupChats[existingIndex] = chatData as unknown as GroupChat;
            } else {
              groupChatStore.allGroupChats.unshift(chatData as unknown as GroupChat);
            }
          }
        }
        chatExtrasStore.loadUnreadChats();
        break;
      }
      case "chat_deleted":
      case "group_chat_created":
      case "chat_updated":
      case "unread_updated":
      case "message_sent":
      case "message_read":
      case "unread_count_updated":
        scheduleReload();
        break;

      case "new_message": {
        const messageData = data as MessageData & { message?: Record<string, unknown> };
        const chatId = messageData.message?.chat_id || messageData.chat_id;
        if (chatId) {
          const msg = messageData.message;
          if (msg && msg.id && msg.created_at) {
            const privateIndex = privateChatStore.chats.findIndex((c) => c.id === chatId);
            if (privateIndex !== -1) {
              const privateChat = privateChatStore.chats[privateIndex]!;
              privateChat.last_message_at = msg.created_at as string;
              privateChat.last_message = {
                id: msg.id as number,
                text: msg.text as string,
                created_at: msg.created_at as string,
                sender: (msg.sender as unknown as { id: number; username: string } | null | undefined) || { id: 0, username: "" },
              } as PrivateChat["last_message"];
            }
            const groupIndex = groupChatStore.allGroupChats.findIndex((c) => c.id === chatId);
            if (groupIndex !== -1) {
              const groupChat = groupChatStore.allGroupChats[groupIndex]!;
              groupChat.last_message = {
                text: (msg.text as string) || "",
                created_at: msg.created_at as string,
                sender: (msg.sender as unknown as { id: number; username: string } | undefined) || undefined,
              } as GroupChat["last_message"];
            }
          }
          chatExtrasStore.loadUnreadChats();
        }
        break;
      }

      case "message_deleted": {
        const messageData = data as MessageData;
        window.dispatchEvent(
          new CustomEvent("messageDeleted", {
            detail: {
              messageId: messageData.message_id,
              chatId: messageData.chat_id,
            },
          }),
        );
        scheduleReload();
        break;
      }

      case "message_edited": {
        const edited = data as { message?: Record<string, unknown> };
        window.dispatchEvent(
          new CustomEvent("messageEdited", {
            detail: { message: edited.message ?? edited },
          }),
        );
        break;
      }

      case "chat_cleared": {
        const cleared = data as MessageData;
        window.dispatchEvent(
          new CustomEvent("chatCleared", { detail: { chatId: cleared.chat_id } }),
        );
        scheduleReload();
        break;
      }

      case "post_liked":
      case "post_commented":
      case "post_reposted":
      case "new_follower":
      case "new_post": {
        window.dispatchEvent(
          new CustomEvent(action, { detail: (data as { data?: unknown }).data ?? data }),
        );
        break;
      }

      case "user_online": {
        const userData = data as MessageData;
        if (userData.user_id) {
          authStore.updateUserOnlineStatus(userData.user_id, true);
        }
        break;
      }

      case "user_offline": {
        const userData = data as MessageData;
        if (userData.user_id) {
          authStore.updateUserOnlineStatus(userData.user_id, false);
        }
        break;
      }

      case "user_typing": {
        const typingData = data as MessageData;
        window.dispatchEvent(
          new CustomEvent("userTyping", {
            detail: {
              chatId: typingData.chat_id,
              userId: typingData.user_id,
              username: typingData.username,
              isTyping: typingData.is_typing,
            },
          }),
        );
        break;
      }

      case "notification": {
        const notifData = data as MessageData;
        chatExtrasStore.loadNotifications();
        window.dispatchEvent(
          new CustomEvent("newNotification", {
            detail: notifData.notification || (notifData.data as MessageData | undefined)?.notification || null,
          }),
        );
        break;
      }

      case "invite_received":
        chatExtrasStore.loadInvites();
        break;

      case "friend_request": {
        const requestData = data as MessageData;
        authStore.loadFriendRequests();
        window.dispatchEvent(
          new CustomEvent("newFriendRequest", {
            detail: {
              from_user_id: requestData.from_user_id,
              username: requestData.username,
              avatar: requestData.avatar,
            },
          }),
        );
        break;
      }

      case "friend_accepted": {
        const acceptData = data as MessageData;
        window.dispatchEvent(
          new CustomEvent("friendAccepted", {
            detail: {
              user_id: acceptData.user_id,
              username: acceptData.username,
            },
          }),
        );
        break;
      }

      case "pong":
        break;

      default:
        console.debug("Unknown WebSocket action:", action);
        break;
    }
  };

  const disconnect = () => {
    clearTimeout(authRetryTimer);
    ++connectionGeneration; chatVersions.clear();
    stopHeartbeatTimer();
    if (reloadTimer) {
      clearTimeout(reloadTimer);
      reloadTimer = null;
    }
    refreshTimers.forEach(timer => clearTimeout(timer));
    refreshTimers.clear(); refreshEvents.clear(); seenEvents.clear();
    connection?.stop(); connection = null; connectionToken = '';
    isConnected.value = false;
    clearSummaryRevisions();
  };

  const subscribe = (action: string, callback: EventCallback) => {
    if (!eventListeners[action]) {
      eventListeners[action] = [];
    }
    eventListeners[action].push(callback);

    return () => {
      const index = eventListeners[action]?.indexOf(callback) ?? -1;
      if (index > -1) {
        eventListeners[action]?.splice(index, 1);
      }
    };
  };

  const send = (data: Record<string, unknown>) => {
    sendThrottled(data);
  };

  const sendTyping = (chatId: number, isTyping: boolean) => {
    send({
      action: isTyping ? "typing_start" : "typing_stop",
      chat_id: chatId,
    });
  };

  return {
    isConnected,
    connect,
    disconnect,
    subscribe,
    send,
    sendTyping,
    startHeartbeat: startHeartbeatTimer,
    stopHeartbeat: stopHeartbeatTimer,
  };
}

export function initGlobalWebSocket() {
  const authStore = useAuthStore();
  if (authStore.isAuthenticated) {
    const { connect, startHeartbeat } = useGlobalWebSocket();
    connect();
    startHeartbeat();
  }
}

export function disconnectGlobalWebSocket() {
  const { disconnect } = useGlobalWebSocket();
  disconnect();
}
