<template>
  <div class="own-profile-view">
    <div class="profile-header" :class="{ 'has-cover': user.cover_image_url }">
      <div
        v-if="user.cover_image_url"
        class="header-background"
        :style="coverImageStyle"
      >
        <button class="cover-upload-btn" @click="openCoverEditor">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"
            />
            <circle cx="12" cy="13" r="4" />
          </svg>
          <span>Изменить обложку</span>
        </button>
      </div>

      <div class="header-content">
        <div class="avatar-section">
          <UserAvatar
            :src="user.avatar || user.avatar_url || '/img/default-avatar.svg'"
            :is-online="isOnline"
            size="2xl"
            shape="circle"
          />
        </div>

        <div class="user-info">
          <h1>
            {{ user.display_name || user.nickname || user.username }}
          </h1>
          <p class="username">
            @{{ user.nickname || user.username }}
          </p>
          <p class="bio">{{ user.bio || "Напишите что-то о себе..." }}</p>

          <div class="user-meta">
            <span v-if="user.experience" class="exp-badge"
              ><SakuraIcon name="sparkles" /> {{ user.experience }} опыта</span
            >
            <span v-if="user.created_at"
              >🗓 На сайте с {{ formatDate(user.created_at) }}</span
            >
          </div>
        </div>

        <div class="header-actions">
          <button @click="openSettings" class="btn-edit">
            <CogIcon class="w-5 h-5" />
            Настройки профиля
          </button>
          <button
            v-if="isAdmin"
            @click="router.push('/admin')"
            class="btn-admin"
          >
            🛡️ Админ
          </button>
        </div>

      </div>
    </div>
  </div>

  <ImageCropEditor
    v-model:open="coverEditorOpen"
    shape="rect"
    title="Изменить обложку"
    :initial-src="user.cover_image_url || undefined"
    :initial-x="user.cover_position_x ?? 50"
    :initial-y="user.cover_position_y ?? 50"
    @crop="handleCoverCrop"
  />

  <section class="notifications-section" style="padding:24px">
    <h2>Уведомления -подписки на серии</h2>
    <NotificationsTab />
  </section>
</template>

<script setup lang="ts">
import { useCachedReads } from '@/composables/useCachedReads';
const read = useCachedReads();
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { CogIcon } from "@heroicons/vue/24/outline";
import NotificationsTab from "@/components/Profile/NotificationsTab.vue";
import api from "@/api";
import ImageCropEditor from "@/components/modal/ImageCropEditor.vue";
import UserAvatar from "@/components/ui/UserAvatar.vue";

interface UserProfile {
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
}

interface UserStats {
  followers?: number;
  following?: number;
  posts?: number;
  playlists?: number;
  achievements?: number;
}

const router = useRouter();
const authStore = useAuthStore();

const user = ref<UserProfile>({});
const stats = ref<UserStats>({});
const isOnline = ref<boolean | undefined>(undefined);

const coverEditorOpen = ref(false);

const isAdmin = computed(() => {
  const u = authStore.user;
  if (!u) return false;
  return u.is_admin || u.is_staff;
});

const currentUser = computed(() => authStore.user);

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
  if (!currentUser.value?.id) return;
  try {
    const id = currentUser.value.id;
    await read(['profile', id], async () => (await api.get(`/users/profile/${id}/`)).data, data => {
      user.value = data; isOnline.value = data.is_online ?? undefined;
    });
  } catch (error) {
    console.error("Ошибка загрузки профиля:", error);
  }
};

const loadStats = async () => {
  if (!currentUser.value?.id) return;
  try {
    const id = currentUser.value.id;
    await read(['profile-stats', id], async () => (await api.get(`/users/${id}/stats/`)).data,
      data => { stats.value = data; });
  } catch (error) {
    console.error("Ошибка загрузки статистики:", error);
  }
};

const openSettings = () => {
  router.push("/settings");
};

const openCoverEditor = () => {
  coverEditorOpen.value = true;
};

const handleCoverCrop = async (payload: { file?: File; x: number; y: number }) => {
  const formData = new FormData();
  if (payload.file) {
    formData.append("cover_image", payload.file);
  }
  formData.append("cover_position_x", String(payload.x));
  formData.append("cover_position_y", String(payload.y));

  try {
    const response = await api.patch(`/users/profile/update/`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    user.value.cover_image_url = response.data.cover_image_url;
    user.value.cover_image = response.data.cover_image;
    user.value.cover_position_x = response.data.cover_position_x ?? payload.x;
    user.value.cover_position_y = response.data.cover_position_y ?? payload.y;
  } catch (error) {
    console.error("Ошибка загрузки обложки:", error);
    alert("Не удалось загрузить обложку");
  }
};

const formatDate = (date: string | Date | undefined) => {
  if (!date) return "";
  return new Date(date).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
};

onMounted(() => {
  if (currentUser.value?.id) {
    router.replace(`/profile/${currentUser.value.id}`);
    return;
  }
  loadProfile();
  loadStats();
});
</script>

<style scoped>
.own-profile-view {
  max-width: 1200px;
  margin: 0 auto;
  background-color: var(--surface-1);
  min-height: 100vh;
}

.profile-header {
  position: relative;
  margin-bottom: 20px;
}

.header-background {
  height: 280px;
  background-color: var(--surface-3);
  border-bottom: 1px solid var(--border-subtle);
  background-size: cover;
  background-position: center;
  position: relative;
}

.header-background::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.1) 0%,
    rgba(0, 0, 0, 0.4) 100%
  );
}

.cover-upload-btn {
  position: absolute;
  bottom: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
  z-index: 10;
}

.cover-upload-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}

.header-content {
  position: relative;
  padding: 0 24px 24px;
  margin-top: -80px;
}

/* Если нет обложки - аватар не накладывается */
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
  max-width: 600px;
}

.user-info h1 {
  margin: 0 0 4px;
  font-size: 28px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  margin: 0 0 4px;
  color: var(--text-secondary);
  font-size: 16px;
}

.nickname {
  margin: 0 0 8px;
  color: var(--accent);
  font-size: 14px;
  font-weight: 500;
}

.bio {
  margin: 0 0 12px;
  color: var(--text-secondary);
  line-height: 1.6;
  font-style: italic;
}

.user-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--text-tertiary);
  font-size: 14px;
  align-items: center;
}

.level-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 20px;
  font-weight: 600;
}

.exp-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  background: var(--surface-3);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.btn-admin {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid #ef4444;
  border-radius: var(--radius-button);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-admin:hover {
  background: rgba(239, 68, 68, 0.25);
}

.btn-edit,
.btn-settings {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--accent);
  color: var(--text-primary);
  border: none;
  border-radius: var(--radius-button);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-edit:hover,
.btn-settings:hover {
  background: var(--accent-hover);
}

.stats {
  display: flex;
  gap: 32px;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--border-subtle);
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: var(--text-primary);
}

.stat-label {
  font-size: 13px;
  color: var(--text-tertiary);
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

.profile-content {
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

  .stats {
    gap: 16px;
  }

  .stat-value {
    font-size: 20px;
  }

  .header-actions {
    flex-wrap: wrap;
  }
}
</style>
