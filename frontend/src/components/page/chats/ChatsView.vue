<template>
  <div class="chats-app" :class="{ 'has-active-chat': activeChatId || activeFranchiseId }">
    <nav v-if="isAdmin" class="chat-mode-switch" aria-label="Режим чатов">
      <button type="button" :class="{ active: isAdminMode }" @click="setMode('admin')">
        Обращения в поддержку
      </button>
      <button type="button" :class="{ active: !isAdminMode }" @click="setMode('regular')">
        Обычные чаты
      </button>
    </nav>

    <div class="chats-layout">
      <aside class="chats-sidebar">
        <ChatList
          :active-chat-id="activeChatId"
          :active-franchise-id="activeFranchiseId"
          :active-chat-type="activeChatType"
          :chat-mode="chatListMode"
          @chat-selected="handleChatSelected"
        />
      </aside>

      <main class="chats-main">
        <div v-if="!activeChatId && !activeFranchiseId" class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <p>{{ resolvingRoute ? 'Загрузка обсуждения...' : routeError || (isAdminMode ? 'Выберите обращение' : 'Выберите чат, чтобы начать общение') }}</p>
          <button v-if="routeError" type="button" @click="updateChatTypeFromRoute">Повторить</button>
        </div>

        <ChatDetailView
          v-else
          :key="`${activeChatType}-${activeChatId}-${activeFranchiseId}-${activeTopicSlug}`"
          :chat-id="activeChatId"
          :chat-type="activeChatType"
          :franchise-id="activeFranchiseId"
          :topic-slug="activeTopicSlug"
          @back="goBack"
        />
      </main>
    </div>

    <button
      v-if="isMobile && (activeChatId || activeFranchiseId)"
      class="mobile-back"
      aria-label="К списку чатов"
      @click="goBack"
    >
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, ref, onMounted, onUnmounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import ChatList from "@/components/Chats/ChatList.vue";
const ChatDetailView = defineAsyncComponent(() => import("@/components/page/chats/ChatDetailView.vue"));
import { usePrivateChatStore } from "@/stores/privateChat";
import apiClient from "@/api/client";
import { useGroupChatStore } from "@/stores/groupChat";
import type { LocalChat } from "@/components/Chats/ChatList.vue";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const router = useRouter();
const privateChatStore = usePrivateChatStore();
const groupChatStore = useGroupChatStore();
const authStore = useAuthStore();
const isAdmin = computed(() => Boolean(authStore.user?.is_admin || authStore.user?.is_staff || authStore.user?.is_superuser));
const hasChatRoute = computed(() => Boolean(route.params.id || route.params.code || route.params.slug));
const isAdminMode = computed(() => isAdmin.value && (
  route.query.mode === "admin" || (!hasChatRoute.value && route.query.mode !== "regular")
));
const chatListMode = computed<"all" | "regular" | "support">(() => {
  if (!isAdmin.value) return "all";
  return isAdminMode.value ? "support" : "regular";
});

const setMode = (mode: "admin" | "regular") => {
  if (mode === "regular") void router.push({ path: "/chats", query: { mode: "regular" } });
  else void router.push({ path: "/chats", query: { mode: "admin" } });
};

const activeChatId = ref<number | undefined>(undefined);
const activeFranchiseId = ref<number | undefined>(undefined);
const activeChatType = ref<"private" | "group" | null>(null);
const activeTopicSlug = ref<string | undefined>(undefined);
const isMobile = ref(false);
const resolvingRoute = ref(false), routeError = ref('');
let routeGeneration = 0;

const parseRouteChatId = (raw: unknown): number | undefined => {
  if (raw === undefined || raw === null) return undefined;
  const str = String(raw);
  if (!str || str === "undefined") return undefined;
  if (!/^[0-9]+$/.test(str)) return undefined;
  const num = Number(str);
  return Number.isSafeInteger(num) && num > 0 ? num : undefined;
};

const resolveChatIdFromSlug = (slug: string): number | undefined => {
  if (!slug) return undefined;
  const normalized = slug.toLowerCase();

  const groupMatch = groupChatStore.allGroupChats.find((c) => {
    const animeSlug = (c.anime_slug || "").toLowerCase();
    const franchiseSlug = (c.franchise_slug || "").toLowerCase();
    const name = (c.name || "").toLowerCase();
    const animeTitle = (c.anime_title || "").toLowerCase();
    return (
      animeSlug === normalized ||
      franchiseSlug === normalized ||
      name === normalized ||
      animeTitle === normalized
    );
  });
  if (groupMatch) return groupMatch.id;

  return undefined;
};

const getChatIdFromRoute = (): number | undefined => {
  const fromId = parseRouteChatId(route.params.id);
  if (fromId) return fromId;
  const fromCode = parseRouteChatId(route.params.code);
  if (fromCode) return fromCode;
  const fromSlug = parseRouteChatId(route.params.slug);
  if (fromSlug) return fromSlug;

  const slug = route.params.slug;
  if (slug && typeof slug === "string") {
    return resolveChatIdFromSlug(slug);
  }

  return undefined;
};

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768;
};

const goBack = () => {
  activeChatId.value = undefined;
  activeFranchiseId.value = undefined;
  activeChatType.value = null;
  activeTopicSlug.value = undefined;
  router.push(isAdmin.value ? { path: "/chats", query: { mode: isAdminMode.value ? "admin" : "regular" } } : "/chats");
};

const handleChatSelected = async (chat: LocalChat) => {
  await router.push({
    path: `/chats/${chat.public_id || chat.id || ''}`,
    query: { type: chat.type, ...(isAdmin.value ? { mode: isAdminMode.value ? "admin" : "regular" } : {}) },
  });
};

  const detectChatType = (chatId: number): "private" | "group" | null => {
    const inPrivate = privateChatStore.chats.some((c) => c.id === chatId || c.public_id === chatId);
    const inGroup = groupChatStore.allGroupChats.some((c) => c.id === chatId || c.public_id === chatId);
    if (inPrivate && !inGroup) return "private";
    if (inGroup && !inPrivate) return "group";
    return null;
  };

  const updateChatTypeFromRoute = async () => {
    const generation = ++routeGeneration, path = route.fullPath;
    resolvingRoute.value = false; routeError.value = '';
    const chatId = getChatIdFromRoute();
    const slug = String(route.params.slug || '');
    if (!chatId && slug) {
      resolvingRoute.value = true;
      try {
        let parent;
        try {
          const { data } = await apiClient.get(`/anime/franchises/${encodeURIComponent(slug)}/`);
          if (data.slug !== slug) throw new Error('Обсуждение не найдено');
          parent = { kind: 'franchise', id: data.id };
        } catch (error) {
          if ((error as { response?: { status: number } }).response?.status !== 404) throw error;
          const { data } = await apiClient.get(`/anime/${encodeURIComponent(slug)}/`);
          if (data.slug !== slug) throw new Error('Обсуждение не найдено');
          parent = { kind: 'anime', id: data.id };
        }
        if (generation !== routeGeneration || path !== route.fullPath) return;
        const endpoint = parent.kind === 'franchise' ? `/social/franchise/${parent.id}/discussion/join/` :
          `/social/anime/${parent.id}/discussion-group/join/`;
        const { data } = await apiClient.post(endpoint);
        if (generation !== routeGeneration || path !== route.fullPath) return;
        const topic = data.topics?.find((t: { id: number }) => t.id === data.current_topic_id);
        await router.replace({ path: `/chats/${data.public_id || data.id}`, query: {
          ...route.query, type: 'group', ...(topic ? { topic: topic.slug || String(topic.anime_id) } : {}),
        } });
      } catch {
        if (generation === routeGeneration && path === route.fullPath) routeError.value = 'Не удалось открыть обсуждение';
      } finally { if (generation === routeGeneration) resolvingRoute.value = false; }
      return;
    }
    if (chatId) {
      const inPrivate = privateChatStore.chats.some((c) => c.id === chatId || c.public_id === chatId);
      const inGroup = groupChatStore.allGroupChats.some((c) => c.id === chatId || c.public_id === chatId);
      if (!inPrivate && !inGroup) {
        try {
          const res = await apiClient.get(`/social/chats/${chatId}/`);
          if (generation !== routeGeneration || path !== route.fullPath) return;
          if (res.data?.type === 'private' && !privateChatStore.chats.some(c => c.id === res.data.id)) {
            privateChatStore.chats.push(res.data);
          } else if (res.data?.type === 'group' && !groupChatStore.allGroupChats.some(c => c.id === res.data.id)) {
            groupChatStore.allGroupChats.push(res.data);
          }
        } catch {
        }
      }
    }
    if (chatId && generation === routeGeneration && path === route.fullPath) {
      const requested = route.query.type;
      activeChatType.value = requested === 'private' || requested === 'group' ? requested : detectChatType(chatId);
      activeChatId.value = chatId;
    }
  };

onMounted(async () => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
  if (!isAdmin.value) {
    try {
      await privateChatStore.ensureAdministratorChat();
    } catch (error) {
      console.error("Failed to initialize administrator chat:", error);
    }
  }
  await Promise.all([
    privateChatStore.loadChats(),
    groupChatStore.loadGroupChats(),
  ]);
  await updateChatTypeFromRoute();
});

  watch(
    () => [route.name, route.params.id, route.params.slug, route.params.code, route.query.type] as const,
  async ([name, newId, newSlug, newCode, requestedType]) => {
      const chatId = parseRouteChatId(newId) ?? parseRouteChatId(newCode) ?? parseRouteChatId(newSlug);
      if (!chatId) {
        const resolved = resolveChatIdFromSlug(String(newSlug || ""));
        if (resolved) {
          router.replace(`/chats/${resolved}`);
          return;
        }
        activeChatId.value = undefined;
        activeFranchiseId.value = undefined;
        activeChatType.value = null;
        activeTopicSlug.value = undefined;
        await updateChatTypeFromRoute();
        return;
      }
      activeChatType.value = requestedType === 'private' || requestedType === 'group' ? requestedType : detectChatType(chatId);
      activeFranchiseId.value = groupChatStore.allGroupChats.find(c => c.id === chatId)?.franchise_id ?? undefined;
      activeChatId.value = chatId;
      activeTopicSlug.value = name === "chat-topic" ? String(newSlug || "") : undefined;
      if (activeChatType.value === null) {
        activeChatType.value = detectChatType(chatId);
      }
      await updateChatTypeFromRoute();
    }
  );

watch(
  [() => privateChatStore.chats, () => groupChatStore.allGroupChats],
  () => {
    if (activeChatId.value && !activeChatType.value) {
      activeChatType.value = detectChatType(activeChatId.value);
    }
  }
);

onUnmounted(() => {
  ++routeGeneration;
  window.removeEventListener("resize", checkMobile);
});
</script>

<style scoped>
.chats-app {
  height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
  overflow: hidden;
}

.chat-mode-switch {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: var(--surface-2);
  border-bottom: 1px solid var(--border-subtle);
}

.chat-mode-switch button {
  min-height: 36px;
  padding: 7px 14px;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font: inherit;
  font-size: var(--text-sm);
  font-weight: 650;
  cursor: pointer;
}

.chat-mode-switch button:hover,
.chat-mode-switch button.active {
  border-color: var(--border-default);
  background: var(--surface-4);
  color: var(--accent);
}

.chats-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.chats-sidebar {
  width: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-1);
  border-right: 1px solid var(--border-subtle);
  min-height: 0;
}

.chats-main {
  flex: 1;
  display: none;
  overflow: hidden;
  background: var(--surface-1);
  min-height: 0;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-tertiary);
}

.empty-icon {
  opacity: 0.5;
  color: var(--accent);
}

.empty-state p {
  font-size: 0.9375rem;
  margin: 0;
}

.mobile-back {
  display: none;
  position: fixed;
  top: 1rem;
  left: 1rem;
  z-index: calc(var(--z-navbar) + 6);
  width: 40px;
  height: 40px;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 50%;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow-sm-md);
  transition: all 0.2s;
}

.mobile-back:hover {
  background: var(--surface-4);
  color: var(--accent);
}

@media (min-width: 768px) {
  .chats-sidebar {
    width: 360px;
    min-width: 360px;
    min-height: 0;
  }

  .chats-main {
    display: flex;
    flex-direction: column;
  }

  .mobile-back {
    display: none;
  }
}

@media (max-width: 767px) {
  .chats-sidebar {
    width: 100%;
  }

  .chats-main {
    position: fixed;
    inset: 0;
    top: var(--viewport-top, 0px);
    bottom: auto;
    height: var(--viewport-height, 100dvh);
    z-index: calc(var(--z-navbar) + 5);
    background: var(--surface-1);
  }

  .has-active-chat .chats-main {
    display: flex;
    flex-direction: column;
  }

  .has-active-chat :deep(.chat-header) {
    padding-left: 4rem;
  }

  .mobile-back {
    display: flex;
    top: 0.5rem;
    left: 0.5rem;
  }
}
</style>
