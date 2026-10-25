<template>
  <div class="achievements-page">
    <div class="page-header">
      <h1>Достижения {{ username ? `@${username}` : "" }}</h1>
      <div class="stats">
        <div class="stat-item">
          <span class="stat-value">{{ unlockedCount }}</span>
          <span class="stat-label">Получено</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ totalCount }}</span>
          <span class="stat-label">Всего</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ progressPercentage }}%</span>
          <span class="stat-label">Прогресс</span>
        </div>
      </div>
    </div>

    <div class="tabs">
      <button
        @click="activeTab = 'all'"
        :class="['tab-btn', { active: activeTab === 'all' }]"
      >
        Все
      </button>
      <button
        @click="activeTab = 'unlocked'"
        :class="['tab-btn', { active: activeTab === 'unlocked' }]"
      >
        Полученные
        <!-- <span class="badge">{{ unlockedCount }}</span> -->
      </button>
      <button
        @click="activeTab = 'in_progress'"
        :class="['tab-btn', { active: activeTab === 'in_progress' }]"
      >
        В процессе
        <!-- <span class="badge">{{ inProgressCount }}</span> -->
      </button>
    </div>

    <div class="category-filter">
      <select v-model="selectedCategory" class="category-select">
        <option value="">Все категории</option>
        <option value="basic">Основные</option>
        <option value="social">Социальные</option>
        <option value="collection">Коллекционные</option>
        <option value="contest">Конкурсные</option>
        <option value="special">Специальные</option>
      </select>
    </div>

    <div v-if="!loading" class="achievements-list">
      <div
        v-for="category in groupedAchievements"
        :key="category.name"
        class="category-group"
      >
        <h2 class="category-title">{{ category.name }}</h2>
        <div class="achievements-grid">
          <div
            v-for="achievement in category.achievements"
            :key="achievement.id"
            :class="[
              'achievement-card',
              {
                unlocked: achievement.is_unlocked,
                locked: !achievement.is_unlocked,
              },
            ]"
            @click="openAchievementDetail(achievement)"
          >
            <div class="icon">
              <SakuraIcon
                :name="achievement.achievement.icon_svg || 'trophy'"
                :size="80"
                :color="getIconColor(achievement.achievement.level)"
              />
              <div :class="['level-badge', achievement.achievement.level]">
                <SakuraIcon :name="getLevelIcon(achievement.achievement.level)" :size="16" />
              </div>
            </div>
            <div class="info">
              <h3>{{ achievement.achievement.name }}</h3>
              <p>{{ achievement.achievement.description }}</p>
              <div class="progress">
                <div class="progress-bar">
                  <div
                    class="progress-fill"
                    :style="{ width: achievement.progress_percentage + '%' }"
                  ></div>
                </div>
                <span class="progress-text">
                  {{ achievement.progress }}/{{
                    achievement.achievement.condition_value
                  }}
                </span>
              </div>
              <div v-if="achievement.is_unlocked" class="unlocked-date">
                Получено: {{ formatDate(achievement.unlocked_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <div v-if="!loading && filteredAchievements.length === 0" class="empty">
      <p>Достижения не найдены</p>
    </div>

    <Modal v-if="selectedAchievement" :model-value="true" @close="selectedAchievement = null">
      <div class="achievement-detail">
        <div class="detail-header">
          <div class="icon-large">
            <SakuraIcon
              :name="selectedAchievement.achievement.icon_svg || 'trophy'"
              :size="120"
              :color="getIconColor(selectedAchievement.achievement.level)"
            />
            <div
              :class="['level-badge', selectedAchievement.achievement.level]"
            >
              <SakuraIcon :name="getLevelIcon(selectedAchievement.achievement.level)" :size="16" />
            </div>
          </div>
          <div class="header-info">
            <h2>{{ selectedAchievement.achievement.name }}</h2>
            <p class="category">
              {{ getCategoryName(selectedAchievement.achievement.category) }}
            </p>
          </div>
        </div>
        <div class="detail-content">
          <p class="description">
            {{ selectedAchievement.achievement.description }}
          </p>

          <div class="condition">
            <h3>Условие получения</h3>
            <p>{{ getConditionText(selectedAchievement.achievement) }}</p>
          </div>

          <div class="progress-section">
            <h3>Прогресс</h3>
            <div class="progress-bar-large">
              <div
                class="progress-fill"
                :style="{
                  width: selectedAchievement.progress_percentage + '%',
                }"
              ></div>
            </div>
            <p class="progress-text">
              {{ selectedAchievement.progress }} /
              {{ selectedAchievement.achievement.condition_value }} ({{
                selectedAchievement.progress_percentage
              }}%)
            </p>
          </div>

          <div v-if="selectedAchievement.is_unlocked" class="unlocked-info">
            <h3>Получено</h3>
            <p>{{ formatDate(selectedAchievement.unlocked_at) }}</p>
          </div>

          <div class="stats">
            <h3>Статистика</h3>
            <p>
              Получили:
              {{ selectedAchievement.achievement.unlocked_count }} пользователей
            </p>
          </div>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import Modal from "@/components/ui/Modal.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import api from "@/api";
import { collectionRows } from '@/lib/collectionRows';

const route = useRoute();

const username = ref(route.params.username || "");
const activeTab = ref("all");
const selectedCategory = ref("");
const loading = ref(false);

interface AchievementDetail {
  id: number;
  name: string;
  description: string;
  icon_url?: string;
  icon_svg?: string;
  level: string;
  category: string;
  condition_type: string;
  condition_value: number;
  unlocked_count?: number;
}

interface Achievement {
  id: number;
  is_unlocked: boolean;
  progress: number;
  progress_percentage: number;
  unlocked_at?: string | null;
  achievement: AchievementDetail;
}

const achievements = ref<Achievement[]>([]);
const selectedAchievement = ref<Achievement | null>(null);

const categoryNames: Record<string, string> = {
  basic: "Основные",
  social: "Социальные",
  collection: "Коллекционные",
  contest: "Конкурсные",
  special: "Специальные",
};

const levelIcons: Record<string, string> = {
  bronze: "medal",
  silver: "medal",
  gold: "medal",
  legendary: "crown",
};

const filteredAchievements = computed(() => {
  let result = achievements.value;

  if (activeTab.value === "unlocked") {
    result = result.filter((a) => a.is_unlocked);
  } else if (activeTab.value === "in_progress") {
    result = result.filter((a) => !a.is_unlocked && a.progress > 0);
  }

  if (selectedCategory.value) {
    result = result.filter(
      (a) => a.achievement.category === selectedCategory.value,
    );
  }

  return result;
});

const groupedAchievements = computed(() => {
  const groups: Record<string, { name: string; achievements: Achievement[] }> =
    {};
  filteredAchievements.value.forEach((achievement) => {
    const category = achievement.achievement.category;
    if (!groups[category]) {
      groups[category] = {
        name: categoryNames[category] || category,
        achievements: [],
      };
    }
    groups[category].achievements.push(achievement);
  });

  return Object.values(groups);
});

const unlockedCount = computed(() => {
  return achievements.value.filter((a) => a.is_unlocked).length;
});

const inProgressCount = computed(() => {
  return achievements.value.filter((a) => !a.is_unlocked && a.progress > 0)
    .length;
});

const totalCount = computed(() => {
  return achievements.value.length;
});

const progressPercentage = computed(() => {
  if (totalCount.value === 0) return 0;
  return Math.round((unlockedCount.value / totalCount.value) * 100);
});

const loadAchievements = async () => {
  loading.value = true;
  try {
    const params: Record<string, unknown> = {};
    if (username.value) {
      const userResponse = await api.get(
        `/users/search/?search=${username.value}`,
      );
      if (userResponse.data.length > 0) {
        params.user_id = userResponse.data[0].id;
      }
    }

    const response = await api.get("/social/user-achievements/all/", {
      params,
    });
    achievements.value = collectionRows(response.data);
  } catch (error) {
    console.error("Ошибка загрузки достижений:", error);
  } finally {
    loading.value = false;
  }
};

const getLevelIcon = (level: string) => {
  return levelIcons[level] || "medal";
};

const getCategoryName = (category: string) => {
  return categoryNames[category] || category;
};

const getConditionText = (achievement: AchievementDetail) => {
  const conditionTexts: Record<string, string> = {
    posts_count: `Создать ${achievement.condition_value} постов`,
    followers_count: `Получить ${achievement.condition_value} подписчиков`,
    following_count: `Подписаться на ${achievement.condition_value} пользователей`,
    likes_received: `Получить ${achievement.condition_value} лайков`,
    reposts_count: `Сделать ${achievement.condition_value} репостов`,
    reposts_received: `Получить ${achievement.condition_value} репостов`,
    comments_count: `Оставить ${achievement.condition_value} комментариев`,
    comments_social: `Написать ${achievement.condition_value} комментариев в ленте`,
    likes_given: `Поставить ${achievement.condition_value} лайков`,
    registration_days: `Быть на сайте ${achievement.condition_value} дней`,
    profile_completed: `Заполнить профиль на ${achievement.condition_value}%`,
    anime_watched: `Посмотреть ${achievement.condition_value} аниме полностью`,
    anime_watched_episodes: `Просмотреть ${achievement.condition_value} эпизодов`,
    anime_favorites: `Добавить ${achievement.condition_value} аниме в избранное`,
    anime_rated: `Поставить оценку ${achievement.condition_value} аниме`,
    anime_rewatched: `Пересмотреть ${achievement.condition_value} аниме`,
    anime_started: `Добавить ${achievement.condition_value} аниме в коллекцию`,
    anime_watching_now: `Смотреть одновременно ${achievement.condition_value} аниме`,
    anime_on_hold: `Отложить ${achievement.condition_value} аниме`,
    anime_dropped: `Бросить просмотр ${achievement.condition_value} аниме`,
    anime_planned: `Добавить ${achievement.condition_value} аниме в планы`,
    top_ratings: `Поставить оценку 9+ ${achievement.condition_value} аниме`,
    movies_watched: `Посмотреть ${achievement.condition_value} фильмов`,
    ova_watched: `Посмотреть ${achievement.condition_value} OVA`,
    anime_comments: `Написать ${achievement.condition_value} комментариев к аниме`,
    genres_explored: `Посмотреть аниме из ${achievement.condition_value} разных жанров`,
    studios_explored: `Посмотреть аниме ${achievement.condition_value} разных студий`,
    franchise_completed: `Полностью просмотреть ${achievement.condition_value} франшиз`,
    episodes_single_day: `Посмотреть ${achievement.condition_value}+ эпизодов за один день`,
    watch_days: `Смотреть аниме ${achievement.condition_value} дней`,
    hours_watched: `Провести ${achievement.condition_value} часов за просмотром`,
    night_owl_days: `Смотреть аниме ночью ${achievement.condition_value} дней`,
    evening_days: `Смотреть аниме вечером ${achievement.condition_value} дней`,
    morning_days: `Смотреть аниме утром ${achievement.condition_value} дней`,
    playlists_created: `Создать ${achievement.condition_value} плейлистов`,
    playlist_items_added: `Добавить ${achievement.condition_value} элементов в плейлисты`,
  };
  return (
    conditionTexts[achievement.condition_type] || achievement.condition_type
  );
};

const getIconColor = (level: string) => {
  return (
    { bronze: "#cd7f32", silver: "#c0c0c0", gold: "#ffd700", legendary: "#9b59b6" }[
      level
    ] || "var(--text-secondary)"
  );
};

const formatDate = (date?: string | null) => {
  if (!date) return "";
  return new Date(date).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
};

const openAchievementDetail = (achievement: Achievement) => {
  selectedAchievement.value = achievement;
};

onMounted(() => {
  loadAchievements();
});
</script>

<style scoped>
.achievements-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: var(--text-primary);
}

.stats {
  display: flex;
  gap: 30px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: var(--accent);
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle);
  padding-bottom: 10px;
}

.tab-btn {
  padding: 10px 20px;
  border: none;
  background: transparent;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.15s ease;
  color: var(--text-secondary);
}

.tab-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.tab-btn.active {
  background: var(--accent);
  color: var(--text-on-accent);
}

.badge {
  background: var(--surface-4);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  margin-left: 5px;
}

.category-filter {
  margin-bottom: 20px;
}

.category-select {
  padding: 10px 16px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-button);
  font-size: 14px;
  background: var(--surface-3);
  color: var(--text-primary);
}

.category-group {
  margin-bottom: 40px;
}

.category-title {
  font-size: 20px;
  margin-bottom: 20px;
  color: var(--text-primary);
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.achievement-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  background: var(--surface-3);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-sm-card);
  cursor: pointer;
  transition: all 0.15s ease;
}

.achievement-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-sm-card-hover);
}

.achievement-card.locked {
  opacity: 0.6;
  filter: grayscale(0.5);
}

.achievement-card.unlocked {
  border: 2px solid var(--accent-orange);
}

.icon {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.icon img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.level-badge {
  position: absolute;
  bottom: -5px;
  right: -5px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 16px;
  background: var(--surface-3);
  box-shadow: var(--shadow-sm-card);
}

.level-badge.bronze {
  border: 2px solid #cd7f32;
}
.level-badge.silver {
  border: 2px solid #c0c0c0;
}
.level-badge.gold {
  border: 2px solid #ffd700;
}
.level-badge.legendary {
  border: 2px solid #9b59b6;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.info {
  flex: 1;
}

.info h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--text-primary);
}

.info p {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.progress {
  margin-bottom: 12px;
}

.progress-bar {
  height: 6px;
  background: var(--surface-1);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 12px;
  color: var(--text-tertiary);
}

.unlocked-date {
  font-size: 11px;
  color: var(--accent-2);
  font-weight: bold;
}

.loading,
.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-tertiary);
}

.achievement-detail {
  padding: 30px;
  max-width: 600px;
}

.detail-header {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.icon-large {
  position: relative;
  width: 120px;
  height: 120px;
  flex-shrink: 0;
}

.icon-large > :deep(svg) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.icon-large .level-badge {
  width: 48px;
  height: 48px;
  font-size: 24px;
}

.header-info h2 {
  margin: 0 0 8px;
  font-size: 24px;
  color: var(--text-primary);
}

.header-info { min-width: 0; }

.category {
  margin: 0;
  color: var(--text-tertiary);
}

.detail-content > * {
  margin-bottom: 24px;
}

.detail-content h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: var(--text-primary);
}

.description {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.condition p {
  font-size: 14px;
  color: var(--text-secondary);
}

.progress-bar-large {
  height: 12px;
  background: var(--surface-1);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar-large .progress-fill {
  height: 100%;
}

.progress-section .progress-text {
  font-size: 14px;
}

.unlocked-info p {
  font-size: 14px;
  color: var(--accent-2);
}

.stats p {
  font-size: 14px;
  color: var(--text-secondary);
}

@media (max-width: 900px) and (min-width: 601px) {
  .achievements-page {
    padding: 18px;
    max-width: 100%;
  }
  .page-header {
    margin-bottom: 24px;
    gap: 16px;
  }
  .page-header h1 {
    font-size: 24px;
  }
  .stats {
    gap: 22px;
  }
  .stat-value {
    font-size: 24px;
  }
  .stat-label {
    font-size: 11px;
  }
  .tabs {
    gap: 8px;
    margin-bottom: 16px;
  }
  .tab-btn {
    padding: 8px 16px;
    font-size: 13px;
  }
  .category-filter {
    margin-bottom: 16px;
  }
  .category-select {
    padding: 9px 14px;
    font-size: 13px;
  }
  .category-group {
    margin-bottom: 30px;
  }
  .category-title {
    font-size: 18px;
    margin-bottom: 16px;
  }
  .achievements-grid {
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 16px;
  }
  .achievement-card {
    padding: 16px;
    gap: 14px;
  }
  .icon {
    width: 68px;
    height: 68px;
  }
  .level-badge {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }
  .info h3 {
    font-size: 15px;
  }
  .info p {
    font-size: 12px;
  }
  .achievement-detail {
    padding: 24px;
    max-width: 100%;
  }
  .icon-large {
    width: 100px;
    height: 100px;
  }
  .icon-large .level-badge {
    width: 42px;
    height: 42px;
    font-size: 20px;
  }
  .header-info h2 {
    font-size: 20px;
  }
}

@media (max-width: 600px) {
  .achievements-page {
    padding: 14px;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 20px;
    gap: 14px;
  }
  .page-header h1 {
    font-size: 20px;
  }
  .stats {
    width: 100%;
    justify-content: space-between;
    gap: 10px;
  }
  .stat-item {
    flex: 1;
  }
  .stat-value {
    font-size: 20px;
  }
  .stat-label {
    font-size: 11px;
  }
  .tabs {
    gap: 6px;
    margin-bottom: 14px;
    padding-bottom: 8px;
    overflow-x: auto;
    flex-wrap: nowrap;
  }
  .tab-btn {
    padding: 8px 14px;
    font-size: 13px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .category-filter {
    margin-bottom: 14px;
  }
  .category-select {
    width: 100%;
    padding: 9px 12px;
    font-size: 13px;
  }
  .category-group {
    margin-bottom: 24px;
  }
  .category-title {
    font-size: 17px;
    margin-bottom: 12px;
  }
  .achievements-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  .achievement-card {
    padding: 14px;
    gap: 12px;
    border-radius: 12px;
  }
  .achievement-card:hover {
    transform: none;
  }
  .icon {
    width: 60px;
    height: 60px;
  }
  .level-badge {
    width: 26px;
    height: 26px;
    font-size: 13px;
    bottom: -3px;
    right: -3px;
  }
  .info h3 {
    font-size: 14px;
    margin-bottom: 5px;
  }
  .info p {
    font-size: 12px;
    margin-bottom: 10px;
  }
  .progress-bar {
    height: 5px;
  }
  .progress-text {
    font-size: 11px;
  }
  .unlocked-date {
    font-size: 10px;
  }
  .loading,
  .empty {
    padding: 40px 14px;
  }
  .achievement-detail {
    padding: 18px;
    max-width: 100%;
  }
  .detail-header {
    gap: 14px;
    margin-bottom: 20px;
  }
  .icon-large {
    width: 80px;
    height: 80px;
  }
  .icon-large .level-badge {
    width: 34px;
    height: 34px;
    font-size: 16px;
  }
  .header-info h2 {
    font-size: 18px;
    margin-bottom: 5px;
  }
  .category {
    font-size: 13px;
  }
  .detail-content > * {
    margin-bottom: 18px;
  }
  .detail-content h3 {
    font-size: 14px;
    margin-bottom: 6px;
  }
  .description,
  .condition p,
  .progress-section .progress-text,
  .unlocked-info p,
  .stats p {
    font-size: 13px;
  }
  .progress-bar-large {
    height: 10px;
    margin-bottom: 6px;
  }
}

@media (max-width: 380px) {
  .achievements-page {
    padding: 10px;
  }
  .page-header h1 {
    font-size: 18px;
  }
  .stat-value {
    font-size: 18px;
  }
  .stat-label {
    font-size: 10px;
  }
  .tab-btn {
    padding: 7px 12px;
    font-size: 12px;
  }
  .category-title {
    font-size: 15px;
  }
  .achievement-card {
    padding: 12px;
    gap: 10px;
  }
  .icon {
    width: 52px;
    height: 52px;
  }
  .level-badge {
    width: 22px;
    height: 22px;
    font-size: 11px;
  }
  .info h3 {
    font-size: 13px;
  }
  .info p {
    font-size: 11px;
  }
  .progress-text {
    font-size: 10px;
  }
  .unlocked-date {
    font-size: 9px;
  }
  .achievement-detail {
    padding: 14px;
  }
  .icon-large {
    width: 68px;
    height: 68px;
  }
  .icon-large .level-badge {
    width: 28px;
    height: 28px;
    font-size: 14px;
  }
  .header-info h2 {
    font-size: 16px;
  }
  .detail-content h3 {
    font-size: 13px;
  }
  .description,
  .condition p,
  .progress-section .progress-text,
  .unlocked-info p,
  .stats p {
    font-size: 12px;
  }
  .progress-bar-large {
    height: 8px;
  }
}
</style>
