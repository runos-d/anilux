<template>
  <div class="user-achievements">
    <div class="achievements-header">
      <h2>Достижения</h2>
      <span class="achievements-stats">
        {{ unlockedCount }} / {{ totalCount }}
      </span>
    </div>

    <div v-if="loading" class="loading">
      <LoadingSpinner />
    </div>

    <div v-if="!loading && visibleAchievements.length === 0" class="empty">
      <p>Достижения не найдены</p>
    </div>

    <div
      v-if="!loading && visibleAchievements.length > 0"
      class="achievements-grid"
    >
      <div
        v-for="achievement in visibleAchievements"
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
            :size="70"
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
              {{ achievement.progress }} / {{
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

    <Modal v-if="selectedAchievement" :model-value="true" @close="selectedAchievement = null">
      <div class="achievement-detail">
        <div class="detail-header">
          <div class="icon-large">
            <SakuraIcon
              :name="selectedAchievement.achievement.icon_svg || 'trophy'"
              :size="100"
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

    <router-link
      v-if="!loading && visibleAchievements.length > 0"
      to="/achievements"
      class="view-all-link"
    >
      Все достижения <SakuraIcon name="arrow-right" :size="16" />
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue";
import Modal from "@/components/ui/Modal.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import api from "@/api";
import { collectionRows } from '@/lib/collectionRows';

interface Props {
  userId: number;
}

interface UserAchievementItem {
  id: number;
  is_unlocked: boolean;
  progress: number;
  progress_percentage: number;
  unlocked_at?: string | null;
  achievement: {
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
  };
}

const props = defineProps<Props>();

const loading = ref(false);
const achievements = ref<UserAchievementItem[]>([]);
const selectedAchievement = ref<UserAchievementItem | null>(null);

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

const unlockedCount = computed(() => {
  return achievements.value.filter((a) => a.is_unlocked).length;
});

const totalCount = computed(() => {
  return achievements.value.length;
});

const visibleAchievements = computed(() =>
  achievements.value.filter((a) => a.is_unlocked),
);

const loadAchievements = async () => {
  loading.value = true;
  try {
    const params = { user_id: props.userId };
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

const getConditionText = (achievement: {
  condition_type: string;
  condition_value: number;
}) => {
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
  return conditionTexts[achievement.condition_type] || achievement.condition_type;
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

const openAchievementDetail = (achievement: UserAchievementItem) => {
  selectedAchievement.value = achievement;
};

onMounted(() => {
  loadAchievements();
});
</script>

<style scoped>
.user-achievements {
  padding: 0 24px 24px;
}

.achievements-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-top: 16px;
}

.achievements-header h2 {
  margin: 0;
  font-size: 20px;
  color: var(--text-primary);
}

.achievements-stats {
  font-size: 14px;
  color: var(--text-secondary);
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 280px), 1fr));
  gap: 16px;
}

.achievement-card {
  display: flex;
  gap: 16px;
  padding: 16px;
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
  width: 70px;
  height: 70px;
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
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 14px;
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
  min-width: 0;
}

.info h3 {
  margin: 0 0 6px;
  font-size: 15px;
  color: var(--text-primary);
}

.info p {
  margin: 0 0 10px;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.progress {
  margin-bottom: 10px;
}

.progress-bar {
  height: 5px;
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
  font-size: 11px;
  color: var(--text-tertiary);
}

.unlocked-date {
  font-size: 10px;
  color: var(--accent-2);
  font-weight: bold;
}

.loading,
.empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-tertiary);
}

.achievement-detail {
  padding: 24px;
  max-width: 500px;
}

.detail-header {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.icon-large {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.icon-large > :deep(svg) {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.icon-large .level-badge {
  width: 40px;
  height: 40px;
  font-size: 20px;
}

.header-info h2 {
  margin: 0 0 6px;
  font-size: 20px;
  color: var(--text-primary);
}

.header-info { min-width: 0; }

.category {
  margin: 0;
  color: var(--text-tertiary);
}

.detail-content > * {
  margin-bottom: 20px;
}

.detail-content h3 {
  margin: 0 0 8px;
  font-size: 15px;
  color: var(--text-primary);
}

.description {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.condition p {
  font-size: 13px;
  color: var(--text-secondary);
}

.progress-bar-large {
  height: 10px;
  background: var(--surface-1);
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-bar-large .progress-fill {
  height: 100%;
}

.progress-section .progress-text {
  font-size: 13px;
}

.unlocked-info p {
  font-size: 13px;
  color: var(--accent-2);
}

.stats p {
  font-size: 13px;
  color: var(--text-secondary);
}

.view-all-link {
  display: inline-block;
  margin-top: 24px;
  padding: 10px 20px;
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
  border-radius: var(--radius-button);
  transition: all 0.15s ease;
}

.view-all-link:hover {
  background: var(--accent-subtle);
}
</style>
