<template>
  <div class="achievements-manager">
    <div class="am-sidebar">
      <div class="am-sidebar-head">
        <div class="am-search">
          <SakuraIcon name="search" :size="16" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск достижения..."
          />
        </div>
        <button class="am-create-btn" @click="openCreate">
          <SakuraIcon name="plus" :size="16" />
          <span>Создать</span>
        </button>
      </div>

      <div v-if="loading" class="am-list-loading">
        <SakuraIcon name="hourglass" :size="18" /> Загрузка...
      </div>

      <div v-else-if="loadError" class="am-list-loading" role="alert">
        <SakuraIcon name="warning" :size="18" /> {{ loadError }}
        <button class="am-create-btn" @click="load">Повторить</button>
      </div>
      <div v-else class="am-list">
        <button
          v-for="a in filtered"
          :key="a.id"
          :class="['am-item', { active: editing && editing.id === a.id }]"
          @click="selectAchievement(a)"
        >
          <span class="am-item-icon">
            <SakuraIcon :name="iconName(a)" :size="20" :color="levelColor(a.level)" />
          </span>
          <span class="am-item-info">
            <span class="am-item-name">
              {{ a.name }}
              <span v-if="!a.is_active" class="am-inactive">неактивно</span>
            </span>
            <span class="am-item-meta">
              {{ conditionLabel(a) }} · {{ a.condition_value }}
            </span>
          </span>
        </button>

        <div v-if="!filtered.length" class="am-empty-list">
          <SakuraIcon name="search" :size="18" />
          <span>Достижения не найдены</span>
        </div>
      </div>

      <div class="am-sidebar-footer">{{ achievements.length }} всего</div>
    </div>

    <div class="am-main">
      <div v-if="!editing && !isCreating" class="am-main-empty">
        <SakuraIcon name="trophy" :size="40" />
        <p>Выберите достижение или создайте новое</p>
      </div>

      <div v-else class="am-editor">
        <div class="am-editor-head">
          <h3>{{ form.id ? "Редактирование" : "Новое достижение" }}</h3>
          <div class="am-head-actions">
            <button
              v-if="form.id"
              class="am-btn small danger"
              @click="askDelete"
              :disabled="saving"
            >
              <SakuraIcon name="trash" :size="14" /> Удалить
            </button>
            <button
              v-if="form.id"
              class="am-btn small"
              @click="toggleActive"
              :disabled="saving"
            >
              <SakuraIcon name="eye" :size="14" />
              {{ form.is_active ? "Деактивировать" : "Активировать" }}
            </button>
            <button
              type="submit"
              class="am-btn small primary"
              form="achievement-form"
              :disabled="saving || !form.name?.trim() || !form.description?.trim()"
            >
              <SakuraIcon name="save" :size="14" /> {{ saving ? "…" : "Сохранить" }}
            </button>
          </div>
        </div>

        <form id="achievement-form" class="am-form" @submit.prevent="save">
          <div class="am-field am-icon-area">
            <label>Иконка</label>
            <div class="am-icon-preview">
              <SakuraIcon
                :name="form.icon_svg || 'trophy'"
                :size="48"
                :color="levelColor(form.level)"
              />
            </div>
            <input
              v-model="form.icon_svg"
              type="text"
              placeholder="Название иконки (SakuraIcon)"
            />
            <div class="am-icon-grid">
              <button
                v-for="ic in ICONS"
                :key="ic"
                type="button"
                :class="['am-icon-choice', { active: form.icon_svg === ic }]"
                @click="form.icon_svg = ic"
                :title="ic"
              >
                <SakuraIcon :name="ic" :size="18" />
              </button>
            </div>
          </div>

          <div class="am-row">
            <div class="am-field">
              <label for="achievement-name">Название</label>
              <input id="achievement-name" v-model="form.name" type="text" required />
            </div>
            <div class="am-field">
              <label>Уровень</label>
              <select v-model="form.level">
                <option v-for="l in LEVELS" :key="l.value" :value="l.value">
                  {{ l.label }}
                </option>
              </select>
            </div>
          </div>

          <div class="am-field">
            <label for="achievement-description">Описание (обязательно)</label>
            <textarea id="achievement-description" v-model="form.description" rows="2" required></textarea>
          </div>

          <div class="am-row">
            <div class="am-field">
              <label>Категория</label>
              <select v-model="form.category">
                <option v-for="c in CATEGORIES" :key="c.value" :value="c.value">
                  {{ c.label }}
                </option>
              </select>
            </div>
            <div class="am-field">
              <label>Условие</label>
              <select v-model="form.condition_type">
                <option
                  v-for="(label, key) in conditionTypes"
                  :key="key"
                  :value="key"
                >
                  {{ label }}
                </option>
              </select>
            </div>
            <div class="am-field am-value">
              <label>Значение</label>
              <input v-model.number="form.condition_value" type="number" min="0" />
            </div>
          </div>

          <div v-if="error" class="am-error">{{ error }}</div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import adminAchievementsApi, {
  ACHIEVEMENT_CATEGORIES,
  ACHIEVEMENT_LEVELS,
  type AdminAchievement,
} from "@/api/adminAchievements";

const CATEGORIES = ACHIEVEMENT_CATEGORIES;
const LEVELS = ACHIEVEMENT_LEVELS;

const ICONS = [
  "trophy", "star", "star-filled", "star-half", "star-rating", "fire",
  "zap", "target", "crown", "sparkles", "sparkle", "eye", "eye-off",
  "play", "movie", "film", "video", "anime-tv", "disc", "heart",
  "heart-plus", "favorite", "book", "bookmark", "users", "user-plus",
  "user-check", "message", "message-circle", "chat", "reply-chat",
  "thumbs-up", "repost", "share-2", "trending-up", "clock", "timer",
  "calendar", "history", "moon", "sun", "sunrise", "sunset", "sunset-alt",
  "hourglass", "rocket", "rocket-alt", "brain", "ghost", "gift", "bell",
  "save", "folder", "folder-open", "list", "link", "filter", "factory",
  "building", "camera", "globe", "package", "toggle", "toggle-off",
  "dropped", "x-circle", "ban", "refresh", "edit", "file-text",
];

interface AchievementForm {
  id?: number;
  name: string;
  description: string;
  icon_svg: string;
  category: string;
  level: string;
  condition_type: string;
  condition_value: number;
  is_active: boolean;
}

const loading = ref(false);
const loadError = ref('');
const saving = ref(false);
const error = ref("");
const searchQuery = ref("");
const achievements = ref<AdminAchievement[]>([]);
const conditionTypes = ref<Record<string, string>>({});

const form = ref<AchievementForm>({} as AchievementForm);
const editing = ref<AdminAchievement | null>(null);
const isCreating = ref(false);

const levelColors: Record<string, string> = {
  bronze: "#cd7f32",
  silver: "#c0c0c0",
  gold: "#ffd700",
  legendary: "#9b59b6",
};

const levelColor = (level: string) =>
  levelColors[level] || "var(--text-secondary)";

const iconName = (a: AdminAchievement) => a.icon_svg || "trophy";

const conditionLabel = (a: AdminAchievement) =>
  conditionTypes.value[a.condition_type] || a.condition_type;

const filtered = computed(() => {
  const q = searchQuery.value.toLowerCase().trim();
  if (!q) return achievements.value;
  return achievements.value.filter(
    (a) =>
      a.name.toLowerCase().includes(q) ||
      a.condition_type.toLowerCase().includes(q),
  );
});

const load = async () => {
  loading.value = true;
  loadError.value = '';
  try {
    const [list, conds] = await Promise.all([
      adminAchievementsApi.list(),
      adminAchievementsApi.conditionTypes(),
    ]);
    achievements.value = list;
    conditionTypes.value = conds;
  } catch (e) {
    console.error("Achievements admin load error:", e);
    loadError.value = 'Не удалось загрузить достижения';
  } finally {
    loading.value = false;
  }
};

const selectAchievement = (a: AdminAchievement) => {
  isCreating.value = false;
  editing.value = a;
  editForm(a);
};

const editForm = (a: AdminAchievement) => {
  form.value = {
    id: a.id,
    name: a.name,
    description: a.description,
    icon_svg: a.icon_svg || "",
    category: a.category,
    level: a.level,
    condition_type: a.condition_type,
    condition_value: a.condition_value,
    is_active: a.is_active,
  };
  error.value = "";
};

const openCreate = () => {
  isCreating.value = true;
  const firstType = Object.keys(conditionTypes.value)[0] || "anime_watched";
  editing.value = null;
  form.value = {
    id: undefined,
    name: "",
    description: "",
    icon_svg: "trophy",
    category: "basic",
    level: "bronze",
    condition_type: firstType,
    condition_value: 1,
    is_active: true,
  };
  error.value = "";
};

const save = async () => {
  saving.value = true;
  error.value = "";
  try {
    const payload = {
      name: form.value.name,
      description: form.value.description || "",
      icon_svg: form.value.icon_svg || "",
      category: form.value.category,
      level: form.value.level,
      condition_type: form.value.condition_type,
      condition_value: Math.max(0, Number(form.value.condition_value) || 0),
    };
    let saved: AdminAchievement;
    if (form.value.id) {
      const { data } = await adminAchievementsApi.update(form.value.id, payload);
      saved = data;
    } else {
      const { data } = await adminAchievementsApi.create(payload);
      saved = data;
    }
    await load();
    const found = achievements.value.find((a) => a.id === saved.id);
    if (found) selectAchievement(found);
  } catch (e: unknown) {
    const data = (e as { response?: { data?: Record<string, unknown> } })?.response?.data;
    const detail = data?.detail || Object.values(data || {}).flat().find(value => typeof value === 'string');
    error.value = typeof detail === 'string' ? detail : "Не удалось сохранить достижение";
  } finally {
    saving.value = false;
  }
};

const toggleActive = async () => {
  if (!form.value.id) return;
  const { data } = await adminAchievementsApi.toggleActive(form.value.id);
  form.value.is_active = data.is_active;
  const found = achievements.value.find((a) => a.id === form.value.id);
  if (found) found.is_active = data.is_active;
};

const askDelete = async () => {
  if (!form.value.id) return;
  if (!confirm(`Удалить достижение «${form.value.name}»?`)) return;
  await adminAchievementsApi.remove(form.value.id);
  isCreating.value = false;
  editing.value = null;
  form.value = {} as AchievementForm;
  await load();
};

onMounted(load);
</script>

<style scoped>
.achievements-manager {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
  min-height: 560px;
}

.am-sidebar {
  background: var(--surface-3);
  border-radius: var(--radius-card);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.am-sidebar-head {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-bottom: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
}

.am-search {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--surface-1);
  border-radius: var(--radius-button);
  padding: 0 10px;
  color: var(--text-tertiary);
}

.am-search input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  padding: 8px 0;
  font-size: 13px;
}

.am-create-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: var(--radius-button);
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.am-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.am-list-loading,
.am-empty-list {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px 12px;
  color: var(--text-tertiary);
}

.am-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border: none;
  background: transparent;
  border-radius: var(--radius-button);
  color: var(--text-primary);
  cursor: pointer;
  text-align: left;
}

.am-item:hover {
  background: var(--surface-1);
}

.am-item.active {
  background: var(--accent-subtle);
}

.am-item-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  background: var(--surface-1);
  border-radius: var(--radius-button);
}

.am-item-info {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.am-item-name {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.am-inactive {
  font-size: 10px;
  color: var(--accent-orange, #ff6b35);
  margin-left: 6px;
}

.am-item-meta {
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.am-sidebar-footer {
  padding: 10px 12px;
  font-size: 12px;
  color: var(--text-tertiary);
  border-top: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
}

.am-main {
  min-width: 0;
  background: var(--surface-3);
  border-radius: var(--radius-card);
  padding: 20px;
  display: flex;
}

.am-main-empty {
  margin: auto;
  text-align: center;
  color: var(--text-tertiary);
}

.am-main-empty p {
  margin-top: 12px;
}

.am-editor {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.am-editor-head {
  flex-wrap: wrap;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.am-editor-head h3 {
  margin: 0;
  color: var(--text-primary);
  font-size: 17px;
}

.am-head-actions {
  flex-wrap: wrap;
  display: flex;
  gap: 8px;
}

.am-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-button);
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
}

.am-btn.small {
  padding: 6px 10px;
  font-size: 12px;
}

.am-btn.primary {
  background: var(--accent);
  border-color: transparent;
  color: #fff;
}

.am-btn.danger {
  background: rgba(255, 77, 79, 0.12);
  border-color: rgba(255, 77, 79, 0.4);
  color: #ff4d4f;
}

.am-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.am-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 160px), 1fr));
  gap: 12px;
}

.am-value {
  max-width: 130px;
}

.am-field {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.am-field label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.am-field input[type="text"],
.am-field input[type="number"],
.am-field textarea,
.am-field select {
  background: var(--surface-1);
  border: 1px solid var(--border-color, rgba(255, 255, 255, 0.12));
  border-radius: var(--radius-button);
  color: var(--text-primary);
  padding: 9px 10px;
  font-size: 13px;
  outline: none;
  width: 100%;
  box-sizing: border-box;
}

.am-field input:focus,
.am-field textarea:focus,
.am-field select:focus {
  border-color: var(--accent);
}

.am-field textarea {
  resize: vertical;
}

.am-icon-area {
  gap: 10px;
}

.am-icon-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: var(--surface-1);
  border-radius: var(--radius-card);
}

.am-icon-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(38px, 1fr));
  gap: 6px;
  max-height: 140px;
  overflow-y: auto;
  background: var(--surface-1);
  padding: 8px;
  border-radius: var(--radius-button);
}

.am-icon-choice {
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  background: transparent;
  border-radius: var(--radius-button);
  color: var(--text-secondary);
  cursor: pointer;
}

.am-icon-choice:hover {
  color: var(--text-primary);
  background: var(--surface-3);
}

.am-icon-choice.active {
  border-color: var(--accent);
  color: var(--accent);
}

.am-error {
  color: #ff4d4f;
  font-size: 13px;
}

@media (max-width: 900px) and (min-width: 601px) {
  .achievements-manager {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
    min-height: 480px;
  }
  .am-sidebar { max-height: 260px; }
  .am-sidebar-head {
    padding: 10px;
    gap: 6px;
  }
  .am-search input {
    font-size: 12px;
    padding: 7px 0;
  }
  .am-create-btn {
    padding: 7px 10px;
    font-size: 12px;
  }
  .am-list {
    padding: 6px;
  }
  .am-item {
    padding: 8px;
    gap: 8px;
  }
  .am-item-icon {
    width: 36px;
    height: 36px;
  }
  .am-item-name {
    font-size: 12px;
  }
  .am-item-meta {
    font-size: 10px;
  }
  .am-main {
    padding: 16px;
  }
  .am-editor-head h3 {
    font-size: 15px;
  }
  .am-btn {
    padding: 7px 12px;
    font-size: 12px;
  }
  .am-btn.small {
    padding: 5px 9px;
    font-size: 11px;
  }
  .am-row {
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 140px), 1fr));
    gap: 10px;
  }
  .am-value {
    max-width: 110px;
  }
  .am-field input[type="text"],
  .am-field input[type="number"],
  .am-field textarea,
  .am-field select {
    padding: 8px 9px;
    font-size: 12px;
  }
  .am-icon-preview {
    width: 56px;
    height: 56px;
  }
  .am-icon-grid {
    grid-template-columns: repeat(auto-fill, minmax(34px, 1fr));
    max-height: 120px;
    gap: 5px;
    padding: 6px;
  }
  .am-icon-choice {
    height: 34px;
  }
}

@media (max-width: 600px) {
  .achievements-manager {
    grid-template-columns: 1fr;
    gap: 10px;
    min-height: auto;
  }
  .am-sidebar {
    max-height: 340px;
  }
  .am-sidebar-head {
    padding: 10px;
    gap: 6px;
    flex-wrap: wrap;
  }
  .am-search {
    flex: 1 1 100%;
    order: 1;
  }
  .am-search input {
    font-size: 12px;
    padding: 8px 0;
  }
  .am-create-btn {
    order: 2;
    flex: 1 1 100%;
    justify-content: center;
    padding: 8px 12px;
    font-size: 13px;
  }
  .am-list {
    padding: 6px;
  }
  .am-item {
    padding: 8px;
    gap: 8px;
  }
  .am-item-icon {
    width: 36px;
    height: 36px;
  }
  .am-item-name {
    font-size: 12px;
  }
  .am-item-meta {
    font-size: 10px;
  }
  .am-sidebar-footer {
    padding: 8px 10px;
    font-size: 11px;
  }
  .am-main {
    padding: 12px;
    min-height: 300px;
  }
  .am-main-empty p {
    font-size: 13px;
  }
  .am-editor {
    gap: 12px;
  }
  .am-editor-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .am-editor-head h3 {
    font-size: 15px;
  }
  .am-head-actions {
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
  }
  .am-btn {
    padding: 7px 11px;
    font-size: 12px;
  }
  .am-btn.small {
    padding: 6px 10px;
    font-size: 11px;
    flex: 1 1 auto;
    justify-content: center;
  }
  .am-form {
    gap: 12px;
  }
  .am-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .am-value {
    max-width: 100%;
  }
  .am-field input[type="text"],
  .am-field input[type="number"],
  .am-field textarea,
  .am-field select {
    padding: 9px 10px;
    font-size: 13px;
  }
  .am-icon-preview {
    width: 56px;
    height: 56px;
  }
  .am-icon-grid {
    grid-template-columns: repeat(auto-fill, minmax(38px, 1fr));
    max-height: 150px;
    gap: 6px;
    padding: 8px;
  }
  .am-icon-choice {
    height: 38px;
  }
  .am-error {
    font-size: 12px;
  }
}

@media (max-width: 380px) {
  .achievements-manager {
    gap: 8px;
  }
  .am-sidebar-head {
    padding: 8px;
  }
  .am-create-btn {
    padding: 7px 10px;
    font-size: 12px;
  }
  .am-item {
    padding: 7px;
    gap: 6px;
  }
  .am-item-icon {
    width: 32px;
    height: 32px;
  }
  .am-item-icon svg {
    width: 18px;
    height: 18px;
  }
  .am-item-name {
    font-size: 11px;
  }
  .am-item-meta {
    font-size: 9px;
  }
  .am-main {
    padding: 10px;
  }
  .am-editor-head h3 {
    font-size: 14px;
  }
  .am-btn {
    padding: 6px 9px;
    font-size: 11px;
  }
  .am-btn.small {
    padding: 5px 8px;
    font-size: 10px;
  }
  .am-field label {
    font-size: 11px;
  }
  .am-field input[type="text"],
  .am-field input[type="number"],
  .am-field textarea,
  .am-field select {
    padding: 8px 9px;
    font-size: 12px;
  }
  .am-icon-preview {
    width: 48px;
    height: 48px;
  }
  .am-icon-grid {
    grid-template-columns: repeat(auto-fill, minmax(32px, 1fr));
    max-height: 130px;
    gap: 5px;
    padding: 6px;
  }
  .am-icon-choice {
    height: 32px;
  }
  .am-icon-choice svg {
    width: 16px;
    height: 16px;
  }
}
</style>
