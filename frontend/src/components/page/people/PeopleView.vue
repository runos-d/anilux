<template>
  <div class="people-page">
    <!-- Заголовок -->
    <div class="page-header">
      <h1 class="page-title">Люди</h1>
      <p class="page-subtitle">Пользователи</p>
    </div>

    <!-- Фильтры и поиск -->
    <div class="filters-section">
      <!-- Табы -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          @click="activeTab = tab.value"
          :class="['tab-btn', { active: activeTab === tab.value }]"
        >
          <span v-if="tab.value === 'online'" class="online-dot"></span>
          {{ tab.label }}
          <span v-if="tab.count !== undefined" class="tab-count">{{
            tab.count
          }}</span>
        </button>
      </div>

      <!-- Поиск + размер страницы -->
      <div class="search-section">
        <div class="search-input-wrap">
          <svg
            class="search-icon"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            type="text"
            placeholder="Поиск по имени..."
            class="search-input"
          />
          <button v-if="searchQuery" @click="clearSearch" class="search-clear">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        <select
          v-model="pageSize"
          class="page-size-select"
          @change="onPageSizeChange"
        >
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </div>
    </div>

    <!-- Загрузка -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton-grid">
        <div v-for="i in 12" :key="i" class="skeleton-card">
          <div class="skeleton-avatar"></div>
          <div class="skeleton-name"></div>
          <div class="skeleton-role"></div>
        </div>
      </div>
    </div>

    <div v-else-if="loadError" class="empty-state" role="alert">
      <SakuraIcon name="warning" :size="48" />
      <p>{{ loadError }}</p>
      <router-link v-if="needsLogin" to="/login" class="btn btn-primary">Войти</router-link>
      <button v-else class="btn btn-secondary" @click="fetchUsers">Повторить</button>
    </div>
    <!-- Сетка карточек -->
    <div v-else-if="users.length > 0" class="people-grid">
      <router-link
        v-for="user in users"
        :key="user.id"
        :to="getUserProfilePath(user)"
        class="person-card"
      >
        <div class="person-avatar">
          <img
            v-if="user.avatar_url"
            :src="user.avatar_url"
            :alt="getUserDisplayName(user)"
            class="avatar-image"
            @error="handleImageError"
          />
          <div v-else class="avatar-placeholder">
            {{ getUserDisplayName(user)[0]?.toUpperCase() }}
          </div>
          <span v-if="user.is_online" class="online-badge">онлайн</span>
        </div>
        <div class="person-info">
          <h3 class="person-name">{{ getUserDisplayName(user) }}</h3>
          <p
            v-if="user.nickname && user.nickname !== getUserDisplayName(user)"
            class="person-nickname"
          >
            @{{ user.nickname }}
          </p>
          <!-- <div class="user-stats">
            <span v-if="user.level" class="level-badge"
              >Ур. {{ user.level }}</span
            >
          </div> -->
          <!-- <p v-if="user.bio" class="person-bio">{{ truncateBio(user.bio) }}</p> -->
        </div>
      </router-link>
    </div>

    <!-- Пустое состояние -->
    <div v-else class="empty-state">
      <svg
        width="64"
        height="64"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
      <p>Пользователи не найдены</p>
    </div>

    <!-- Пагинация -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        @click="goToPage(currentPage - 1)"
        :disabled="currentPage === 1"
        class="pagination-btn"
      >
        Назад
      </button>

      <div class="page-numbers">
        <span
          v-for="page in visiblePages"
          :key="page"
          :class="['page-number', { active: page === currentPage }]"
          @click="goToPage(page)"
        >
          {{ page }}
        </span>
      </div>

      <button
        @click="goToPage(currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="pagination-btn"
      >
        Вперёд
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import usersApi, { type User } from "@/api/users";

const tabs = ref([
  { value: "all", label: "Все", count: undefined as number | undefined },
  { value: "online", label: "Онлайн", count: undefined as number | undefined },
]);

const activeTab = ref("all");
const searchQuery = ref("");
const users = ref<User[]>([]);
const isLoading = ref(false);
const loadError = ref('');
const needsLogin = ref(false);
const currentPage = ref(1);
const totalPages = ref(1);
const totalCount = ref(0);
const pageSize = ref(50);

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const visiblePages = computed(() => {
  const pages: number[] = [];
  const maxVisible = 5;

  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2));
  const end = Math.min(totalPages.value, start + maxVisible - 1);

  if (end - start + 1 < maxVisible) {
    start = Math.max(1, end - maxVisible + 1);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
});

const getUserDisplayName = (user: User): string => {
  return user.display_name || user.nickname || user.username;
};

const getUserProfilePath = (user: User): string => {
  const nickname = String(user.nickname || user.username || "").replace(/^@+/, "").trim();
  return nickname ? `/profile/@${encodeURIComponent(nickname)}` : "/people";
};

const truncateBio = (bio: string): string => {
  return bio.length > 60 ? bio.slice(0, 60) + "..." : bio;
};

const fetchUsers = async () => {
  isLoading.value = true;
  loadError.value = '';
  needsLogin.value = false;
  try {
    const params: Record<string, unknown> = {
      page: currentPage.value,
      page_size: pageSize.value,
    };

    if (activeTab.value === "online") {
      params.status = "online";
    } else if (activeTab.value === "offline") {
      params.status = "offline";
    }

    if (searchQuery.value) {
      params.search = searchQuery.value;
    }

    const response = await usersApi.getUsers(params);
    users.value = response.data.results || [];
    totalCount.value = response.data.count || 0;
    totalPages.value = Math.ceil(totalCount.value / pageSize.value);

    if (activeTab.value === "all" && tabs.value[0]) {
      tabs.value[0].count = totalCount.value;
    }
  } catch (error) {
    console.error("Error fetching users:", error);
    needsLogin.value = (error as { response?: { status?: number } }).response?.status === 401;
    loadError.value = needsLogin.value ? 'Войдите, чтобы посмотреть пользователей' : 'Не удалось загрузить пользователей';
    users.value = [];
  } finally {
    isLoading.value = false;
  }
};

const onPageSizeChange = () => {
  currentPage.value = 1;
  fetchUsers();
};

const goToPage = (page: number) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page;
    fetchUsers();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
};

const debouncedSearch = () => {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    currentPage.value = 1;
    fetchUsers();
  }, 300);
};

const clearSearch = () => {
  searchQuery.value = "";
  currentPage.value = 1;
  fetchUsers();
};

const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  img.style.display = "none";
};

watch(activeTab, () => {
  currentPage.value = 1;
  fetchUsers();
});

watch(pageSize, () => {
  currentPage.value = 1;
  fetchUsers();
});

onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.people-page {
  padding: 1.5rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* Заголовок */
.page-header {
  margin-bottom: 1.5rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
}

.page-subtitle {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Фильтры */
.filters-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
  align-items: center;
  justify-content: space-between;
}

.tabs {
  display: flex;
  gap: 0.25rem;
  background: var(--surface-4);
  padding: 0.25rem;
  border-radius: 0.5rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--accent);
  color: #fff;
}

.search-section {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.page-size-select {
  height: 38px;
  padding: 0 2.5rem 0 0.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--surface-3);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%239ca3af' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E") !important;
  background-repeat: no-repeat !important;
  background-position: right 1.25rem center !important;
  appearance: none !important;
  -webkit-appearance: none !important;
  outline: none;
  cursor: pointer;
  transition: all 0.2s;
}

.page-size-select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 0.875rem;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 280px;
  padding: 0.625rem 2.5rem 0.625rem 2.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: var(--text-primary);
  background: var(--surface-3);
  outline: none;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.search-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.search-clear {
  position: absolute;
  right: 0.5rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 50%;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.search-clear:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

/* Сетка */
.people-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.person-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.25rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.75rem;
  text-decoration: none;
  transition: all 0.2s;
}

.person-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  border-color: var(--accent);
}

.person-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: visible;
  margin-bottom: 0.75rem;
  background: var(--surface-4);
  position: relative;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #fff;
  font-size: 2rem;
  font-weight: 700;
  border-radius: 50%;
}

.online-badge {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.625rem;
  padding: 0.125rem 0.5rem;
  background: #22c55e;
  color: #fff;
  border-radius: 9999px;
  font-weight: 600;
  white-space: nowrap;
}

.person-info {
  text-align: center;
  width: 100%;
}

.person-name {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.person-nickname {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin: 0 0 0.5rem;
}

.user-stats {
  display: flex;
  gap: 0.25rem;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.level-badge {
  font-size: 0.6875rem;
  padding: 0.125rem 0.5rem;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #fff;
  border-radius: 9999px;
  font-weight: 600;
}

.person-bio {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin: 0;
  line-height: 1.4;
}

/* Онлайн точка в табе */
.online-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: #22c55e;
  border-radius: 50%;
  margin-right: 0.375rem;
}

.tab-count {
  font-size: 0.75rem;
  margin-left: 0.375rem;
  opacity: 0.7;
}

/* Загрузка */
.loading-state {
  padding: 1rem 0;
}

.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1rem;
}

.skeleton-card {
  padding: 1.25rem;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.75rem;
}

.skeleton-avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--surface-4);
  margin: 0 auto 0.75rem;
  animation: pulse 1.5s infinite;
}

.skeleton-name {
  height: 18px;
  width: 80%;
  background: var(--surface-4);
  border-radius: 4px;
  margin: 0 auto 0.5rem;
  animation: pulse 1.5s infinite;
}

.skeleton-role {
  height: 14px;
  width: 50%;
  background: var(--surface-4);
  border-radius: 4px;
  margin: 0 auto;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

/* Пустое состояние */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  color: var(--text-tertiary);
}

.empty-state p {
  margin: 1rem 0 0;
  font-size: 1rem;
}

/* Пагинация */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border-strong);
}

.pagination-btn {
  min-width: 36px;
  height: 36px;
  padding: 0 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.pagination-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.pagination-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.page-number {
  min-width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  font-weight: 500;
}

.page-number:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.page-number.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* Адаптивность */
@media (max-width: 768px) {
  .people-page {
    padding: 1rem;
  }

  .filters-section {
    flex-direction: column;
    align-items: stretch;
  }

  .tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .search-input-wrap {
    width: 100%;
  }

  .search-input {
    width: 100%;
  }

  .people-grid,
  .skeleton-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }

  .person-avatar {
    width: 80px;
    height: 80px;
  }
}
</style>
