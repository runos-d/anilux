<template>
  <div class="admin-dashboard">
    <header class="admin-header">
      <div class="admin-title">
        <h1>Панель администратора</h1>
        <p>Управление данными и модерация · вошёл как <strong>@{{ currentUser?.nickname || currentUser?.username }}</strong></p>
      </div>
      <button class="btn-refresh" @click="loadOverview" :disabled="loading">
        <SakuraIcon name="refresh" :size="16" />
        Обновить
      </button>
    </header>

    <nav class="admin-tabs">
      <button
        v-for="t in tabs"
        :key="t.id"
        :class="['tab-btn', { active: activeTab === t.id }]"
        @click="setTab(t.id)"
      >
        <SakuraIcon :name="t.icon" :size="18" />
        <span>{{ t.label }}</span>
        <span
          v-if="t.id === 'complaints' && pendingCount"
          class="badge"
        >{{ pendingCount }}</span>
      </button>
    </nav>

    <!-- ===================== ОБЗОР ===================== -->
    <section v-if="activeTab === 'overview'" class="tab-content">
      <div v-if="loading" class="loading-state">
        <SakuraIcon name="hourglass" :size="20" /> Загрузка данных...
      </div>

      <template v-else>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon"><SakuraIcon name="users" :size="22" /></div>
            <div class="stat-value">{{ stats.total_users ?? 0 }}</div>
            <div class="stat-label">Всего пользователей</div>
          </div>
          <div class="stat-card accent-green">
            <div class="stat-icon"><SakuraIcon name="circle" :size="22" /></div>
            <div class="stat-value">{{ stats.online_now ?? 0 }}</div>
            <div class="stat-label">Онлайн сейчас</div>
          </div>
          <div class="stat-card accent-blue">
            <div class="stat-icon"><SakuraIcon name="calendar" :size="22" /></div>
            <div class="stat-value">{{ stats.registered_today ?? 0 }}</div>
            <div class="stat-label">Зарегистрировались сегодня</div>
          </div>
          <div class="stat-card accent-purple">
            <div class="stat-icon"><SakuraIcon name="trending-up" :size="22" /></div>
            <div class="stat-value">{{ stats.registered_this_week ?? 0 }}</div>
            <div class="stat-label">За неделю</div>
          </div>
          <div class="stat-card accent-red">
            <div class="stat-icon"><SakuraIcon name="report" :size="22" /></div>
            <div class="stat-value">{{ pendingCount }}</div>
            <div class="stat-label">Необработанных жалоб</div>
          </div>
          <div class="stat-card accent-pink">
            <div class="stat-icon"><SakuraIcon name="film" :size="22" /></div>
            <div class="stat-value">{{ stats.total_playlists ?? 0 }}</div>
            <div class="stat-label">Плейлистов</div>
          </div>
        </div>

        <div class="overview-grid">
          <div class="panel">
            <div class="panel-head">
              <h3>Последние регистрации</h3>
              <span class="panel-count">{{ recentRegistrations.length }}</span>
            </div>
            <div class="user-list">
              <div v-for="u in recentRegistrations" :key="u.id" class="user-row">
                <span
                  :class="['status-dot', { online: isUserOnline(u.id) }]"
                  :title="isUserOnline(u.id) ? 'Онлайн' : 'Офлайн'"
                />
                <router-link
                  :to="`/profile/@${u.nickname || u.username}`"
                  class="user-link"
                >
                  @{{ u.nickname || u.username }}
                </router-link>
                <span class="user-meta">{{ u.email || "-" }}</span>
                <span class="user-date">{{ formatShort(u.date_joined) }}</span>
              </div>
              <div v-if="!recentRegistrations.length" class="empty-state">Нет данных</div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-head">
              <h3>Онлайн сейчас</h3>
              <span class="panel-count">{{ onlineUsers.length }}</span>
            </div>
            <div class="user-list">
              <div v-for="u in onlineUsers" :key="u.id" class="user-row">
                <span class="status-dot online" />
                <router-link
                  :to="`/profile/@${u.nickname || u.username}`"
                  class="user-link"
                >
                  @{{ u.nickname || u.username }}
                </router-link>
                <span class="user-meta">последний вход {{ formatShort(u.last_login) }}</span>
                <router-link
                  :to="`/profile/@${u.nickname || u.username}`"
                  class="btn-view"
                >
                  Профиль <SakuraIcon name="arrow-right" :size="16" />
                </router-link>
              </div>
              <div v-if="!onlineUsers.length" class="empty-state">Никого нет онлайн</div>
            </div>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <h3>Добавлено сегодня</h3>
            <span class="panel-count">{{ todayAddedFranchises.length + todayAddedAnime.length }}</span>
          </div>
          <div class="today-anime-grid">
            <FranchiseCard
              v-for="f in todayAddedFranchises"
              :key="`fr-${f.id}`"
              :franchise="f"
              :show-actions="false"
              :show-genres="false"
               @click="f.slug && goToFranchise(f.slug)"
            />
            <AnimeCard
              v-for="a in todayAddedAnime"
              :key="a.id"
              :anime="toCardAnime(a)"
              :show-actions="false"
              :show-progress="false"
              :show-genres="true"
              :max-genres="3"
               @click="goToAnime(a)"
            />
            <div v-if="!todayAddedFranchises.length && !todayAddedAnime.length" class="empty-state spread">Сегодня аниме не добавлялось</div>
          </div>
        </div>
      </template>
    </section>

    <!-- ===================== ИМПОРТЫ ===================== -->
    <section v-else-if="activeTab === 'imports'" class="tab-content">
      <div class="import-section">
        <div class="import-card">
          <div class="import-head">
            <SakuraIcon name="download" :size="22" />
            <h3>Импорт аниме из Kodik</h3>
          </div>
          <p class="import-desc">
            Загружает каталог аниме из Kodik API. Обновляет существующие записи
            по shikimori_id или создаёт новые. Выполняется в фоне.
          </p>
          <div class="form-group">
            <label for="kodik-limit">Лимит (пусто -всё)</label>
            <input
              id="kodik-limit"
              v-model="kodikLimit"
              type="number"
              min="1"
              placeholder="Например: 500"
            />
          </div>
          <label class="checkbox-row">
            <input v-model="kodikReplace" type="checkbox" />
            Обновлять существующие записи
          </label>
          <button class="btn-primary" @click="runKodikImport" :disabled="importRunning">
            <SakuraIcon v-if="importRunning" name="hourglass" :size="16" />
            <template v-else><SakuraIcon name="download" :size="16" /></template>
            {{ importRunning ? "Импорт выполняется..." : "Запустить импорт Kodik" }}
          </button>
        </div>

        <div class="import-card">
          <div class="import-head">
            <SakuraIcon name="network" :size="22" />
            <h3>Пересборка франшиз</h3>
          </div>
          <p class="import-desc">
            Группирует аниме по franchise-коду Shikimori и курируемому списку
            (франшизы с несколькими частями). Выполняется в фоне.
          </p>
          <div class="form-group">
            <label for="fr-shiki">JSON кодов Shikimori</label>
            <input id="fr-shiki" v-model="frShikiJson" type="text" />
          </div>
          <!-- <div class="form-group">
            <label for="fr-curated">Курируемый JSON франшиз</label>
            <input id="fr-curated" v-model="frCuratedJson" type="text" />
          </div> -->
          <label class="checkbox-row">
            <input v-model="frDryRun" type="checkbox" />
            Только посчитать (dry-run, без записи в БД)
          </label>
          <button class="btn-primary" @click="runFranchiseRebuild" :disabled="importRunning">
            <SakuraIcon v-if="importRunning" name="hourglass" :size="16" />
            <template v-else><SakuraIcon name="network" :size="16" /></template>
            {{ importRunning ? "Пересборка выполняется..." : "Запустить пересборку франшиз" }}
          </button>
        </div>

        <div class="import-card">
          <div class="import-head">
            <SakuraIcon name="calendar" :size="22" />
            <h3>Синхронизация календаря</h3>
          </div>
          <p class="import-desc">
            Обновляет расписание релизов из живой Shikimori API: следующие эпизоды
            онгоингов и предстоящие премьеры. Выполняется в фоне.
          </p>
          <button class="btn-primary" @click="runCalendarSync" :disabled="importRunning">
            <SakuraIcon v-if="importRunning" name="hourglass" :size="16" />
            <template v-else><SakuraIcon name="calendar" :size="16" /></template>
            {{ importRunning ? "Синхронизация выполняется..." : "Синхронизировать календарь" }}
          </button>
        </div>
      </div>

      <div v-if="importJob.log || importRunning" class="import-result">
        <div class="import-result-head">
          <h4>{{ importJobTitle }}</h4>
          <span v-if="!importJob.finished" class="job-badge running">выполняется</span>
          <span v-else-if="importJob.stopped" class="job-badge stopped">остановлена</span>
          <span
            v-else
            :class="['job-badge', importJob.success ? 'ok' : 'fail']"
          >{{ importJob.success ? "успешно" : "с ошибкой" }}</span>
        </div>
        <pre class="import-log">{{ importJob.log || "Задача запущена, ждём завершения..." }}</pre>
      </div>

      <div v-if="importRunning" class="stop-banner">
        <div>
          <strong>Фоновая задача выполняется на сервере</strong>
          <div class="import-desc">
            Остановка завершит процесс принудительно, незавершённая часть может
            быть не сохранена.
          </div>
        </div>
        <button class="btn-stop" @click="stopImportJob" :disabled="stoppingJob">
          <SakuraIcon name="square" :size="16" />
          {{ stoppingJob ? "Останавливаем..." : "Остановить задачу" }}
        </button>
      </div>

      <div class="danger-zone">
        <h3><SakuraIcon name="ban" :size="18" /> Опасная зона: полная очистка</h3>
        <p class="import-desc">
          Удаление происходит на сервере напрямую и без отката. Перед очисткой
          остановите фоновые задачи.
        </p>
        <div class="danger-buttons">
          <button
            class="btn-danger"
            @click="wipeAll(['franchises'])"
            :disabled="importRunning"
          >
            <SakuraIcon name="trash" :size="16" /> Удалить все франшизы
          </button>
          <button
            class="btn-danger"
            @click="wipeAll(['anime'])"
            :disabled="importRunning"
          >
            <SakuraIcon name="trash" :size="16" /> Удалить все аниме
          </button>
          <button
            class="btn-danger-strong"
            @click="wipeAll(['anime', 'franchises'])"
            :disabled="importRunning"
          >
            <SakuraIcon name="trash" :size="16" /> Удалить всё (аниме + франшизы)
          </button>
        </div>
        <div v-if="wipeResult" class="wipe-result">{{ wipeResult }}</div>
      </div>
    </section>

    <!-- ===================== ЖАЛОБЫ ===================== -->
    <section v-else-if="activeTab === 'complaints'" class="tab-content">
      <div class="panel-head complaints-head">
        <h3>Жалобы</h3>
        <div class="filter-row">
          <button
            v-for="s in complaintStatuses"
            :key="s.value"
            :class="['filter-btn', { active: complaintFilter === s.value }]"
            @click="setComplaintFilter(s.value)"
          >
            {{ s.label }}
          </button>
        </div>
      </div>

      <div v-if="complaintsLoading" class="loading-state">
        <SakuraIcon name="hourglass" :size="20" /> Загрузка жалоб...
      </div>

      <div v-else class="complaints-list">
        <div v-for="c in complaints" :key="c.id" class="complaint-card" :class="c.status">
          <div class="complaint-header">
            <div class="complaint-header-left">
              <span class="complaint-type">{{ complaintTypeLabel(c.complaint_type) }}</span>
              <span :class="['complaint-status', c.status]">{{ complaintStatusLabel(c.status) }}</span>
            </div>
            <div class="complaint-header-right">
              <span class="complaint-id">#{{ c.id }}</span>
              <span class="complaint-date">{{ formatDate(c.created_at) }}</span>
            </div>
          </div>

          <div class="complaint-sections">
            <div class="complaint-section">
              <span class="complaint-section-label">Жалоба от:</span>
              <span class="complaint-section-value">
                <a v-if="c.complainant_url" :href="c.complainant_url" class="complaint-link" @click.prevent="goTo(c.complainant_url)">
                  @{{ c.complainant?.nickname || c.complainant?.username }}
                </a>
                <span v-else class="complaint-text">@{{ c.complainant?.nickname || c.complainant?.username }}</span>
              </span>
            </div>

            <div class="complaint-section">
              <span class="complaint-section-label">Причина:</span>
              <span class="complaint-reason">{{ complaintReasonLabel(c.reason) }}</span>
            </div>

            <div v-if="c.target_info" class="complaint-section">
              <span class="complaint-section-label">На что пожаловались:</span>
              <span class="complaint-section-value">
                <span class="complaint-text">{{ c.target_info }}</span>
                <a v-if="c.target_url" :href="c.target_url" class="btn-open" @click.prevent="goTo(c.target_url)">
                  Открыть
                </a>
                <span v-else-if="c.target_available === false" class="complaint-unavailable">Контент недоступен</span>
              </span>
            </div>

            <div v-if="c.target_title && c.target_title !== c.target_preview" class="complaint-section">
              <span class="complaint-section-label">Заголовок:</span>
              <span class="complaint-text">{{ c.target_title }}</span>
            </div>

            <div v-if="c.target_preview" class="complaint-preview">
              <span class="complaint-preview-label">Превью контента:</span>
              <span class="complaint-preview-text">{{ c.target_preview }}</span>
            </div>

            <div v-if="c.target_media?.length" class="complaint-media">
              <span class="complaint-preview-label">Вложения на момент жалобы:</span>
              <a
                v-for="media in c.target_media"
                :key="media.id"
                :href="media.url || undefined"
                class="complaint-media-item"
                target="_blank"
                rel="noopener"
              >
                {{ media.type === "video" ? "Видео" : "Изображение" }}
                <span v-if="media.caption">— {{ media.caption }}</span>
              </a>
            </div>

            <div v-if="c.description" class="complaint-desc">
              <span class="complaint-desc-label">Комментарий жалобы:</span>
              <span class="complaint-desc-text">{{ c.description }}</span>
            </div>

            <div v-if="c.assigned_to" class="complaint-moderation">
              <span class="complaint-moderation-label">Назначен:</span>
              <a :href="`/profile/@${c.assigned_to.nickname || c.assigned_to.username}`" class="complaint-link" @click.prevent="goTo(`/profile/@${c.assigned_to.nickname || c.assigned_to.username}`)">
                @{{ c.assigned_to.nickname || c.assigned_to.username }}
              </a>
            </div>

            <div v-if="c.resolution" class="complaint-resolution">
              <span class="complaint-resolution-label">Решение:</span>
              <span class="complaint-resolution-text">{{ c.resolution }}</span>
            </div>
            <div v-if="c.action_taken && c.action_taken !== 'none'" class="complaint-meta-row">
              <span class="complaint-meta-label">Применено:</span>
              <span class="complaint-meta-value">{{ complaintActionLabel(c.action_taken) }}</span>
            </div>

            <div v-if="c.resolved_at" class="complaint-meta-row">
              <span class="complaint-meta-label">Решена:</span>
              <span class="complaint-meta-value">{{ formatDate(c.resolved_at) }}</span>
            </div>

            <div v-if="c.updated_at && c.updated_at !== c.created_at" class="complaint-meta-row">
              <span class="complaint-meta-label">Обновлена:</span>
              <span class="complaint-meta-value">{{ formatDate(c.updated_at) }}</span>
            </div>
          </div>

          <div class="complaint-actions">
            <button
              v-if="c.status === 'pending'"
              @click="resolveComplaint(c.id, 'investigating')"
              class="btn-action blue"
            >
              <SakuraIcon name="search" :size="15" /> Расследовать
            </button>
            <button
              v-if="c.status === 'pending' || c.status === 'investigating'"
              @click="openComplaintDecision(c)"
              class="btn-action green"
            >
              <SakuraIcon name="gavel" :size="15" /> Рассмотреть
            </button>
          </div>
        </div>
        <div v-if="!complaints.length" class="empty-state spread">Жалоб нет <SakuraIcon name="tada"/></div>
      </div>
      <div v-if="complaintTotal > complaintPageSize" class="pagination">
        <button class="btn-secondary" :disabled="complaintPage <= 1 || complaintsLoading" @click="changeComplaintPage(complaintPage - 1)">Назад</button>
        <span>Страница {{ complaintPage }} из {{ complaintPages }}</span>
        <button class="btn-secondary" :disabled="complaintPage >= complaintPages || complaintsLoading" @click="changeComplaintPage(complaintPage + 1)">Далее</button>
      </div>
    </section>

    <!-- ===================== ФРАНШИЗЫ ===================== -->
    <section v-else-if="activeTab === 'franchises'" class="tab-content">
      <FranchisesManager />
    </section>

    <!-- ===================== КАТАЛОГ ===================== -->
    <section v-else-if="activeTab === 'catalog'" class="tab-content">
      <CatalogManager />
    </section>

    <!-- ===================== ДОСТИЖЕНИЯ ===================== -->
    <section v-else-if="activeTab === 'achievements'" class="tab-content">
      <AchievementsManager />
    </section>

    <BaseModal
      :show="decisionOpen"
      title="Решение по жалобе"
      size="medium"
      :close-on-overlay="!decisionSaving"
      @close="closeComplaintDecision"
    >
      <div v-if="decisionComplaint" class="decision-form">
        <div class="decision-summary">
          <strong>{{ complaintTypeLabel(decisionComplaint.complaint_type) }} #{{ decisionComplaint.id }}</strong>
          <span>{{ complaintReasonLabel(decisionComplaint.reason) }}</span>
          <span v-if="decisionComplaint.target_info">{{ decisionComplaint.target_info }}</span>
        </div>
        <label class="decision-field">
          <span>Результат</span>
          <select v-model="decisionStatus" :disabled="decisionSaving">
            <option value="resolved">Жалоба подтверждена</option>
            <option value="dismissed">Жалоба отклонена</option>
          </select>
        </label>
        <label v-if="decisionStatus === 'resolved'" class="decision-field">
          <span>Действие</span>
          <select v-model="decisionAction" :disabled="decisionSaving">
            <option value="none">Без дополнительного действия</option>
            <option value="warn_user">Предупредить пользователя</option>
            <option v-if="decisionComplaint.complaint_type !== 'user'" value="delete_content">Удалить контент</option>
            <option value="delete_user">Удалить аккаунт (с сохранением данных)</option>
          </select>
        </label>
        <label class="decision-field">
          <span>Комментарий для отправителя жалобы</span>
          <textarea v-model="decisionResolution" rows="4" maxlength="1000" placeholder="Что проверено и какое решение принято" :disabled="decisionSaving"></textarea>
          <small>{{ decisionResolution.length }}/1000</small>
        </label>
        <p v-if="decisionError" class="decision-error" role="alert">{{ decisionError }}</p>
      </div>
      <template #footer>
        <button class="btn-secondary" :disabled="decisionSaving" @click="closeComplaintDecision">Отмена</button>
        <button class="btn-action green" :disabled="decisionSaving || !decisionResolution.trim()" @click="submitComplaintDecision">
          {{ decisionSaving ? "Применение..." : "Применить решение" }}
        </button>
      </template>
    </BaseModal>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useOnlineStatus } from "@/composables/useOnlineStatus";
import api from "@/api";
import FranchisesManager from "@/components/admin/FranchisesManager.vue";
import AchievementsManager from "@/components/admin/AchievementsManager.vue";
import CatalogManager from "@/components/admin/CatalogManager.vue";
import AnimeCard from "@/components/Cards/AnimeCard.vue";
import FranchiseCard from "@/components/Cards/FranchiseCard.vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import { useToast } from "@/composables/useToast";

const props = defineProps({
  tab: { type: String, default: "overview" },
});

const router = useRouter();
const toast = useToast();
const goToAnime = (a: { slug?: string; id: number | string }) => router.push(`/anime/${a.slug || a.id}`);
const goToFranchise = (slug: string) => router.push(`/franchise/${slug}`);
const goTo = (path: string) => router.push(path);

const authStore = useAuthStore();
const { isUserOnline } = useOnlineStatus();
const currentUser = computed(() => authStore.user);

interface AdminStats {
  total_users?: number;
  online_now?: number;
  registered_today?: number;
  registered_this_week?: number;
  pending_complaints?: number;
  total_playlists?: number;
}

interface AdminUser {
  id: number;
  nickname?: string;
  username: string;
  email?: string;
  date_joined?: string;
  last_login?: string | null;
}

interface AdminAnime {
  id: number;
  slug?: string;
  poster_url?: string;
  title_ru: string;
  title_en?: string;
  year?: number | string;
  kind?: string;
  episodes?: number | string;
  status?: string;
  genres?: (string | { name: string })[] | string;
  score?: number | string;
}

interface AdminComplaint {
  id: number;
  status: string;
  complaint_type?: string;
  reason: string;
  description?: string;
  created_at: string;
  updated_at?: string;
  resolved_at?: string;
  complainant?: { id: number; nickname?: string; username: string };
  complainant_url?: string;
  target_info?: string;
  target_title?: string;
  target_user?: { id: number; username: string; nickname?: string };
  target_url?: string;
  target_preview?: string;
  target_media?: Array<{ id: number; type: string; url?: string | null; caption?: string }>;
  assigned_to?: { id: number; username: string; nickname?: string } | null;
  resolution?: string | null;
  action_taken?: string | null;
  target_available?: boolean;
  object_id?: number;
  content_type_id?: number;
}

const toCardAnime = (a: AdminAnime) => {
  let genres: string[];
  const raw = a.genres;
  if (Array.isArray(raw)) {
    genres = raw.map((g) =>
      typeof g === "object" && g !== null && "name" in g
        ? (g as { name: string }).name
        : String(g),
    );
  } else if (typeof raw === "string" && raw.trim()) {
    genres = raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
  } else {
    genres = [];
  }
  const num = (v: number | string | undefined): number | null =>
    v === undefined || v === null || v === "" ? null : Number(v);
  return {
    id: a.id,
    title_ru: a.title_ru,
    title_en: a.title_en || "",
    year: num(a.year),
    status: a.status || "",
    episodes: num(a.episodes),
    score: a.score ? parseFloat(String(a.score)) : null,
    poster_url: a.poster_url || null,
    type: a.kind || "",
    genres,
  };
};

const legacyToTab: Record<string, string> = {
  stats: "overview",
  registrations: "overview",
  online: "overview",
  today_added: "overview",
  imports: "imports",
  complaints: "complaints",
  support: "overview",
  franchises: "franchises",
  catalog: "catalog",
};
const activeTab = ref(legacyToTab[props.tab] || "overview");

const tabs = [
  { id: "overview", icon: "chart", label: "Обзор" },
  { id: "imports", icon: "import", label: "Импорты" },
  { id: "franchises", icon: "network", label: "Франшизы" },
  { id: "catalog", icon: "filter", label: "Каталог" },
  { id: "achievements", icon: "trophy", label: "Достижения" },
  { id: "complaints", icon: "report", label: "Жалобы" },
];

const setTab = (id: string) => {
  activeTab.value = id;
};

const loading = ref(false);
const lastRefresh = ref("");
const stats = ref<Partial<AdminStats>>({});
const recentRegistrations = ref<AdminUser[]>([]);
const onlineUsers = ref<AdminUser[]>([]);
const todayAddedAnime = ref<AdminAnime[]>([]);

interface TodayFranchise {
  id: number;
  name: string;
  slug?: string;
  score?: number | null;
  year_start?: number | null;
  year_end?: number | null;
  genres?: string[];
  poster_url?: string;
  all_posters?: string[];
  parts_count?: number;
  added_today_count: number;
  entries?: {
    id: number;
    title_ru: string;
    year?: number | undefined;
    status?: string;
    poster_url?: string;
  }[];
}
const todayAddedFranchises = ref<TodayFranchise[]>([]);

const pendingCount = computed(() => stats.value.pending_complaints ?? 0);

const loadOverview = async () => {
  loading.value = true;
  try {
    const [{ data }, animeResp] = await Promise.all([
      api.get("/users/admin/dashboard/"),
      api.get("/anime/admin/today-added/").catch(() => ({ data: { anime: [] } })),
    ]);
    stats.value = data.stats || {};
    recentRegistrations.value = data.recent_registrations || [];
    onlineUsers.value = data.online_users || [];
    const todayItems = animeResp.data.items || animeResp.data.anime || [];
    todayAddedFranchises.value = todayItems.filter(
      (i: { type?: string }) => i.type === "franchise",
    );
    todayAddedAnime.value = todayItems.filter(
      (i: { type?: string }) => !i.type || i.type === "anime",
    );
    lastRefresh.value = new Date().toLocaleTimeString("ru-RU");
  } catch (e) {
    console.error("Admin dashboard error:", e);
  } finally {
    loading.value = false;
  }
};

const complaintsLoading = ref(false);
const complaints = ref<AdminComplaint[]>([]);
const complaintFilter = ref("pending");
const complaintPage = ref(1);
const complaintPageSize = 20;
const complaintTotal = ref(0);
const complaintPages = computed(() => Math.max(1, Math.ceil(complaintTotal.value / complaintPageSize)));
const decisionOpen = ref(false);
const decisionComplaint = ref<AdminComplaint | null>(null);
const decisionStatus = ref<"resolved" | "dismissed">("resolved");
const decisionAction = ref("none");
const decisionResolution = ref("");
const decisionSaving = ref(false);
const decisionError = ref("");

const complaintStatuses = [
  { value: "pending", label: "На рассмотрении" },
  { value: "investigating", label: "Расследуется" },
  { value: "resolved", label: "Решённые" },
  { value: "dismissed", label: "Отклонённые" },
  { value: "all", label: "Все" },
];

const loadComplaints = async () => {
  complaintsLoading.value = true;
  try {
    const { data } = await api.get(
      `/users/admin/complaints/?status=${complaintFilter.value}&page=${complaintPage.value}&page_size=${complaintPageSize}`,
    );
    complaints.value = data.results || [];
    complaintTotal.value = Number(data.count || 0);
  } catch (e) {
    console.error("Complaints error:", e);
  } finally {
    complaintsLoading.value = false;
  }
};

const setComplaintFilter = (val: string) => {
  complaintFilter.value = val;
  complaintPage.value = 1;
  loadComplaints();
};

const changeComplaintPage = (page: number) => {
  if (page < 1 || page > complaintPages.value) return;
  complaintPage.value = page;
  void loadComplaints();
};

const resolveComplaint = async (id: number, newStatus: string) => {
  try {
    await api.patch(`/users/admin/complaints/${id}/`, { status: newStatus });
    await loadComplaints();
    const { data } = await api.get("/users/admin/dashboard/");
    stats.value = data.stats || {};
  } catch (e) {
    console.error("Resolve complaint error:", e);
  }
};

const openComplaintDecision = (complaint: AdminComplaint) => {
  decisionComplaint.value = complaint;
  decisionStatus.value = "resolved";
  decisionAction.value = "none";
  decisionResolution.value = "";
  decisionError.value = "";
  decisionOpen.value = true;
};

const closeComplaintDecision = () => {
  if (decisionSaving.value) return;
  decisionOpen.value = false;
  decisionComplaint.value = null;
};

const submitComplaintDecision = async () => {
  if (!decisionComplaint.value || !decisionResolution.value.trim()) return;
  decisionSaving.value = true;
  decisionError.value = "";
  try {
    await api.patch(`/users/admin/complaints/${decisionComplaint.value.id}/`, {
      status: decisionStatus.value,
      action: decisionStatus.value === "resolved" ? decisionAction.value : "none",
      resolution: decisionResolution.value.trim(),
    });
    toast.success("Решение применено, пользователь уведомлён");
    decisionOpen.value = false;
    decisionComplaint.value = null;
    await Promise.all([loadComplaints(), loadOverview()]);
  } catch (error: unknown) {
    decisionError.value = (error as { response?: { data?: { error?: string } } })?.response?.data?.error
      || "Не удалось применить решение";
  } finally {
    decisionSaving.value = false;
  }
};

const kodikLimit = ref("");
const kodikReplace = ref(false);
const frShikiJson = ref("/app/data_shikimori_franchise.json");
const frCuratedJson = ref("/app/franshize_anime.json");
const frDryRun = ref(false);
const importPollTimer = ref<ReturnType<typeof setInterval> | null>(null);
const importRunning = ref(false);
const importJobTitle = ref("");
const importJob = ref<{
  running: boolean;
  finished: boolean;
  success: boolean | null;
  stopped: boolean;
  log: string;
}>({ running: false, finished: false, success: null, stopped: false, log: "" });
const stoppingJob = ref(false);
const wipeResult = ref("");

const runKodikImport = async () => {
  importRunning.value = true;
  importJobTitle.value = "Импорт Kodik";
  importJob.value = { running: true, finished: false, success: null, stopped: false, log: "" };

  try {
    await api.post("/admin/run-kodik-import/", {
      mode: kodikReplace.value ? "full" : "update",
      limit: kodikLimit.value ? Number(kodikLimit.value) : undefined,
    });
    startImportPolling();
  } catch (error: unknown) {
    importRunning.value = false;
    importJob.value = {
      running: false,
      finished: true,
      success: false,
      stopped: false,
      log: `Ошибка запуска: ${extractError(error)}`,
    };
  }
};

const runFranchiseRebuild = async () => {
  importRunning.value = true;
  importJobTitle.value = "Пересборка франшиз";
  importJob.value = { running: true, finished: false, success: null, stopped: false, log: "" };

  try {
    await api.post("/admin/run-franchise-rebuild/", {
      mode: frDryRun.value ? "incremental" : "incremental",
      dry_run: frDryRun.value,
    });
    startImportPolling();
  } catch (error: unknown) {
    importRunning.value = false;
    importJob.value = {
      running: false,
      finished: true,
      success: false,
      stopped: false,
      log: `Ошибка запуска: ${extractError(error)}`,
    };
  }
};

const runCalendarSync = async () => {
  importRunning.value = true;
  importJobTitle.value = "Синхронизация календаря";
  importJob.value = { running: true, finished: false, success: null, stopped: false, log: "" };

  try {
    await api.post("/admin/run-calendar-sync/", {});
    startImportPolling();
  } catch (error: unknown) {
    importRunning.value = false;
    importJob.value = {
      running: false,
      finished: true,
      success: false,
      stopped: false,
      log: `Ошибка запуска: ${extractError(error)}`,
    };
  }
};

const extractError = (error: unknown): string => {
  const e = error as {
    response?: { data?: { detail?: string; error?: string } };
    message?: string;
  };
  return e?.response?.data?.detail || e?.response?.data?.error || e?.message || "Неизвестная ошибка";
};

const startImportPolling = () => {
  stopImportPolling();
  importPollTimer.value = setInterval(async () => {
    try {
      const { data } = await api.get("/admin/import-status/");
      importJob.value = {
        running: data.running,
        finished: data.finished,
        success: data.success,
        stopped: !!data.stopped,
        log: data.log,
      };
      importRunning.value = data.running === true;
      if (data.finished) {
        stopImportPolling();
        importRunning.value = false;
      }
    } catch {
      stopImportPolling();
      importRunning.value = false;
    }
  }, 3000);
};

const stopImportPolling = () => {
  if (importPollTimer.value) {
    clearInterval(importPollTimer.value);
    importPollTimer.value = null;
  }
};

const loadImportStatusOnce = async () => {
  try {
    const { data } = await api.get("/admin/import-status/");
    importJob.value = {
      running: data.running,
      finished: data.finished,
      success: data.success,
      stopped: !!data.stopped,
      log: data.log,
    };
    importRunning.value = data.running === true;
    importJobTitle.value = data.command
      ? data.command === "import_from_kodik"
        ? "Импорт Kodik"
        : data.command === "rebuild_franchises"
          ? "Пересборка франшиз"
          : data.command === "sync_calendar"
            ? "Синхронизация календаря"
            : data.command
      : "Импорт";
    if (data.running) startImportPolling();
  } catch {
    /* ignore */
  }
};

const stopImportJob = async () => {
  stoppingJob.value = true;
  try {
    const { data } = await api.post("/admin/stop-import/");
    if (data?.stopped) {
      importJob.value.log += "\n[остановка запрошена...]";
      startImportPolling();
    } else {
      importJob.value.log = importJob.value.log || data?.message || "";
    }
  } catch (error: unknown) {
    importJob.value.log += `\nОшибка остановки: ${extractError(error)}`;
  } finally {
    stoppingJob.value = false;
  }
};

const wipeAll = async (targets: string[]) => {
  const targetText =
    targets.includes("anime") && targets.includes("franchises")
      ? "все аниме и все франшизы"
      : targets.includes("anime")
        ? "все аниме"
        : "все франшизы";
  const confirmed = window.confirm(
    `Это удалит ${targetText} из базы навсегда. Продолжить?`,
  );
  if (!confirmed) return;
  try {
    const { data } = await api.post("/admin/wipe-all/", { targets });
    const parts: string[] = [];
    if (typeof data?.anime_deleted === "number")
      parts.push(`аниме: ${data.anime_deleted}`);
    if (typeof data?.franchises_deleted === "number")
      parts.push(`франшиз: ${data.franchises_deleted}`);
    wipeResult.value =
      "Очищено -" + (parts.length ? parts.join(", ") : "ничего не удалено");
    await loadImportStatusOnce();
  } catch (error: unknown) {
    wipeResult.value = `Ошибка очистки: ${extractError(error)}`;
  }
};

const formatDate = (d?: string | null) => {
  if (!d) return "-";
  return new Date(d).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

const formatShort = (d?: string | null) => {
  if (!d) return "-";
  return new Date(d).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
};

const complaintTypeLabel = (t?: string) =>
  ({
    playlist: "Плейлист",
    comment: "Комментарий",
    reactor_post: "Пост",
    user: "Пользователь",
    dub: "Озвучка",
    group: "Группа",
    playlist_item: "Элемент плейлиста",
  })[t || ""] || t || "Жалоба";

const complaintReasonLabel = (r?: string) =>
  ({
    spam: "Спам",
    harassment: "Харассмент",
    inappropriate: "Неподходящий контент",
    copyright: "Авторские права",
    misleading: "Вводящий в заблуждение",
    broken_link: "Битая ссылка",
    duplicate: "Дубликат",
    other: "Другое",
  })[r || ""] || r;

const complaintStatusLabel = (s?: string) =>
  ({
    pending: "На рассмотрении",
    investigating: "Расследуется",
    resolved: "Решена",
    dismissed: "Отклонена",
  })[s || ""] || s;

const complaintActionLabel = (action?: string | null) =>
  ({
    warn_user: "Предупреждение пользователю",
    delete_content: "Контент удалён",
    deactivate_user: "Пользователь заблокирован",
  })[action || ""] || action || "Без дополнительного действия";

watch(activeTab, (val) => {
  if (val === "complaints") loadComplaints();
  if (val === "imports") loadImportStatusOnce();
  if (val !== "imports") stopImportPolling();
});

onMounted(() => {
  loadOverview();
  if (activeTab.value === "complaints") loadComplaints();
  if (activeTab.value === "imports") loadImportStatusOnce();
});
</script>

<style scoped>
.admin-dashboard {
  max-width: 1120px;
  margin: 0 auto;
  padding: 24px;
  min-height: 100vh;
}

/* ---------- Header ---------- */
.admin-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 4px;
}

.admin-title h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: var(--text-primary, #fff);
}

.admin-title p {
  margin: 0;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-tertiary, #9aa);
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 9px 16px;
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-md, 11px);
  color: var(--text-primary, #fff);
  font-size: var(--text-sm, 0.75rem);
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.btn-refresh:hover:not(:disabled) {
  background: var(--surface-4, #1c162c);
  border-color: var(--border-strong, #555);
}
.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ---------- Tabs ---------- */
.admin-tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border-default, #333);
  margin: 20px 0 24px;
  overflow-x: none;
}

.tab-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-tertiary, #9aa);
  font-size: var(--text-base, 0.875rem);
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.15s, border-color 0.15s;
  margin-bottom: -1px;
}
.tab-btn:hover {
  color: var(--text-primary, #fff);
}
.tab-btn.active {
  color: var(--accent, #ff7eb3);
  border-bottom-color: var(--accent, #ff7eb3);
}

.badge {
  background: var(--danger, #d72727);
  color: #fff;
  border-radius: 999px;
  padding: 1px 5px;
  font-size: 0.6875rem;
  font-weight: 700;
  min-width: 15px;
  min-height: 15px;
  text-align: center;
  justify-content: center;
}

/* ---------- Обзор: статистика ---------- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 18px 16px;
  text-align: center;
  transition: transform 0.15s, border-color 0.15s;
}
.stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-strong, #555);
}

.stat-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
  color: var(--accent, #ff7eb3);
}
.stat-card.accent-green .stat-icon { color: var(--success, #2cea72); }
.stat-card.accent-blue .stat-icon { color: var(--info, #42a0f1); }
.stat-card.accent-purple .stat-icon { color: var(--status-onhold, #b56bff); }
.stat-card.accent-red .stat-icon { color: var(--danger, #d72727); }
.stat-card.accent-pink .stat-icon { color: var(--accent-bright, #ffa8c9); }

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 4px;
  color: var(--text-primary, #fff);
}
.stat-label {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
}

/* ---------- Обзор: панели ---------- */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.panel {
  min-width: 0;
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 18px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.panel-head h3 {
  margin: 0;
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.panel-count {
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 700;
  color: var(--accent, #ff7eb3);
  background: var(--accent-subtle, rgba(255, 126, 179, 0.12));
  border-radius: 999px;
  padding: 2px 10px;
}

.user-list {
  display: flex;
  flex-direction: column;
}

.user-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 0;
  border-top: 1px solid var(--border-subtle, #222);
  font-size: var(--text-sm, 0.75rem);
}
.user-row:first-child {
  border-top: none;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-disabled, #555);
  flex-shrink: 0;
}
.status-dot.online {
  background: var(--success, #2cea72);
  box-shadow: 0 0 6px var(--success-subtle, rgba(60, 255, 131, 0.4));
}

.user-link {
  min-width: 0;
  flex: 1;
  color: var(--accent, #ff7eb3);
  text-decoration: none;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-link:hover {
  text-decoration: underline;
}

.user-meta {
  color: var(--text-tertiary, #9aa);
  margin-left: auto;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-date {
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
}

.btn-view {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  flex-shrink: 0;
  color: var(--accent, #ff7eb3);
  text-decoration: none;
  white-space: nowrap;
}
.btn-view:hover {
  text-decoration: underline;
}

/* ---------- Обзор: аниме ---------- */
.today-anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: var(--space-6);
}
.today-anime-grid :deep(.anime-card) {
  width: 100%;
  max-width: 100%;
}
.today-anime-grid :deep(.anime-poster) {
  aspect-ratio: 2 / 3;
  height: auto;
}

/* ---------- Импорты ---------- */
.import-section {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.import-card {
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 20px;
}

.import-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  color: var(--accent, #ff7eb3);
}
.import-head h3 {
  margin: 0;
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}

.import-desc {
  margin: 0 0 16px;
  font-size: var(--text-sm, 0.75rem);
  line-height: 1.55;
  color: var(--text-tertiary, #9aa);
}

.form-group {
  margin-bottom: 12px;
}
.form-group label {
  display: block;
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  margin-bottom: 6px;
}
.form-group input,
.checkbox-row input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 12px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-sm, 7px);
  color: var(--text-primary, #fff);
  font-size: var(--text-sm, 0.75rem);
  font-family: inherit;
}
.form-group input:focus {
  outline: none;
  border-color: var(--accent, #ff7eb3);
}

.checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-tertiary, #9aa);
  margin-bottom: 10px;
  cursor: pointer;
}
.checkbox-row input {
  width: auto;
  accent-color: var(--accent, #ff7eb3);
}

.btn-primary {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 16px;
  background: linear-gradient(135deg, var(--accent, #ff7eb3), var(--accent-press, #e86a9e));
  color: var(--text-on-accent, #1a0a14);
  border: none;
  border-radius: var(--radius-md, 11px);
  font-weight: 700;
  font-size: var(--text-sm, 0.75rem);
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
  margin-top: 4px;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-petal-sm, none);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.import-result {
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 16px;
}
.import-result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.import-result-head h4 {
  margin: 0;
  font-size: var(--text-md, 0.9375rem);
  color: var(--text-primary, #fff);
}
.job-badge {
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
}
.job-badge.running { background: var(--info-subtle); color: var(--info); }
.job-badge.ok { background: var(--success-subtle); color: var(--success); }
.job-badge.fail { background: var(--danger-subtle); color: var(--danger); }
.job-badge.stopped { background: var(--warning-subtle); color: var(--warning); }

.import-log {
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-subtle, #222);
  border-radius: var(--radius-sm, 7px);
  padding: 12px;
  font-family: var(--font-mono, monospace);
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-secondary, #ccc);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow-y: auto;
}

.stop-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 16px;
  padding: 14px 16px;
  border: 1px solid var(--warning-subtle);
  border-radius: var(--radius-sm, 7px);
  background: color-mix(in srgb, var(--warning) 8%, transparent);
}
.btn-stop {
  padding: 8px 16px;
  border: none;
  border-radius: var(--radius-sm, 7px);
  background: var(--warning, #e8a33d);
  color: #1a1a1a;
  font-weight: 700;
  font-size: var(--text-sm, 0.8125rem);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-stop:hover:not(:disabled) {
  filter: brightness(1.08);
}
.btn-stop:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.danger-zone {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid color-mix(in srgb, var(--danger) 35%, transparent);
  border-radius: var(--radius-sm, 7px);
}
.danger-zone h3 {
  margin: 0 0 6px;
  font-size: var(--text-base, 0.9375rem);
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}
.danger-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 12px;
}
.btn-danger,
.btn-danger-strong {
  padding: 8px 16px;
  border-radius: var(--radius-sm, 7px);
  font-weight: 700;
  font-size: var(--text-sm, 0.8125rem);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: color-mix(in srgb, var(--danger) 12%, transparent);
  color: var(--danger);
  border: 1px solid color-mix(in srgb, var(--danger) 35%, transparent);
}
.btn-danger:hover:not(:disabled),
.btn-danger-strong:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 22%, transparent);
}
.btn-danger-strong {
  background: var(--danger);
  color: #fff;
  border-color: var(--danger);
}
.btn-danger-strong:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 82%, #000);
}
.btn-danger:disabled,
.btn-danger-strong:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.wipe-result {
  margin-top: 10px;
  font-size: var(--text-sm, 0.8125rem);
  color: var(--text-secondary);
}

/* ---------- Жалобы ---------- */
.complaints-head {
  justify-content: space-between;
}

.filter-row {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.filter-btn {
  padding: 5px 12px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-default, #333);
  border-radius: 999px;
  color: var(--text-tertiary, #9aa);
  font-size: var(--text-xs, 0.6875rem);
  cursor: pointer;
  transition: all 0.15s;
}
.filter-btn:hover {
  border-color: var(--border-strong, #555);
}
.filter-btn.active {
  background: var(--accent-subtle, rgba(255, 126, 179, 0.12));
  color: var(--accent, #ff7eb3);
  border-color: var(--accent, #ff7eb3);
}

.complaints-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.complaint-card {
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.complaint-card.resolved {
  border-color: var(--success-subtle);
  opacity: 0.85;
}
.complaint-card.dismissed {
  opacity: 0.6;
}

.complaint-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.complaint-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.complaint-header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.complaint-type {
  font-weight: 700;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-primary, #fff);
}
.complaint-status {
  font-size: var(--text-xs, 0.6875rem);
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.complaint-status.pending { background: var(--warning-subtle); color: var(--warning); }
.complaint-status.investigating { background: var(--info-subtle); color: var(--info); }
.complaint-status.resolved { background: var(--success-subtle); color: var(--success); }
.complaint-status.dismissed { background: var(--surface-5); color: var(--text-tertiary); }
.complaint-id {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  font-family: var(--font-mono, monospace);
}
.complaint-date {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
}

.complaint-sections {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.complaint-section {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: var(--text-sm, 0.75rem);
}
.complaint-section-label {
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
  flex-shrink: 0;
  min-width: 110px;
}
.complaint-section-value {
  color: var(--text-secondary, #ccc);
  display: inline-flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.complaint-text {
  color: var(--text-secondary, #ccc);
}
.complaint-unavailable { color: var(--text-tertiary); font-size: var(--text-xs); }
.complaint-reason {
  color: var(--text-primary, #fff);
  font-weight: 600;
}

.complaint-link {
  color: var(--accent, #ff7eb3);
  text-decoration: none;
  font-weight: 600;
}
.complaint-link:hover {
  text-decoration: underline;
}

.btn-open {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--accent-subtle, rgba(255, 126, 179, 0.12));
  border: 1px solid var(--accent, #ff7eb3);
  border-radius: var(--radius-sm, 7px);
  color: var(--accent, #ff7eb3);
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 700;
  cursor: pointer;
  text-decoration: none;
  transition: background 0.15s, transform 0.15s;
}
.btn-open:hover {
  background: var(--accent, #ff7eb3);
  color: var(--text-on-accent, #1a0a14);
  transform: translateY(-1px);
}

.complaint-preview {
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-subtle, #222);
  border-radius: var(--radius-sm, 7px);
  padding: 10px 12px;
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  line-height: 1.5;
}
.complaint-preview-label {
  display: block;
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-disabled, #555);
  margin-bottom: 4px;
}
.complaint-preview-text {
  white-space: pre-wrap;
  word-break: break-word;
}
.complaint-media { display: flex; flex-direction: column; gap: 7px; padding: 10px 12px; border-radius: var(--radius-sm); background: var(--surface-4); }
.complaint-media-item { color: var(--accent); text-decoration: none; font-size: var(--text-sm); }
.complaint-media-item:hover { text-decoration: underline; }

.complaint-desc {
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-subtle, #222);
  border-radius: var(--radius-sm, 7px);
  padding: 10px 12px;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-secondary, #ccc);
  line-height: 1.5;
}
.complaint-desc-label {
  display: block;
  font-size: 0.625rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-disabled, #555);
  margin-bottom: 4px;
}
.complaint-desc-text {
  white-space: pre-wrap;
  word-break: break-word;
}

.complaint-moderation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: var(--text-sm, 0.75rem);
  padding: 8px 12px;
  background: color-mix(in srgb, var(--info) 8%, transparent);
  border-radius: var(--radius-sm, 7px);
}
.complaint-moderation-label {
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
  flex-shrink: 0;
}
.complaint-moderation-value {
  color: var(--text-secondary, #ccc);
}

.complaint-resolution {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: var(--text-sm, 0.75rem);
  padding: 8px 12px;
  background: color-mix(in srgb, var(--success) 8%, transparent);
  border-radius: var(--radius-sm, 7px);
}
.complaint-resolution-label {
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
  flex-shrink: 0;
}
.complaint-resolution-text {
  color: var(--text-secondary, #ccc);
  white-space: pre-wrap;
  word-break: break-word;
}

.complaint-meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
}
.complaint-meta-label {
  white-space: nowrap;
}
.complaint-meta-value {
  color: var(--text-secondary, #ccc);
}

.complaint-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 4px;
  border-top: 1px solid var(--border-subtle, #222);
}
.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-sm, 7px);
  font-size: var(--text-sm, 0.75rem);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
  background: transparent;
}
.btn-action:hover {
  transform: translateY(-1px);
}
.btn-action.blue { background: var(--info-subtle); color: var(--info); border: 1px solid transparent; }
.btn-action.green { background: var(--success-subtle); color: var(--success); border: 1px solid transparent; }
.btn-action.gray { background: var(--surface-5); color: var(--text-tertiary); border: 1px solid var(--border-default); }

.decision-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.decision-summary {
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--surface-4);
  color: var(--text-secondary);
}
.decision-summary strong { color: var(--text-primary); }
.decision-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: 600;
}
.decision-field select,
.decision-field textarea {
  width: 100%;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-4);
  color: var(--text-primary);
  padding: 10px 12px;
  font: inherit;
}
.decision-field textarea { resize: vertical; min-height: 100px; }
.decision-field small { align-self: flex-end; color: var(--text-tertiary); font-weight: 400; }
.decision-error {
  margin: 0;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--danger, #ef4444) 12%, transparent);
  color: var(--danger, #ef4444);
}

/* ---------- Утилиты ---------- */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 48px;
  font-size: var(--text-md, 0.9375rem);
  color: var(--text-tertiary, #9aa);
}
.spread {
  grid-column: 1 / -1;
}
.empty-state {
  padding: 24px;
  text-align: center;
  color: var(--text-tertiary, #9aa);
  font-size: var(--text-sm, 0.75rem);
}

@media (max-width: 768px) {
  .overview-grid,
  .import-section {
    grid-template-columns: 1fr;
  }
  .admin-header {
    flex-direction: column;
  }
  .user-meta {
    display: none;
  }
}
</style>
