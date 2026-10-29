import { ref, computed, onScopeDispose } from "vue";
import { defineStore } from "pinia";
import { useRouter } from "vue-router";
import apiClient, { cancelAllRequests } from "@/api/client";

const clearChatRuntime = async (userId?: number) => {
  const [outbox, socket, privateChats, groupChats, extras, folders] = await Promise.all([
    import('@/lib/chatOutbox'),
    import('@/composables/useGlobalWebSocket'),
    import('@/stores/privateChat'),
    import('@/stores/groupChat'),
    import('@/stores/chatExtras'),
    import('@/stores/chatFolders'),
  ]);
  socket.disconnectGlobalWebSocket();
  outbox.clearChatOutbox(userId);
  privateChats.usePrivateChatStore().clearChats();
  groupChats.useGroupChatStore().clearGroupChats();
  extras.useChatExtrasStore().clearAllData();
  folders.useChatFoldersStore().clearFolders();
};

const startChatRuntime = async () => (await import('@/composables/useGlobalWebSocket')).initGlobalWebSocket();

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  nickname?: string;
  display_name?: string;
  avatar?: string;
  avatar_url?: string;
  level: number;
  experience: number;
  is_online: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  last_login: string;
  phone_number?: string;
  followers_count?: number;
  following_count?: number;
  playlists_count?: number;
  is_verified?: boolean;
  is_admin?: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  competition_wins?: number;
  following?: number[];
  favorite_genres?: number[];
}

export const useAuthStore = defineStore("auth", () => {
  localStorage.removeItem('user');
  let storedUser: User | null = null;
  try {
    const saved = JSON.parse(localStorage.getItem('anilux_user_v1') || 'null');
    if (localStorage.getItem('anilux_access_token_v1') && Number.isInteger(saved?.id) && saved.id > 0) storedUser = saved;
  } catch { /* Invalid stored data is checked by the regular login flow. */ }
  const user = ref<User | null>(storedUser);
  // Cached profile data is useful for rendering, but it is not proof that the
  // persisted token still belongs to an existing account.
  const isAuthenticated = ref(false);
  const loading = ref(false);
  const router = useRouter();
  let storageTimer: ReturnType<typeof setTimeout> | undefined;
  const onStorage = (event: StorageEvent) => {
    if (event.key && !['anilux_access_token_v1', 'anilux_refresh_token_v1', 'anilux_user_v1'].includes(event.key)) return;
    clearTimeout(storageTimer);
    storageTimer = setTimeout(() => {
      const token = localStorage.getItem('anilux_access_token_v1');
      let cached: User | null = null;
      try { cached = JSON.parse(localStorage.getItem('anilux_user_v1') || 'null'); } catch { /* invalid cache */ }
      const changed = !token || !cached?.id || cached.id !== user.value?.id;
      if (changed) {
        onlineUsers.value.clear();
        cancelAllRequests();
        void clearChatRuntime(user.value?.id);
        for (let index = sessionStorage.length - 1; index >= 0; index--) {
          const key = sessionStorage.key(index);
          if (key?.startsWith('chat-draft:')) sessionStorage.removeItem(key);
        }
      }
      user.value = token ? cached : null;
      isAuthenticated.value = false;
      if (token && cached?.id) {
        void checkAuth().then(result => {
          if (!result.success || !isAuthenticated.value) return;
          void startChatRuntime();
          if (changed && router.currentRoute.value.path.startsWith('/chats')) void router.replace('/chats');
        });
      } else if (router.currentRoute.value.path.startsWith('/chats')) void router.replace('/login');
    }, 50);
  };
  window.addEventListener('storage', onStorage);
  onScopeDispose(() => { clearTimeout(storageTimer); window.removeEventListener('storage', onStorage); });

  const login = async (email: string, password: string) => {
    try {
      const response = await apiClient.post("/users/login/", {
        email,
        password,
      });

      const { user: userData, tokens } = response.data;

      localStorage.setItem("anilux_access_token_v1", tokens.access);
      localStorage.setItem("anilux_refresh_token_v1", tokens.refresh);
      localStorage.setItem("anilux_user_v1", JSON.stringify(userData));

      user.value = userData;
      isAuthenticated.value = true;

      return { success: true, user: userData };
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { detail?: string; message?: string } } };
      const errorMessage =
        apiError.response?.data?.detail ||
        apiError.response?.data?.message ||
        "Неверные учетные данные";
      return { success: false, error: errorMessage };
    }
  };

  const register = async (data: {
    username: string;
    email: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    nickname?: string;
  }) => {
    try {
      await apiClient.post("/users/register/", data);
      return { success: true };
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { password?: string[]; username?: string[]; email?: string[] } } };
      const errorMessage =
        apiError.response?.data?.password?.[0] ||
        apiError.response?.data?.username?.[0] ||
        apiError.response?.data?.email?.[0] ||
        "Ошибка регистрации";
      return { success: false, error: errorMessage };
    }
  };

  const googleLogin = async (idToken: string) => {
    try {
      const response = await apiClient.post("/users/google/", {
        id_token: idToken,
      });
      const { user: userData, tokens } = response.data;

      localStorage.setItem("anilux_access_token_v1", tokens.access);
      localStorage.setItem("anilux_refresh_token_v1", tokens.refresh);
      localStorage.setItem("anilux_user_v1", JSON.stringify(userData));

      user.value = userData;
      isAuthenticated.value = true;

      return { success: true, user: userData };
    } catch {
      return { success: false, error: "Ошибка входа через Google" };
    }
  };

  const verifyPhone = async (
    phoneNumber: string,
    action: "send" | "verify",
    code?: string,
  ) => {
    try {
      const response = await apiClient.post("/users/verify/phone/", {
        phone_number: phoneNumber,
        action,
        ...(code && { code }),
      });
      return { success: true, data: response.data };
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { error?: string } } };
      return {
        success: false,
        error: apiError.response?.data?.error || "Ошибка верификации телефона",
      };
    }
  };

  const verifyEmail = async (
    email: string,
    action: "send" | "verify",
    code?: string,
  ) => {
    try {
      const response = await apiClient.post("/users/verify/email/", {
        email,
        action,
        ...(code && { code }),
      });
      return { success: true, data: response.data };
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { error?: string } } };
      return {
        success: false,
        error: apiError.response?.data?.error || "Ошибка верификации email",
      };
    }
  };

  const logout = async () => {
    const { detachDevicePushOnLogout } = await import('@/lib/devicePush')
    await detachDevicePushOnLogout()
    try {
      await apiClient.post("/users/logout/", {
        refresh: localStorage.getItem("anilux_refresh_token_v1"),
      });
    } catch (_error: unknown) {
      console.error("Logout error:", _error);
    } finally {
      await clearChatRuntime(user.value?.id);
      localStorage.removeItem("anilux_access_token_v1");
      localStorage.removeItem("anilux_refresh_token_v1");
      localStorage.removeItem("anilux_user_v1");

      for (let index = sessionStorage.length - 1; index >= 0; index--) {
        const key = sessionStorage.key(index);
        if (key?.startsWith('chat-draft:')) sessionStorage.removeItem(key);
      }
      user.value = null;
      onlineUsers.value.clear();
      isAuthenticated.value = false;

      router.push("/login");
    }
  };

  const clearDeletedAccountSession = async () => {
    await clearChatRuntime(user.value?.id);
    localStorage.clear();
    sessionStorage.clear();
    user.value = null;
    onlineUsers.value.clear();
    isAuthenticated.value = false;
  };

  const fetchUser = async () => {
    try {
      const response = await apiClient.get("/users/profile/", { _keepOnNavigation: true });
      let cachedId: number | undefined;
      try { cachedId = JSON.parse(localStorage.getItem('anilux_user_v1') || 'null')?.id; } catch { /* invalid cache */ }
      if (!localStorage.getItem('anilux_access_token_v1') || cachedId && cachedId !== response.data.id)
        return { success: false, error: 'Аккаунт изменился' };
      user.value = response.data;
      isAuthenticated.value = true;
      return { success: true, user: response.data };
    } catch (error: unknown) {
      const apiError = error as { message?: string; response?: { status?: number } };
      return { success: false, error: apiError.message, status: apiError.response?.status };
    }
  };

  const passwordReset = async (email: string) => {
    try {
      await apiClient.post("/users/password-reset/", { email });
      return { success: true, message: "Новый пароль отправлен на email" };
    } catch (_error: unknown) {
      console.error("Auth Store: Password reset failed", _error);
      return { success: false, error: "Ошибка сброса пароля" };
    }
  };

  const updateProfile = async (profileData: FormData | object) => {
    try {
      const response = await apiClient.patch("/users/profile/", profileData);
      user.value = response.data;
      return { success: true, user: response.data };
    } catch (_error: unknown) {
      console.error("Auth Store: Profile update failed", _error);
      return { success: false, error: "Ошибка обновления профиля" };
    }
  };

  const changePassword = async (
    currentPassword: string,
    newPassword: string,
  ) => {
    try {
      const response = await apiClient.post("/users/change-password/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      return { success: true, data: response.data };
    } catch (error: unknown) {
      console.error("Auth Store: Change password failed", error);
      const apiError = error as { response?: { data?: { detail?: string } } };
      const errorMessage =
        apiError.response?.data?.detail || "Ошибка смены пароля";
      return { success: false, error: errorMessage };
    }
  };

  const checkNickname = async (nickname: string) => {
    try {
      const response = await apiClient.post("/users/nickname/check/", {
        nickname,
      });
      return { available: true, message: response.data.message };
    } catch (error: unknown) {
      const apiError = error as { response?: { data?: { error?: string } } };
      return {
        available: false,
        error: apiError.response?.data?.error || "Nickname недоступен",
      };
    }
  };

  const getUserSessions = async () => {
    try {
      const response = await apiClient.get("/users/sessions/");
      return { success: true, sessions: response.data };
    } catch (_error: unknown) {
      console.error("Auth Store: Get sessions failed", _error);
      return { success: false, error: "Ошибка получения сессий" };
    }
  };

  const revokeSession = async (sessionId: number) => {
    try {
      await apiClient.delete(`/users/sessions/${sessionId}/`);
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Revoke session failed", _error);
      return { success: false, error: "Ошибка завершения сессии" };
    }
  };

  const getUserSettings = async () => {
    try {
      const response = await apiClient.get("/users/settings/");
      return { success: true, settings: response.data };
    } catch (_error: unknown) {
      console.error("Auth Store: Get settings failed", _error);
      return { success: false, error: "Ошибка получения настроек" };
    }
  };

  const updateUserSettings = async (settings: object) => {
    try {
      const response = await apiClient.patch("/users/settings/", settings);
      return { success: true, settings: response.data };
    } catch (_error: unknown) {
      console.error("Auth Store: Update settings failed", _error);
      return { success: false, error: "Ошибка обновления настроек" };
    }
  };

  const setupTwoFactor = async (
    action: "enable" | "disable" | "verify",
    code?: string,
  ) => {
    try {
      const response = await apiClient.post("/users/two-factor/", {
        action,
        ...(code && { code }),
      });
      return { success: true, data: response.data };
    } catch (error: unknown) {
      console.error("Auth Store: 2FA setup failed", error);
      const apiError = error as { response?: { data?: { error?: string } } };
      return {
        success: false,
        error: apiError.response?.data?.error || "Ошибка настройки 2FA",
      };
    }
  };

  const isLocalDevelopment = () => {
    return import.meta.env.DEV && (
      window.location.hostname === "127.0.0.1"
      || window.location.hostname === "::1"
      || window.location.hostname === "localhost"
    );
  };

  const clearInvalidSession = async () => {
    await clearChatRuntime(user.value?.id);
    localStorage.removeItem("anilux_access_token_v1");
    localStorage.removeItem("anilux_refresh_token_v1");
    localStorage.removeItem("anilux_user_v1");
    user.value = null;
    onlineUsers.value.clear();
    isAuthenticated.value = false;

    const path = router.currentRoute.value.path;
    const isPublicPage = path === "/" || path === "/anime" || path.startsWith("/anime/");
    if (!isPublicPage) await router.replace("/login");
  };
  const onInvalidSession = () => { void clearInvalidSession(); };
  window.addEventListener("anilux-auth-session-invalidated", onInvalidSession);
  onScopeDispose(() => window.removeEventListener("anilux-auth-session-invalidated", onInvalidSession));

  const executeAuthCheck = async () => {
    const accessToken = localStorage.getItem("anilux_access_token_v1");
    if (!accessToken) {
      isAuthenticated.value = false;
      return { success: false };
    }

    const result = await fetchUser();
    if (result.success) return { success: true };

    const tokensWereRejected =
      [401, 403].includes(result.status ?? 0) ||
      !localStorage.getItem("anilux_access_token_v1");
    if (tokensWereRejected) await clearInvalidSession();
    return { success: false };
  };

  let authCheck: { token: string; promise: Promise<{ success: boolean }> } | undefined;
  let checkedToken = '';
  let checkedAt = 0;
  const checkAuth = (): Promise<{ success: boolean }> => {
    const token = localStorage.getItem('anilux_access_token_v1') || '';
    if (isAuthenticated.value && checkedToken === token && Date.now() - checkedAt < 60_000)
      return Promise.resolve({ success: true });
    if (authCheck?.token === token) return authCheck.promise;
    const promise = executeAuthCheck().then(result => {
      if (result.success && localStorage.getItem('anilux_access_token_v1') === token) {
        checkedToken = token; checkedAt = Date.now();
      }
      return result;
    }).finally(() => { if (authCheck?.promise === promise) authCheck = undefined; });
    authCheck = { token, promise };
    return promise;
  };

  const initializeAuth = async () => {
    const accessToken = localStorage.getItem("anilux_access_token_v1");
    const userData = localStorage.getItem("anilux_user_v1");

    if (accessToken && userData) {
      try {
        user.value = JSON.parse(userData);
        await checkAuth();
      } catch (error) {
        console.error("Auth Store: Failed to parse stored user data", error);
        logout();
      }
    }
  };

  const followUser = async (userId: number) => {
    try {
      await apiClient.post(`/users/${userId}/follow`);
      if (user.value) {
        user.value.following_count = (user.value.following_count || 0) + 1;
      }
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Follow failed", _error);
      return { success: false, error: "Ошибка подписки" };
    }
  };

  const unfollowUser = async (userId: number) => {
    try {
      await apiClient.delete(`/users/${userId}/follow`);
      if (user.value) {
        user.value.following_count = Math.max(
          0,
          (user.value.following_count || 0) - 1,
        );
      }
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Unfollow failed", _error);
      return { success: false, error: "Ошибка отписки" };
    }
  };

  const blockUser = async (userId: number) => {
    try {
      await apiClient.post(`/users/${userId}/block`);
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Block failed", _error);
      return { success: false, error: "Ошибка блокировки" };
    }
  };

  const unblockUser = async (userId: number) => {
    try {
      await apiClient.delete(`/users/${userId}/block`);
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Unblock failed", _error);
      return { success: false, error: "Ошибка разблокировки" };
    }
  };

  const reportUser = async (userId: number, reason: string) => {
    try {
      await apiClient.post(`/users/${userId}/report`, { reason });
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Report failed", _error);
      return { success: false, error: "Ошибка отправки жалобы" };
    }
  };

  const uploadAvatar = async (file: File): Promise<string> => {
    try {
      const formData = new FormData();
      formData.append("avatar", file);

      const response = await apiClient.post<{ avatar_url: string }>(
        "/users/avatar",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        },
      );

      if (user.value) {
        user.value.avatar = response.data.avatar_url;
        localStorage.setItem("anilux_user_v1", JSON.stringify(user.value));
      }

      return response.data.avatar_url;
    } catch (_error: unknown) {
      console.error("Auth Store: Upload avatar failed", _error);
      throw _error;
    }
  };

  const removeAvatar = async () => {
    try {
      await apiClient.delete("/users/avatar");
      if (user.value) {
        user.value.avatar = undefined;
        localStorage.setItem("anilux_user_v1", JSON.stringify(user.value));
      }
      return { success: true };
    } catch (_error: unknown) {
      console.error("Auth Store: Remove avatar failed", _error);
      return { success: false, error: "Ошибка удаления аватара" };
    }
  };

  const updatePrivacySettings = async (settings: unknown) => {
    try {
      const response = await apiClient.patch("/users/privacy-settings/me/", settings);
      return { success: true, user: response.data };
    } catch {
      return {
        success: false,
        error: "Ошибка обновления настроек приватности",
      };
    }
  };

  const onlineUsers = ref<
    Map<number, { is_online: boolean; last_seen?: string }>
  >(new Map());

  const updateUserOnlineStatus = (userId: number, isOnline: boolean) => {
    const previous = onlineUsers.value.get(userId)?.is_online ?? false;
    onlineUsers.value.set(userId, { is_online: isOnline });
    if (previous === isOnline) return;

    window.dispatchEvent(
      new CustomEvent("userOnlineStatusChanged", {
        detail: { userId, isOnline },
      }),
    );
  };

  const isUserOnline = (userId: number): boolean => {
    return onlineUsers.value.get(userId)?.is_online ?? false;
  };

  const friendRequests = ref<User[]>([]);
  const loadingFriendRequests = ref(false);

  const loadFriendRequests = async () => {
    loadingFriendRequests.value = true;
    try {
      const response = await apiClient.get("/social/follows/requests/");
      friendRequests.value = response.data.results || response.data;
      return friendRequests.value;
    } catch (error) {
      console.error("Error loading friend requests:", error);
      return [];
    } finally {
      loadingFriendRequests.value = false;
    }
  };

  const acceptFriendRequest = async (requestId: number) => {
    try {
      await apiClient.post(`/social/follows/requests/${requestId}/accept/`);
      friendRequests.value = friendRequests.value.filter(
        (r) => r.id !== requestId,
      );
      return { success: true };
    } catch (_error: unknown) {
      console.error("Error accepting friend request:", _error);
      return { success: false, error: "Ошибка принятия запроса" };
    }
  };

  const rejectFriendRequest = async (requestId: number) => {
    try {
      await apiClient.post(`/social/follows/requests/${requestId}/reject/`);
      friendRequests.value = friendRequests.value.filter(
        (r) => r.id !== requestId,
      );
      return { success: true };
    } catch (_error: unknown) {
      console.error("Error rejecting friend request:", _error);
      return { success: false, error: "Ошибка отклонения запроса" };
    }
  };

  const token = computed(() => localStorage.getItem("anilux_access_token_v1"));

  return {
    user,
    isAuthenticated,
    loading,
    token,
    login,
    register,
    googleLogin,
    verifyPhone,
    verifyEmail,
    logout,
    clearDeletedAccountSession,
    fetchUser,
    passwordReset,
    updateProfile,
    changePassword,
    checkNickname,
    getUserSessions,
    revokeSession,
    getUserSettings,
    updateUserSettings,
    setupTwoFactor,
    checkAuth,
    initializeAuth,
    followUser,
    unfollowUser,
    blockUser,
    unblockUser,
    reportUser,
    uploadAvatar,
    removeAvatar,
    updatePrivacySettings,
    onlineUsers,
    updateUserOnlineStatus,
    isUserOnline,
    friendRequests,
    loadFriendRequests,
    acceptFriendRequest,
    rejectFriendRequest,
    isLocalDevelopment,
  };
});
