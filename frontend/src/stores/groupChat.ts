import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import apiClient, { isRequestCancelled } from "@/api/client";
import { useCachedReads } from '@/composables/useCachedReads';
import { queryClient } from '@/lib/queryClient';
import { useAuthStore } from '@/stores/auth';

export interface GroupChat {
  public_id?: number;
  conversation_id?: number;
  id: number;
  code: string;
  name: string;
  description: string;
  avatar: string | null;
  avatar_url?: string | null;
  created_at: string;
  created_by: {
    id: number;
    username: string;
    email: string;
  };
  is_public: boolean;
  invite_link: string | null;
  max_members: number;
  members_count: number;
  online_count: number;
  user_role: {
    is_owner: boolean;
    role: ChatRole | null;
    custom_title: string;
    is_admin: boolean;
  } | null;
  user_permissions: Record<string, boolean>;
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
  user_member_settings?: {
    is_pinned?: boolean;
    is_archived?: boolean;
    is_muted?: boolean;
    muted_until?: string | null;
  };
}

export interface ChatRole {
  id: number;
  name: string;
  level: number;
  color: string;
  can_delete_messages: boolean;
  can_ban_users: boolean;
  can_pin_messages: boolean;
  can_add_new_admins: boolean;
  can_remain_anonymous: boolean;
  can_manage_chat: boolean;
  can_manage_video_chats: boolean;
  can_restrict_members: boolean;
  can_promote_members: boolean;
  can_change_chat_info: boolean;
  can_invite_users: boolean;
  can_post_messages: boolean;
  can_edit_messages: boolean;
  can_delete_chat: boolean;
}

export interface ChatMember {
  id: number;
  user: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
    avatar?: string | null;
    avatar_url?: string | null;
    status: {
      status: string;
      last_seen: string;
      custom_status: string;
    } | null;
  };
  role: ChatRole | null;
  role_id: number | null;
  is_admin: boolean;
  is_owner: boolean;
  joined_at: string;
  custom_title: string;
  is_muted: boolean;
  muted_until: string | null;
  can_send_messages: boolean;
  can_send_media: boolean;
  can_add_reactions: boolean;
  can_send_polls: boolean;
  can_change_info: boolean;
  can_invite_users: boolean;
  can_pin_messages: boolean;
  is_banned: boolean;
  effective_permissions: Record<string, boolean>;
}

interface ChatAdminLog {
  id: number;
  chat: number;
  user: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
  } | null;
  action: string;
  action_display: string;
  target_user: {
    id: number;
    username: string;
    first_name: string;
    last_name: string;
    email: string;
  } | null;
  message: number | null;
  details: Record<string, unknown>;
  created_at: string;
}

export const useGroupChatStore = defineStore("groupChat", () => {
  const read = useCachedReads();
  const auth = useAuthStore();
  const dismissedStorageKey = computed(() => `anilux_dismissed_group_chats_${auth.user?.id ?? 'guest'}`);
  const readDismissedIds = () => {
    try {
      const values = JSON.parse(localStorage.getItem(dismissedStorageKey.value) || '[]');
      return Array.isArray(values) ? values.map(Number).filter(Number.isSafeInteger) : [];
    } catch {
      return [];
    }
  };
  const dismissedGroupChatIds = ref<number[]>(readDismissedIds());
  const currentChat = ref<GroupChat | null>(null);
  const chatMembers = ref<ChatMember[]>([]);
  const chatRoles = ref<ChatRole[]>([]);
  const adminLogs = ref<ChatAdminLog[]>([]);
  const userPermissions = ref<Record<number, Record<string, boolean>>>({});

  const loadingChat = ref(false);
  const loadingMembers = ref(false);
  const loadingRoles = ref(false);
  const loadingLogs = ref(false);

  const allGroupChats = ref<GroupChat[]>([]);
  const loadingGroupChats = ref(false);

  const isOwner = computed(
    () => currentChat.value?.user_role?.is_owner || false,
  );
  const isAdmin = computed(
    () => currentChat.value?.user_role?.is_admin || false,
  );
  const currentUserPermissions = computed(() =>
    currentChat.value ? userPermissions.value[currentChat.value.id] || {} : {},
  );

  const loadChat = async (chatId: number) => {
    loadingChat.value = true;
    try {
      const response = await apiClient.get(`/social/group-chats/${chatId}/`);
      currentChat.value = response.data;
      if (currentChat.value) {
        userPermissions.value[currentChat.value.id] =
          currentChat.value.user_permissions;
      }
    } catch (error) {
      console.error("Error loading group chat:", error);
      throw error;
    } finally {
      loadingChat.value = false;
    }
  };

  const loadChatMembers = async (chatId: number) => {
    loadingMembers.value = true;
    try {
      const response = await apiClient.get(
        `/social/group-chats/${chatId}/members/`,
      );
      const data = response.data as ChatMember[] | { results: ChatMember[] };
      chatMembers.value = "results" in data ? data.results : data;
    } catch (error) {
      console.error("Error loading chat members:", error);
      throw error;
    } finally {
      loadingMembers.value = false;
    }
  };

  const loadChatRoles = async (chatId: number) => {
    loadingRoles.value = true;
    try {
      const response = await apiClient.get(
        `/social/group-chats/${chatId}/roles/`,
      );
      const data = response.data as ChatRole[] | { results: ChatRole[] };
      chatRoles.value = "results" in data ? data.results : data;
    } catch (error) {
      console.error("Error loading chat roles:", error);
      throw error;
    } finally {
      loadingRoles.value = false;
    }
  };

  const loadAdminLogs = async (chatId: number) => {
    loadingLogs.value = true;
    try {
      const response = await apiClient.get(
        `/social/group-chats/${chatId}/admin-logs/`,
      );
      const data = response.data as
        ChatAdminLog[] | { results: ChatAdminLog[] };
      adminLogs.value = "results" in data ? data.results : data;
    } catch (error) {
      console.error("Error loading admin logs:", error);
      throw error;
    } finally {
      loadingLogs.value = false;
    }
  };

  const createGroupChat = async (data: {
    name: string;
    description?: string;
    is_public?: boolean;
  }) => {
    try {
      const response = await apiClient.post("/social/group-chats/", data);
      return response.data;
    } catch (error) {
      console.error("Error creating group chat:", error);
      throw error;
    }
  };

  const updateGroupChat = async (chatId: number, data: Partial<GroupChat>) => {
    try {
      const response = await apiClient.patch(
        `/social/group-chats/${chatId}/`,
        data,
      );
      if (currentChat.value && currentChat.value.id === chatId) {
        currentChat.value = { ...currentChat.value, ...response.data };
      }
      return response.data;
    } catch (error) {
      console.error("Error updating group chat:", error);
      throw error;
    }
  };

  const deleteGroupChat = async (chatId: number) => {
    try {
      await apiClient.delete(`/social/group-chats/${chatId}/`);
      if (currentChat.value && currentChat.value.id === chatId) {
        currentChat.value = null;
      }
    } catch (error) {
      console.error("Error deleting group chat:", error);
      throw error;
    }
  };

  const inviteUser = async (
    chatId: number,
    userId: number,
    message?: string,
  ) => {
    try {
      const response = await apiClient.post(
        `/social/group-chats/${chatId}/invite_user/`,
        {
          user_id: userId,
          message: message || "",
        },
      );
      return response.data;
    } catch (error) {
      console.error("Error inviting user:", error);
      throw error;
    }
  };

  const removeMember = async (
    chatId: number,
    userId: number,
    reason?: string,
  ) => {
    try {
      await apiClient.post(`/social/group-chats/${chatId}/remove_member/`, {
        user_id: userId,
        reason: reason || "",
      });
    } catch (error) {
      console.error("Error removing member:", error);
      throw error;
    }
  };

  const banUser = async (
    chatId: number,
    userId: number,
    reason?: string,
    untilDate?: string,
  ) => {
    try {
      await apiClient.post(`/social/group-chats/${chatId}/ban_user/`, {
        user_id: userId,
        reason: reason || "",
        until_date: untilDate,
      });
    } catch (error) {
      console.error("Error banning user:", error);
      throw error;
    }
  };

  const updateMemberRole = async (
    chatId: number,
    userId: number,
    roleId: number | null,
    isAdmin?: boolean,
  ) => {
    try {
      const response = await apiClient.post(
        `/social/group-chats/${chatId}/members/${userId}/role/`,
        {
          role_id: roleId,
          is_admin: isAdmin,
        },
      );
      return response.data;
    } catch (error) {
      console.error("Error updating member role:", error);
      throw error;
    }
  };

  const createChatRole = async (
    chatId: number,
    roleData: Partial<ChatRole>,
  ) => {
    try {
      const response = await apiClient.post(
        `/social/group-chats/${chatId}/roles/`,
        roleData,
      );
      chatRoles.value.push(response.data);
      return response.data;
    } catch (error) {
      console.error("Error creating chat role:", error);
      throw error;
    }
  };

  const updateChatRole = async (
    chatId: number,
    roleId: number,
    roleData: Partial<ChatRole>,
  ) => {
    try {
      const response = await apiClient.patch(
        `/social/group-chats/${chatId}/roles/${roleId}/`,
        roleData,
      );
      const index = chatRoles.value.findIndex((role) => role.id === roleId);
      if (index !== -1) {
        chatRoles.value[index] = response.data;
      }
      return response.data;
    } catch (error) {
      console.error("Error updating chat role:", error);
      throw error;
    }
  };

  const deleteChatRole = async (chatId: number, roleId: number) => {
    try {
      await apiClient.delete(`/social/group-chats/${chatId}/roles/${roleId}/`);
      chatRoles.value = chatRoles.value.filter((role) => role.id !== roleId);
    } catch (error) {
      console.error("Error deleting chat role:", error);
      throw error;
    }
  };

  const toggleMemberMute = async (
    chatId: number,
    userId: number,
    muted: boolean,
  ) => {
    const member = chatMembers.value.find((m) => m.user.id === userId);
    if (member) {
      member.is_muted = muted;
      if (!muted) {
        member.muted_until = null;
      }
    }
  };

  const leaveChat = async (chatId: number) => {
    if (currentChat.value && currentChat.value.id === chatId) {
      currentChat.value = null;
    }
    chatMembers.value = [];
    chatRoles.value = [];
    adminLogs.value = [];
  };

  const isGroupChatDismissed = (chatId?: number) =>
    Number.isSafeInteger(Number(chatId)) && dismissedGroupChatIds.value.includes(Number(chatId));

  const loadGroupChats = async () => {
    loadingGroupChats.value = true;
    try {
      await read(['group-chats'], async signal => (await apiClient.get('/social/group-chats/', { signal })).data, response => {
        const chats = response.results || response;
        allGroupChats.value = chats.filter((chat: GroupChat) => !isGroupChatDismissed(chat.id) && !isGroupChatDismissed(chat.public_id));
        window.dispatchEvent(new CustomEvent('groupChatsUpdated', { detail: allGroupChats.value }));
      });
      const data = allGroupChats.value;
      return data;
    } catch (error) {
      if (!isRequestCancelled(error)) console.error("Error loading group chats:", error);
      return [];
    } finally {
      loadingGroupChats.value = false;
    }
  };

  const clearGroupChats = () => {
    allGroupChats.value = [];
  };

  const removeGroupChatFromList = (chatId: number) => {
    const matches = (chat: GroupChat) =>
      Number(chat.id) === Number(chatId) || Number(chat.public_id) === Number(chatId);
    const removed = allGroupChats.value.filter(matches);
    const ids = new Set(dismissedGroupChatIds.value);
    ids.add(Number(chatId));
    removed.forEach((chat) => {
      ids.add(Number(chat.id));
      if (chat.public_id) ids.add(Number(chat.public_id));
    });
    dismissedGroupChatIds.value = [...ids].filter(Number.isSafeInteger);
    localStorage.setItem(dismissedStorageKey.value, JSON.stringify(dismissedGroupChatIds.value));
    allGroupChats.value = allGroupChats.value.filter((chat) => !matches(chat));
    if (currentChat.value && matches(currentChat.value)) currentChat.value = null;

    const queryKey = ['read', String(auth.user?.id ?? 'guest'), 'group-chats'] as const;
    void queryClient.cancelQueries({ queryKey, exact: true }).then(() => {
      queryClient.setQueryData<GroupChat[] | { results: GroupChat[] }>(queryKey, (cached) => {
        if (Array.isArray(cached)) return cached.filter((chat) => !matches(chat));
        if (cached?.results) return { ...cached, results: cached.results.filter((chat) => !matches(chat)) };
        return cached;
      });
      return queryClient.invalidateQueries({ queryKey, exact: true });
    });

    window.dispatchEvent(new CustomEvent('groupChatsUpdated', { detail: allGroupChats.value }));
  };

  const restoreGroupChatToList = (chatId: number) => {
    dismissedGroupChatIds.value = dismissedGroupChatIds.value.filter((id) => id !== Number(chatId));
    localStorage.setItem(dismissedStorageKey.value, JSON.stringify(dismissedGroupChatIds.value));
  };

  watch(() => auth.user?.id, () => {
    dismissedGroupChatIds.value = readDismissedIds();
  });

  const decrementUnreadCount = (chatId: number, count: number) => {
    const chat = allGroupChats.value.find((c) => c.id === chatId);
    if (!chat) return;
    const current = chat.unread_count || 0;
    const next = Math.max(0, current - count);
    chat.unread_count = next;
  };

  const hasPermission = (permission: string): boolean => {
    return currentUserPermissions.value[permission] || false;
  };

  const canManageChat = (): boolean => {
    return hasPermission("can_manage_chat") || isOwner.value;
  };

  const canBanUsers = (): boolean => {
    return hasPermission("can_ban_users") || isOwner.value;
  };

  const canInviteUsers = (): boolean => {
    return hasPermission("can_invite_users") || isOwner.value;
  };

  const canDeleteMessages = (): boolean => {
    return hasPermission("can_delete_messages") || isOwner.value;
  };

  const canChangeChatInfo = (): boolean => {
    return hasPermission("can_change_chat_info") || isOwner.value;
  };

  const canPinMessages = (): boolean => {
    return hasPermission("can_pin_messages") || isOwner.value;
  };

  const canPromoteMembers = (): boolean => {
    return hasPermission("can_promote_members") || isOwner.value;
  };

  return {
    currentChat,
    chatMembers,
    chatRoles,
    adminLogs,
    userPermissions,
    loadingChat,
    loadingMembers,
    loadingRoles,
    loadingLogs,
    isOwner,
    isAdmin,
    currentUserPermissions,

    loadChat,
    loadChatMembers,
    loadChatRoles,
    loadAdminLogs,
    createGroupChat,
    updateGroupChat,
    deleteGroupChat,
    inviteUser,
    removeMember,
    banUser,
    updateMemberRole,
    createChatRole,
    updateChatRole,
    deleteChatRole,
    toggleMemberMute,
    leaveChat,

    hasPermission,
    canManageChat,
    canBanUsers,
    canInviteUsers,
    canDeleteMessages,
    canChangeChatInfo,
    canPinMessages,
    canPromoteMembers,
    allGroupChats,     
    loadingGroupChats, 
    loadGroupChats, 
    clearGroupChats,  
    removeGroupChatFromList,
    isGroupChatDismissed,
    restoreGroupChatToList,
    decrementUnreadCount,
  };
});
