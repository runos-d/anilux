<template>
  <div class="user-profile-view">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <div v-else-if="!user.id" class="not-found">
      <h2><SakuraIcon name="user" /> Пользователь не найден</h2>
      <p>Пользователь с таким никнеймом не существует или был удалён.</p>
      <button @click="goToFeed" class="btn-back">Вернуться в ленту</button>
    </div>

    <div v-else class="profile-content">
      <div
        class="profile-header"
        :class="{ 'has-cover': user.cover_image_url }"
      >
        <div
          v-if="user.cover_image_url"
          class="header-background"
          :style="coverImageStyle"
        ></div>

        <div class="header-content">
          <div class="avatar-section">
            <UserAvatar
              :src="user.avatar || user.avatar_url || '/img/default-avatar.svg'"
              :is-online="isUserOnline(userId)"
              size="2xl"
              shape="circle"
            />
          </div>

          <div class="user-info">
            <h1>
              {{ seoPage?.status === 200 ? seoPage.h1 : (user.display_name || user.nickname || user.username) }}
            </h1>
            <p class="username">
              @{{ user.nickname || user.username }}
            </p>

            <div
              v-if="user.bio"
              class="bio bio--md"
              v-html="bioMarkdown"
            ></div>
            <p v-else class="bio bio--empty">
              Пользователь пока ничего не написал о себе
            </p>
          </div>

          <div class="header-actions">
            <button
              v-if="!isOwnProfile && !isFollowing"
              @click="toggleFollow"
              class="btn-follow"
            >
              Подписаться
            </button>
            <button
              v-if="!isOwnProfile && isFollowing"
              @click="toggleFollow"
              class="btn-unfollow"
            >
              <SakuraIcon name="check" :size="16" /> Подписан
            </button>
            <button v-if="!isOwnProfile" @click="openChat" class="btn-message">
              <ChatBubbleLeftIcon class="w-5 h-5" />
              Написать
            </button>
            <!-- <button v-if="!isOwnProfile" @click="reportUser" class="btn-report">
              <SakuraIcon name="flag" :size="18" />
              Пожаловаться
            </button> -->
          </div>
        </div>
      </div>

      <div class="profile-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
        >
          {{ tab.name }}
        </button>
      </div>

      <div class="tab-content-container">
        <div v-if="activeTab === 'feed'" class="tab-content">
          <UserFeed :user-id="userId" />
        </div>

        <div v-if="activeTab === 'anime'" class="tab-content">
          <UserAnimeCollection :user-id="userId" />
        </div>

        <div v-if="activeTab === 'stats'" class="tab-content">
          <UserStatsView :user-id="userId" embedded />
        </div>

        <div v-if="activeTab === 'playlists'" class="tab-content">
          <UserPublicPlaylists :user-id="userId" />
        </div>

        <div v-if="activeTab === 'social'" class="tab-content">
          <UserSocialNetworks :user="user as User" />
        </div>

        <div v-if="activeTab === 'favorites'" class="tab-content">
          <UserFavorites :user-id="userId" />
        </div>

        <div v-if="activeTab === 'achievements'" class="tab-content">
          <UserAchievements :user-id="userId" />
        </div>

        <div v-if="activeTab === 'about'" class="tab-content">
          <ProfileAbout :user="user as User" />
        </div>
      </div>
    </div>
    <ReportModal
      v-if="showUserReport"
      content-type="user"
      :content-id="userId"
      @close="showUserReport = false"
    />
  </div>
</template>

<script setup lang="ts">
import { seoPage } from '@/composables/useSeo';
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { isRequestCancelled } from "@/api/client";
import { useCachedReads } from '@/composables/useCachedReads';
const read = useCachedReads();
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useOnlineStatus } from "@/composables/useOnlineStatus";
import { useSafeMarkdown } from "@/composables/useSafeMarkdown";
import { ChatBubbleLeftIcon } from "@heroicons/vue/24/outline";
import UserFeed from "@/components/Profile/UserFeed.vue";
import UserAnimeCollection from "@/components/Profile/UserAnimeCollection.vue";
import UserPublicPlaylists from "@/components/Profile/UserPublicPlaylists.vue";
import UserSocialNetworks from "@/components/Profile/UserSocialNetworks.vue";
import UserFavorites from "@/components/Profile/UserFavorites.vue";
import UserAchievements from "@/components/Profile/UserAchievements.vue";
import ProfileAbout from "@/components/Profile/ProfileAbout.vue";
import UserStatsView from "@/components/page/profile/UserStatsView.vue";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import UserAvatar from "@/components/ui/UserAvatar.vue";
import ReportModal from "@/components/feed/ReportModal.vue";
import { useModalStore } from "@/stores/modal";
import api from "@/api";
import type { User } from "@/types";

interface UserProfile {
  id?: number;
  avatar?: string;
  avatar_url?: string;
  display_name?: string;
  nickname?: string;
  username?: string;
  bio?: string;
  experience?: number;
  created_at?: string;
  cover_image_url?: string;
  cover_image?: string;
  cover_position_x?: number;
  cover_position_y?: number;
  is_online?: boolean;
}

interface UserStats {
  followers?: number;
  following?: number;
  posts?: number;
  playlists?: number;
  achievements?: number;
}

const props = defineProps<{
  id?: string | number | null;
  nickname?: string | null;
}>();

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const modalStore = useModalStore();
const { isUserOnline } = useOnlineStatus();

const routeId = String(props.id ?? route.params.id ?? "");
const userId = ref<number>(NaN);
const user = ref<UserProfile>({});
const stats = ref<UserStats>({});
const isFollowing = ref(false);
const activeTab = ref("stats");
const loading = ref(true);
const showUserReport = ref(false);

const bioMarkdown = useSafeMarkdown(
  computed(() => user.value.bio || ""),
);

const tabs = computed(() => {
  const baseTabs = [
    { id: "stats", name: "Статистика" },
    { id: "anime", name: "Аниме" },
    { id: "playlists", name: "Плейлисты" },
    { id: "favorites", name: "Избранное" },
    { id: "achievements", name: "Достижения" },
  ];
  return baseTabs;
});

const currentUser = computed(() => authStore.user);

const isOwnProfile = computed(() => {
  if (!currentUser.value || !userId.value || isNaN(userId.value)) return false;
  return currentUser.value.id === userId.value;
});

const coverImageStyle = computed(() => {
  if (user.value.cover_image_url) {
    const positionX = user.value.cover_position_x ?? 50;
    const positionY = user.value.cover_position_y ?? 50;
    return {
      backgroundImage: `url(${user.value.cover_image_url})`,
      backgroundSize: "cover",
      backgroundPosition: `${positionX}% ${positionY}%`,
    };
  }
  return {};
});

const loadProfile = async () => {
  loading.value = true;
  try {
    await read(['profile', props.nickname || routeId], async () => {
    let response;

    if (props.nickname) {
      const nick = props.nickname.replace(/^@/, "");
      const resp = await api.get(`/users/by-nickname/@${nick}/`);
      return resp.data;
    }

    const isNumericId = /^\d+$/.test(String(routeId));
    if (isNumericId) {
      response = await api.get(`/users/profile/${routeId}/`);
    } else {
      const nickname = routeId.replace(/^@+/, "");
      try {
        response = await api.get(
          `/users/by-nickname/@${encodeURIComponent(nickname)}/`,
        );
      } catch {
        response = await api.get(
          `/users/search/?q=${encodeURIComponent(nickname)}&exact=true`,
        );
        if (response.data?.results?.length) {
          response = await api.get(`/users/profile/${response.data.results[0].id}/`);
        } else {
          throw new Error("Пользователь не найден");
        }
      }
    }
    return response.data;
    }, data => { user.value = data; userId.value = data.id; });
  } catch (error) {
    console.error("Ошибка загрузки профиля:", error);
    user.value = {};
  } finally {
    loading.value = false;
  }
};

const loadStats = async () => {
  if (!userId.value || isNaN(userId.value)) return;
  try {
    const id = userId.value;
    await read(['profile-stats', id], async () => (await api.get(`/users/${id}/stats/`)).data,
      data => { stats.value = data; });
  } catch (error) {
    if (!isRequestCancelled(error)) console.error("Ошибка загрузки статистики:", error);
  }
};

const loadFollowStatus = async () => {
  if (!authStore.isAuthenticated || !userId.value || isNaN(userId.value))
    return;

  try {
    const response = await api.get(
      `/social/follows/check/?following_id=${userId.value}`,
    );
    isFollowing.value = response.data.is_following ?? response.data.following;
  } catch (error) {
    if (!isRequestCancelled(error)) console.error("Ошибка загрузки статуса:", error);
  }
};

const toggleFollow = async () => {
  if (!authStore.isAuthenticated) {
    alert("Для подписки необходимо войти в аккаунт");
    return;
  }
  try {
    const response = await api.post(`/social/follow/toggle/${userId.value}/`);
    isFollowing.value = response.data.following;
    stats.value.followers =
      response.data.followers_count || stats.value.followers;
  } catch (error) {
    console.error("Ошибка подписки:", error);
    alert("Не удалось выполнить подписку");
  }
};

const openChat = async () => {
  if (!authStore.isAuthenticated) {
    alert("Для отправки сообщения необходимо войти в аккаунт");
    return;
  }
  try {
    const response = await api.post("/social/private-chats/", {
      user2: userId.value,
    });
    router.push(`/chats/${response.data.id}`);
  } catch (error) {
    console.error("Ошибка создания чата:", error);
    alert("Не удалось создать чат");
  }
};

const reportUser = () => {
  if (!authStore.isAuthenticated) {
    modalStore.openAuthModal();
    return;
  }
  showUserReport.value = true;
};

const handleCoverUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("cover_image", file);

  try {
    const response = await api.patch(`/users/profile/update/`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    user.value.cover_image_url = response.data.cover_image_url;
    user.value.cover_image = response.data.cover_image;
  } catch (error) {
    console.error("Ошибка загрузки обложки:", error);
    alert("Не удалось загрузить обложку");
  }
};

const goToFeed = () => {
  router.push("/feed");
};

const formatDate = (date: string | Date | undefined) => {
  if (!date) return "";
  return new Date(date).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

onMounted(async () => {
  await loadProfile();
  loadStats();
  loadFollowStatus();
});
</script>

<style scoped>
.user-profile-view {
  max-width: 1200px;
  margin: 0 auto;
  background-color: var(--surface-1);
  min-height: 100vh;
}

.loading,
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 40px;
}

.not-found h2 {
  font-size: 32px;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.not-found p {
  color: var(--text-secondary);
  margin: 0 0 24px;
}

.btn-back {
  padding: 12px 24px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-back:hover {
  background: var(--accent-hover);
}

.profile-header {
  position: relative;
  margin-bottom: -10px;
}

.header-background {
  height: 280px;
  min-height: 280px;
  background-color: transparent;
  border-bottom: 1px solid var(--border-subtle);
  background-size: cover;
  border-radius: 15px;
  background-position: center;
  position: relative;
}

.header-content {
  position: relative;
  padding: 0 24px 24px;
  margin-top: -80px;
}

.profile-header:not(.has-cover) .header-content {
  margin-top: 24px;
}

.profile-header.has-cover .header-content {
  margin-top: -80px;
}

.avatar-section {
  position: relative;
  display: inline-block;
}

.user-info {
  margin-top: 16px;
  max-width: 640px;
  min-width: 0;
  width: 100%;
}

.user-info h1 {
  margin: 0 0 4px;
  font-size: 28px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.username {
  margin: 0 0 4px;
  color: var(--text-secondary);
  font-size: 16px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.bio {
  margin: 12px 0 0;
  padding: 14px 16px;
  color: var(--text-secondary);
  line-height: 1.65;
  font-size: 14px;
  max-width: 100%;
  overflow-wrap: anywhere;
  word-break: break-word;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  position: relative;
}

.bio--md {
  border-left: 3px solid var(--accent);
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
}

.bio--empty {
  color: var(--text-tertiary);
  font-style: italic;
  background: transparent;
  border: 1px dashed var(--border-subtle);
  border-left: 1px dashed var(--border-subtle);
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
}

.bio--md :deep(p) {
  margin: 0 0 8px;
}
.bio--md :deep(p:last-child) {
  margin-bottom: 0;
}

.bio--md :deep(strong) {
  color: var(--text-primary);
  font-weight: 600;
}

.bio--md :deep(em) {
  color: var(--text-primary);
  font-style: italic;
}

.bio--md :deep(a) {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
  transition: color 0.15s ease, border-color 0.15s ease;
}
.bio--md :deep(a:hover) {
  color: var(--accent-hover);
  border-bottom-color: var(--accent-hover);
}

.bio--md :deep(code) {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 0.9em;
  background: var(--surface-4);
  color: var(--text-primary);
  padding: 2px 6px;
  border-radius: 5px;
}

.bio--md :deep(pre) {
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 0.85em;
  line-height: 1.5;
  margin: 8px 0;
}
.bio--md :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: inherit;
}

.bio--md :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 12px;
  border-left: 3px solid var(--accent);
  background: var(--surface-4);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
  font-style: italic;
}

.bio--md :deep(ul),
.bio--md :deep(ol) {
  margin: 6px 0;
  padding-left: 22px;
}
.bio--md :deep(li) {
  margin: 2px 0;
}

.bio--md :deep(h1),
.bio--md :deep(h2),
.bio--md :deep(h3),
.bio--md :deep(h4),
.bio--md :deep(h5),
.bio--md :deep(h6) {
  color: var(--text-primary);
  font-weight: 700;
  line-height: 1.3;
  margin: 12px 0 6px;
}
.bio--md :deep(h1) { font-size: 1.25em; }
.bio--md :deep(h2) { font-size: 1.15em; }
.bio--md :deep(h3) { font-size: 1.05em; }
.bio--md :deep(h4),
.bio--md :deep(h5),
.bio--md :deep(h6) { font-size: 1em; }

.bio--md :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 12px 0;
}

.bio--md :deep(del),
.bio--md :deep(s) {
  opacity: 0.6;
  text-decoration: line-through;
}

.bio--md :deep(img) {
  max-width: 100%;
  border-radius: 10px;
}

.header-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.btn-follow {
  padding: 10px 24px;
  background: var(--accent);
  color: var(--text-on-accent);
  border: none;
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-follow:hover {
  background: var(--accent-hover);
}

.btn-unfollow {
  padding: 10px 24px;
  background: var(--surface-3);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-unfollow:hover {
  background: var(--surface-4);
}

.btn-message,
.btn-report {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-button);
  cursor: pointer;
  transition: background 0.15s ease;
  color: var(--text-secondary);
}

.btn-message:hover,
.btn-report:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.profile-tabs {
  display: flex;
  gap: 8px;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-subtle);
  overflow-x: auto;
}

.tab-btn {
  padding: 14px 20px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.15s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
}

.tab-content-container {
  padding: 24px;
}

.tab-content {
  min-height: 400px;
}

@media (max-width: 768px) {
  .header-background {
    height: 180px;
  }

  .header-content {
    padding: 0 16px 16px;
  }

  .user-info h1 {
    font-size: 24px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
