<template>
  <div class="franchises-manager">
    <header class="fm-header">
      <div class="fm-header-title">
        <div class="fm-header-icon"><SakuraIcon name="network" :size="22" /></div>
        <div>
          <h2>Управление франшизами</h2>
          <p v-if="!selected">Найдите франшизу или создайте новую</p>
          <p v-else>Редактирование: <strong>{{ editing.name || "…" }}</strong></p>
        </div>
      </div>
      <div class="fm-header-actions">
        <button v-if="selected" class="fm-btn" @click="selected = null">
          <SakuraIcon name="arrow-left" :size="15" /> Назад к списку
        </button>
        <button class="fm-btn primary" @click="openCreateForm" :disabled="!!listError">
          <SakuraIcon name="plus" :size="15" /> Новая франшиза
        </button>
        <button class="fm-btn" @click="rebuildFromShikimori" :disabled="rebuildBusy">
          <SakuraIcon name="refresh" :size="15" />
          {{ rebuildLabel }}
        </button>
      </div>
    </header>

    <template v-if="!selected">
      <div class="fm-toolbar">
        <div class="fm-search">
          <SakuraIcon name="search" :size="16" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Поиск по названию..."
            @input="onSearchInput"
          />
          <button
            v-if="searchQuery"
            class="fm-search-clear"
            @click="clearSearch"
            title="Очистить"
          >
            <SakuraIcon name="x" :size="14" />
          </button>
        </div>
        <span class="fm-count">{{ plural(count) }}</span>
      </div>

      <div v-if="listLoading" class="fm-state">
        <SakuraIcon name="hourglass" :size="22" />
        <span>Загрузка франшиз...</span>
      </div>

      <div v-else-if="listError" class="fm-state" role="alert">
        <SakuraIcon name="warning" :size="22" />
        <span>{{ listError }}</span>
        <button class="fm-btn" @click="loadList">Повторить</button>
      </div>
      <div v-else-if="franchises.length" class="fm-grid">
        <button
          v-for="f in franchises"
          :key="f.id"
          class="fm-card"
          @click="selectFranchise(f)"
        >
          <div class="fm-card-cover">
            <img v-if="f.cover" :src="f.cover" :alt="f.name" loading="lazy" />
            <div v-else class="fm-card-cover-ph">
              <SakuraIcon name="network" :size="26" />
            </div>
            <span v-if="f.parts_count" class="fm-card-badge">
              <SakuraIcon name="film" :size="11" /> {{ f.parts_count }}
            </span>
          </div>
          <div class="fm-card-body">
            <span class="fm-card-name">{{ f.name }}</span>
            <span class="fm-card-meta">
              <template v-if="f.year_start">
                {{ f.year_start
                }}<template v-if="f.year_end && f.year_end !== f.year_start"
                  >–{{ f.year_end }}</template
                >
              </template>
              <template v-if="f.score"> · <SakuraIcon name="star" :size="16" /> {{ Number(f.score).toFixed(2) }}</template>
              <template v-if="!f.year_start && !f.score">&nbsp;</template>
            </span>
          </div>
        </button>
      </div>

      <div v-else class="fm-state">
        <SakuraIcon name="search" :size="22" />
        <span>Франшизы не найдены</span>
      </div>

      <div v-if="count > pageSize" class="fm-pager">
        <button class="fm-btn" :disabled="page <= 1 || listLoading" @click="loadPage(page - 1)">
          <SakuraIcon name="arrow-left" :size="16" /> Предыдущая
        </button>
        <span class="fm-paging">{{ page }} / {{ totalPages }}</span>
        <button class="fm-btn" :disabled="page >= totalPages || listLoading" @click="loadPage(page + 1)">
          Следующая <SakuraIcon name="arrow-right" :size="16" />
        </button>
      </div>
    </template>

    <template v-else>
      <div v-if="detailLoading" class="fm-state">
        <SakuraIcon name="hourglass" :size="22" />
        <span>Загрузка франшизы...</span>
      </div>

      <div v-else class="fm-editor">
        <section class="fm-card fm-main-card">
          <div class="fm-main-top">
            <div class="fm-cover">
              <img v-if="selected.cover" :src="selected.cover" :alt="editing.name" />
              <div v-else class="fm-cover-ph"><SakuraIcon name="network" :size="28" /></div>
            </div>
            <div class="fm-main-fields">
              <label class="fm-field">
                <span class="fm-field-label">Название франшизы</span>
                <input
                  v-model="editing.name"
                  type="text"
                  class="fm-input fm-input-name"
                  placeholder="Введите название"
                  @keyup.enter="saveDetails"
                />
              </label>
              <label class="fm-field">
                <span class="fm-field-label">Описание</span>
                <textarea
                  v-model="editing.description"
                  class="fm-input"
                  rows="3"
                  placeholder="Короткое описание франшизы"
                ></textarea>
              </label>
            </div>
          </div>

          <div class="fm-main-actions">
            <div class="fm-meta">
              <span class="fm-chip">
                <SakuraIcon name="film" :size="12" /> {{ selected.entries.length }} частей
              </span>
              <span v-if="selected.score" class="fm-chip score">
                <SakuraIcon name="star" :size="12" /> {{ Number(selected.score).toFixed(2) }}
              </span>
              <span v-if="selected.year_start" class="fm-chip">
                <SakuraIcon name="calendar" :size="12" />
                {{ selected.year_start
                }}<template
                  v-if="selected.year_end && selected.year_end !== selected.year_start"
                  >–{{ selected.year_end }}</template
                >
              </span>
              <span v-if="selected.genres?.length" class="fm-chip genres">
                {{ selected.genres.slice(0, 4).join(", ") }}
                <template v-if="selected.genres.length > 4"> +{{ selected.genres.length - 4 }}</template>
              </span>
            </div>
            <div class="fm-main-btns">
              <button class="fm-btn danger" :disabled="busy" @click="deleteOpen = true">
                <SakuraIcon name="trash" :size="14" /> Удалить
              </button>
              <button class="fm-btn primary" @click="saveDetails" :disabled="saveBusy">
                <SakuraIcon name="save" :size="14" />
                {{ saveBusy ? "Сохранение..." : "Сохранить" }}
              </button>
            </div>
          </div>
        </section>

        <section class="fm-card">
          <div class="fm-section-head">
            <div class="fm-section-title-w">
              <SakuraIcon name="list" :size="16" />
              <h3>Состав франшизы</h3>
              <span class="fm-section-count">{{ selected.entries.length }}</span>
            </div>
            <p class="fm-hint">Порядок = порядок просмотра. Используйте стрелки для сортировки.</p>
          </div>

          <div v-if="selected.entries.length" class="fm-entries">
            <div
              v-for="(e, idx) in selected.entries"
              :key="e.id"
              class="fm-entry"
              :class="{ moving: movingId === e.id }"
            >
              <span class="fm-order-num">{{ idx + 1 }}</span>
              <div class="fm-entry-poster">
                <img v-if="e.poster_url" :src="e.poster_url" :alt="e.title_ru" loading="lazy" />
                <SakuraIcon v-else name="film" :size="16" />
              </div>
              <div class="fm-entry-info">
                <router-link :to="`/anime/${e.slug || e.id}`" class="fm-entry-title">
                  {{ e.title_ru }}
                </router-link>
                <div class="fm-entry-meta">
                  <span v-if="e.year">{{ e.year }}</span>
                  <span v-if="e.kind">{{ e.kind }}</span>
                  <template v-if="e.episodes && e.episodes > 0"
                    ><span>{{ e.episodes }} эп.</span></template
                  >
                  <span v-if="e.status">{{ e.status }}</span>
                  <span v-if="e.score" class="fm-score"><SakuraIcon name="star" :size="16" /> {{ Number(e.score).toFixed(1) }}</span>
                </div>
              </div>
              <div class="fm-entry-actions">
                <button
                  class="fm-tool"
                  :disabled="idx === 0 || busy"
                  @click="moveEntry(idx, -1)"
                  title="Поднять выше"
                >
                  <SakuraIcon name="arrow-up" :size="14" />
                </button>
                <button
                  class="fm-tool"
                  :disabled="idx === selected.entries.length - 1 || busy"
                  @click="moveEntry(idx, 1)"
                  title="Опустить ниже"
                >
                  <SakuraIcon name="arrow-down" :size="14" />
                </button>
                <button
                  class="fm-tool danger"
                  :disabled="busy"
                  @click="removeEntry(e.id)"
                  title="Убрать из франшизы"
                >
                  <SakuraIcon name="trash" :size="14" />
                </button>
              </div>
            </div>
          </div>

          <div v-else class="fm-empty">
            <SakuraIcon name="network" :size="26" />
            <span>Пока пусто -найдите аниме ниже и добавьте его в франшизу</span>
          </div>
        </section>

        <section class="fm-card">
          <div class="fm-section-head">
            <div class="fm-section-title-w">
              <SakuraIcon name="search" :size="16" />
              <h3>Добавить аниме</h3>
            </div>
            <p class="fm-hint">Введите минимум 2 символа</p>
          </div>

          <div class="fm-add-search">
            <SakuraIcon name="search" :size="16" />
            <input
              v-model="addQuery"
              type="text"
              placeholder="Поиск по названию..."
              @input="onAddSearch"
            />
          </div>

          <div v-if="addLoading" class="fm-add-state">
            <SakuraIcon name="hourglass" :size="16" /> Поиск...
          </div>

          <div v-else-if="addResults.length" class="fm-add-results">
            <div
              v-for="a in addResults"
              :key="a.id"
              class="fm-add-result"
              :class="{ added: isInSelected(a.id) }"
            >
              <div class="fm-add-poster">
                <img v-if="a.poster_url" :src="a.poster_url" :alt="a.title_ru" loading="lazy" />
                <SakuraIcon v-else name="film" :size="14" />
              </div>
              <div class="fm-add-result-info">
                <span class="fm-add-result-title">{{ a.title_ru }}</span>
                <div class="fm-add-result-meta">
                  <span v-if="a.year">{{ a.year }}</span>
                  <span v-if="a.kind">{{ a.kind }}</span>
                  <span v-if="a.score"><SakuraIcon name="star" :size="16" /> {{ Number(a.score).toFixed(1) }}</span>
                </div>
                <span
                  v-if="a.franchise && a.franchise.id !== selected.id"
                  class="fm-add-result-cur"
                >
                  уже в «{{ a.franchise.name }}»
                </span>
              </div>
              <button
                class="fm-add-btn"
                :disabled="busy || isInSelected(a.id)"
                @click="addEntry(a.id)"
                :title="isInSelected(a.id) ? 'Уже в составе' : 'Добавить в франшизу'"
              >
                <SakuraIcon :name="isInSelected(a.id) ? 'check' : 'plus'" :size="16" />
              </button>
            </div>
          </div>

          <div v-else-if="addQuery.length >= 2" class="fm-add-state muted">
            Ничего не найдено
          </div>
        </section>
      </div>
    </template>

    <BaseModal
      :show="createOpen"
      @update:show="(v: boolean) => (createOpen = v)"
      title="Новая франшиза"
      size="small"
    >
      <div class="fm-modal-body">
        <label class="fm-field">
          <span class="fm-field-label">Название</span>
          <input
            v-model="createName"
            type="text"
            class="fm-input"
            placeholder="Например: Re:Zero"
            ref="createInput"
            @keyup.enter="createFranchise"
          />
        </label>
        <label class="fm-field">
          <span class="fm-field-label">Описание <i>необязательно</i></span>
          <textarea
            v-model="createDescription"
            class="fm-input"
            rows="3"
            placeholder="Короткое описание"
          ></textarea>
        </label>
      </div>
      <template #footer>
        <button class="fm-btn" :disabled="createBusy" @click="createOpen = false">Отмена</button>
        <button class="fm-btn primary" :disabled="createBusy || !createName.trim()" @click="createFranchise">
          {{ createBusy ? "Создание..." : "Создать" }}
        </button>
      </template>
    </BaseModal>

    <BaseModal
      :show="deleteOpen"
      @update:show="(v: boolean) => (deleteOpen = v)"
      title="Удалить франшизу?"
      size="small"
    >
      <div class="fm-modal-body">
        <p class="fm-delete-text">
          Франшиза <strong>«{{ editing.name }}»</strong> будет удалена. Аниме из неё
          не удаляются -они просто останутся без привязки к франшизе.
        </p>
      </div>
      <template #footer>
        <button class="fm-btn" :disabled="busy" @click="deleteOpen = false">Отмена</button>
        <button class="fm-btn danger-solid" :disabled="busy" @click="confirmDelete">
          {{ busy ? "Удаление..." : "Удалить" }}
        </button>
      </template>
    </BaseModal>

    <transition name="toast">
      <div v-if="toast.visible" class="fm-toast" :class="toast.type">
        <SakuraIcon :name="toast.icon" :size="15" />
        {{ toast.text }}
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted, watch } from "vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import BaseModal from "@/components/ui/BaseModal.vue";
import adminApi, {
  type AdminFranchiseSummary,
  type AdminFranchiseDetail,
  type AdminAnimeSearchResult,
} from "@/api/adminFranchises";

const pageSize = 25;

const franchises = ref<AdminFranchiseSummary[]>([]);
const count = ref(0);
const page = ref(1);
const totalPages = computed(() => Math.max(1, Math.ceil(count.value / pageSize)));

const listLoading = ref(false);
const listError = ref('');
const rebuildBusy = ref(false);
const rebuildProgress = ref<number | null>(null);
const rebuildLabel = computed(() => {
  if (!rebuildBusy.value) return "Пересобрать из Shikimori";
  return rebuildProgress.value === null
    ? "Запускаем…"
    : `Пересборка: ${rebuildProgress.value}%`;
});
let rebuildPollingCancelled = false;
const searchQuery = ref("");
let searchDebounce: ReturnType<typeof setTimeout> | null = null;

const loadList = async () => {
  listLoading.value = true;
  listError.value = '';
  try {
    const { data } = await adminApi.list({
      search: searchQuery.value.trim() || undefined,
      page: page.value,
      page_size: pageSize,
    });
    franchises.value = data.results || [];
    count.value = data.count ?? 0;
  } catch (e) {
    console.error("load franchises:", e);
    franchises.value = [];
    count.value = 0;
    listError.value = 'Редактор франшиз сейчас недоступен. Не удалось загрузить данные.';
    showToast("Не удалось загрузить франшизы", "x", "error");
  } finally {
    listLoading.value = false;
  }
};

const loadPage = (p: number) => {
  if (p < 1) return;
  page.value = p;
  loadList();
};

const onSearchInput = () => {
  if (searchDebounce) clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    page.value = 1;
    loadList();
  }, 350);
};

const clearSearch = () => {
  searchQuery.value = "";
  page.value = 1;
  loadList();
};

const rebuildFromShikimori = async () => {
  if (rebuildBusy.value) return;
  rebuildBusy.value = true;
  rebuildProgress.value = null;
  rebuildPollingCancelled = false;
  try {
    const { data } = await adminApi.rebuild();
    showToast(`Пересборка запущена: ${data.anime_scheduled} аниме в очереди`);
    if (!data.rebuild_id) {
      setTimeout(() => loadList(), 3000);
      return;
    }
    let rebuildId = data.rebuild_id;
    while (!rebuildPollingCancelled) {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      if (rebuildPollingCancelled) return;
      const { data: status } = await adminApi.rebuildStatus(rebuildId);
      if (status.rebuild_id) rebuildId = status.rebuild_id;
      rebuildProgress.value = status.total > 0
        ? Math.min(100, Math.round((status.processed / status.total) * 100))
        : 100;
      if (status.state === "completed") {
        await loadList();
        showToast(status.message || "Франшизы пересобраны");
        return;
      }
      if (status.state === "failed") {
        showToast(status.message || "Пересборка остановлена", "x", "error");
        return;
      }
    }
  } catch (error) {
    console.error("rebuild franchises:", error);
    showToast("Не удалось выполнить пересборку", "x", "error");
  } finally {
    rebuildBusy.value = false;
    rebuildProgress.value = null;
  }
};

onUnmounted(() => {
  rebuildPollingCancelled = true;
});

const createOpen = ref(false);
const createName = ref("");
const createDescription = ref("");
const createBusy = ref(false);
const createInput = ref<HTMLInputElement | null>(null);

const openCreateForm = () => {
  createName.value = "";
  createDescription.value = "";
  createOpen.value = true;
  nextTick(() => createInput.value?.focus());
};

const createFranchise = async () => {
  const name = createName.value.trim();
  if (!name || createBusy.value) return;
  createBusy.value = true;
  try {
    const { data } = await adminApi.create({
      name,
      description: createDescription.value.trim() || undefined,
    });
    createOpen.value = false;
    searchQuery.value = "";
    page.value = 1;
    await loadList();
    await selectFranchise(data);
    showToast("Франшиза создана");
  } catch (e) {
    console.error("create franchise:", e);
    showToast("Не удалось создать франшизу", "x", "error");
  } finally {
    createBusy.value = false;
  }
};

const selected = ref<AdminFranchiseDetail | null>(null);
const detailLoading = ref(false);
const busy = ref(false);
const saveBusy = ref(false);
const editing = ref({ name: "", description: "" });

const selectFranchise = async (f: AdminFranchiseSummary) => {
  detailLoading.value = true;
  try {
    const { data } = await adminApi.detail(f.id);
    selected.value = data;
    editing.value = {
      name: data.name || "",
      description: data.description || "",
    };
  } catch (e) {
    console.error("load franchise detail:", e);
    selected.value = null;
    showToast("Не удалось загрузить франшизу", "x", "error");
  } finally {
    detailLoading.value = false;
  }
};

const saveDetails = async () => {
  if (!selected.value || saveBusy.value) return;
  const name = editing.value.name.trim();
  if (!name) {
    showToast("Название не может быть пустым", "x", "error");
    return;
  }
  saveBusy.value = true;
  try {
    await adminApi.update(selected.value.id, {
      name,
      description: editing.value.description,
    });
    selected.value.name = name;
    selected.value.description = editing.value.description;
    await loadList();
    showToast("Изменения сохранены");
  } catch (e) {
    console.error("save franchise:", e);
    showToast("Не удалось сохранить", "x", "error");
  } finally {
    saveBusy.value = false;
  }
};

const deleteOpen = ref(false);

const confirmDelete = async () => {
  if (!selected.value || busy.value) return;
  busy.value = true;
  try {
    const name = selected.value.name;
    await adminApi.remove(selected.value.id);
    deleteOpen.value = false;
    selected.value = null;
    await loadList();
    showToast(`Франшиза «${name}» удалена`);
  } catch (e) {
    console.error("delete franchise:", e);
    showToast("Не удалось удалить франшизу", "x", "error");
  } finally {
    busy.value = false;
  }
};

const movingId = ref<number | null>(null);

const applyDetail = (data: AdminFranchiseDetail) => {
  selected.value = data;
  editing.value = {
    name: data.name || editing.value.name,
    description: data.description ?? editing.value.description,
  };
};

const addEntry = async (animeId: number) => {
  if (!selected.value || busy.value) return;
  busy.value = true;
  try {
    const { data } = await adminApi.addAnime(selected.value.id, animeId);
    applyDetail(data);
    addQuery.value = "";
    addResults.value = [];
    showToast("Аниме добавлено в франшизу");
  } catch (e) {
    console.error("add to franchise:", e);
    showToast("Не удалось добавить аниме", "x", "error");
  } finally {
    busy.value = false;
  }
};

const removeEntry = async (animeId: number) => {
  if (!selected.value || busy.value) return;
  busy.value = true;
  try {
    const { data } = await adminApi.removeAnime(selected.value.id, animeId);
    applyDetail(data);
    showToast("Аниме убрано из франшизы");
  } catch (e) {
    console.error("remove from franchise:", e);
    showToast("Не удалось убрать аниме", "x", "error");
  } finally {
    busy.value = false;
  }
};

const moveEntry = async (idx: number, dir: -1 | 1) => {
  if (!selected.value || busy.value) return;
  const target = idx + dir;
  if (target < 0 || target >= selected.value.entries.length) return;

  const next = [...selected.value.entries];
  const item = next[idx];
  if (!item) return;
  next.splice(idx, 1);
  next.splice(target, 0, item);

  movingId.value = item.id;
  busy.value = true;
  try {
    const { data } = await adminApi.reorder(
      selected.value.id,
      next.map((e) => e.id),
    );
    applyDetail(data);
    showToast("Порядок сохранён");
  } catch (e) {
    console.error("reorder franchise:", e);
    showToast("Не удалось изменить порядок", "x", "error");
  } finally {
    busy.value = false;
    movingId.value = null;
  }
};

const addQuery = ref("");
const addResults = ref<AdminAnimeSearchResult[]>([]);
const addLoading = ref(false);
let addDebounce: ReturnType<typeof setTimeout> | null = null;

const isInSelected = (id: number) =>
  !!selected.value?.entries.some((e) => e.id === id);

const onAddSearch = () => {
  if (addDebounce) clearTimeout(addDebounce);
  addDebounce = setTimeout(runAddSearch, 300);
};

const runAddSearch = async () => {
  const q = addQuery.value.trim();
  addResults.value = [];
  if (q.length < 2) return;
  addLoading.value = true;
  try {
    const { data } = await adminApi.searchAnime(q);
    const res = data.results || [];
    const seen = new Set<number>();
    addResults.value = res.filter((a) => {
      if (seen.has(a.id)) return false;
      seen.add(a.id);
      return true;
    });
  } catch (e) {
    console.error("search anime:", e);
  } finally {
    addLoading.value = false;
  }
};

type ToastType = "success" | "error";
const toast = ref<{ visible: boolean; text: string; icon: string; type: ToastType }>({
  visible: false,
  text: "",
  icon: "check",
  type: "success",
});
let toastTimer: ReturnType<typeof setTimeout> | null = null;

const showToast = (text: string, icon = "check", type: ToastType = "success") => {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { visible: true, text, icon, type };
  toastTimer = setTimeout(() => (toast.value.visible = false), 3000);
};

const plural = (n: number) => {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return `${n} франшиза`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return `${n} франшизы`;
  return `${n} франшиз`;
};

watch(createOpen, (open) => {
  if (!open) createName.value = "";
});

loadList();
</script>

<style scoped>
.franchises-manager {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.fm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  flex-wrap: wrap;
}
.fm-header-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.fm-header-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-subtle);
  color: var(--accent-bright);
  border-radius: var(--radius-lg);
  flex-shrink: 0;
}
.fm-header-title h2 {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
}
.fm-header-title p {
  margin: 2px 0 0;
  font-size: var(--text-sm);
  color: var(--text-tertiary);
}
.fm-header-title p strong {
  color: var(--text-secondary);
}
.fm-header-actions {
  display: flex;
  gap: var(--space-2);
}

.fm-toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.fm-search {
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 42px;
  padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-tertiary);
  transition:
    border-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.fm-search:focus-within {
  border-color: var(--border-focus);
  box-shadow: var(--border-glow);
}
.fm-search input {
  flex: 1;
  min-width: 0;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: inherit;
}
.fm-search-clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--surface-4);
  color: var(--text-tertiary);
  cursor: pointer;
  transition:
    color var(--duration-base) var(--ease-out),
    background var(--duration-base) var(--ease-out);
}
.fm-search-clear:hover {
  color: var(--text-primary);
  background: var(--surface-5);
}
.fm-count {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  white-space: nowrap;
}

.fm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: var(--space-4);
}

.fm-card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 0;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  text-align: left;
  font-family: var(--font-sans);
  transition:
    transform var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);
}
.fm-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-default);
  box-shadow: var(--shadow-sm-glow-sm);
}

.fm-card-cover {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  background: var(--surface-4);
  overflow: hidden;
}
.fm-card-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.fm-card-cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-disabled);
}
.fm-card-badge {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--text-on-accent, #fff);
  background: color-mix(in srgb, var(--accent) 88%, black);
  border-radius: var(--radius-full);
  backdrop-filter: blur(4px);
}
.fm-card-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
  min-width: 0;
}
.fm-card-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fm-card-meta {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fm-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding-top: var(--space-2);
}
.fm-paging {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  min-width: 60px;
  text-align: center;
}

.fm-editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.fm-main-card {
  background: var(--surface-3);
}
.fm-main-top {
  display: flex;
  gap: var(--space-5);
  flex-wrap: wrap;
}
.fm-cover {
  width: 130px;
  flex: 0 0 130px;
  aspect-ratio: 2 / 3;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--surface-4);
}
.fm-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.fm-cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-disabled);
}
.fm-main-fields {
  flex: 1;
  min-width: 260px;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.fm-main-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  flex-wrap: wrap;
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}
.fm-meta {
  display: flex;
  gap: var(--space-2);
  flex-wrap: wrap;
}
.fm-main-btns {
  display: flex;
  gap: var(--space-2);
  margin-left: auto;
}

.fm-card {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}

.fm-section-head {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: var(--space-4);
}
.fm-section-title-w {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-secondary);
}
.fm-section-title-w h3 {
  margin: 0;
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--text-primary);
}
.fm-section-count {
  font-size: var(--text-xs);
  font-weight: 700;
  color: var(--accent-bright);
  background: var(--accent-subtle);
  border-radius: var(--radius-full);
  padding: 2px 10px;
}
.fm-hint {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.fm-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.fm-field-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.fm-field-label i {
  font-style: normal;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--text-disabled);
}
.fm-input {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-sans);
  resize: vertical;
  transition:
    border-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.fm-input:focus {
  outline: none;
  border-color: var(--border-focus);
  box-shadow: var(--border-glow);
}
.fm-input-name {
  font-size: var(--text-lg);
  font-weight: 700;
}

.fm-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--text-tertiary);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-full);
  padding: 5px 12px;
}
.fm-chip.score {
  color: var(--warning);
}
.fm-chip.genres {
  color: var(--accent-bright);
}

.fm-entries {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.fm-entry {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition:
    opacity var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);
}
.fm-entry.moving {
  opacity: 0.45;
  border-color: var(--border-strong);
}
.fm-order-num {
  flex: 0 0 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--accent-bright);
  background: var(--accent-subtle);
  border-radius: var(--radius-sm);
  height: 26px;
}
.fm-entry-poster {
  width: 40px;
  flex: 0 0 40px;
  aspect-ratio: 2 / 3;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface-4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}
.fm-entry-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.fm-entry-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.fm-entry-title {
  color: var(--text-primary);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--duration-base) var(--ease-out);
}
.fm-entry-title:hover {
  color: var(--accent-bright);
}
.fm-entry-meta {
  display: flex;
  gap: var(--space-1);
  flex-wrap: wrap;
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
.fm-entry-meta span {
  background: var(--surface-4);
  padding: 1px 7px;
  border-radius: 5px;
}
.fm-entry-meta .fm-score {
  color: var(--warning);
}
.fm-entry-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.fm-tool {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 0;
  transition:
    color var(--duration-base) var(--ease-out),
    background var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out);
}
.fm-tool:hover:not(:disabled) {
  color: var(--text-primary);
  background: var(--surface-5);
  border-color: var(--border-default);
}
.fm-tool.danger:hover:not(:disabled) {
  color: var(--danger);
  background: var(--danger-subtle);
  border-color: var(--danger);
}
.fm-tool:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.fm-empty {
  padding: var(--space-6);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  background: var(--surface-3);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.fm-state {
  padding: var(--space-12) var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-md);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.fm-add-search {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  height: 42px;
  padding: 0 var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--text-tertiary);
  margin-bottom: var(--space-3);
  transition:
    border-color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.fm-add-search:focus-within {
  border-color: var(--border-focus);
  box-shadow: var(--border-glow);
}
.fm-add-search input {
  flex: 1;
  min-width: 0;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: inherit;
}
.fm-add-state {
  padding: var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
}
.fm-add-state.muted {
  background: var(--surface-3);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-md);
}
.fm-add-results {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-height: 360px;
  overflow-y: auto;
  scrollbar-width: thin;
}
.fm-add-result {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition: opacity var(--duration-base) var(--ease-out);
}
.fm-add-result.added {
  opacity: 0.5;
}
.fm-add-poster {
  width: 32px;
  flex: 0 0 32px;
  aspect-ratio: 2 / 3;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--surface-4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}
.fm-add-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.fm-add-result-info {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.fm-add-result-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fm-add-result-meta {
  display: flex;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
.fm-add-result-meta span {
  background: var(--surface-4);
  padding: 1px 7px;
  border-radius: 5px;
}
.fm-add-result-cur {
  font-size: var(--text-xs);
  color: var(--warning);
}
.fm-add-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  background: var(--success-subtle);
  color: var(--success);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out);
}
.fm-add-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: scale(1.06);
}
.fm-add-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.fm-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 38px;
  padding: 0 var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 600;
  font-family: var(--font-sans);
  cursor: pointer;
  white-space: nowrap;
  transition:
    background var(--duration-base) var(--ease-out),
    border-color var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out),
    box-shadow var(--duration-base) var(--ease-out);
}
.fm-btn:hover:not(:disabled) {
  background: var(--surface-5);
  border-color: var(--border-default);
  color: var(--text-primary);
}
.fm-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.fm-btn.primary {
  background: var(--accent-subtle);
  color: var(--accent-bright);
  border-color: transparent;
}
.fm-btn.primary:hover:not(:disabled) {
  background: var(--accent-glow-sm);
  color: var(--accent-bright);
  box-shadow: var(--shadow-sm-glow-sm);
}
.fm-btn.danger {
  background: var(--danger-subtle);
  color: var(--danger);
  border-color: transparent;
}
.fm-btn.danger:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 22%, transparent);
  color: var(--danger);
}
.fm-btn.danger-solid {
  background: var(--danger);
  color: #fff;
  border-color: transparent;
}
.fm-btn.danger-solid:hover:not(:disabled) {
  background: color-mix(in srgb, var(--danger) 82%, black);
  color: #fff;
}

.fm-modal-body {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.fm-delete-text {
  margin: 0;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
}
.fm-delete-text strong {
  color: var(--text-primary);
}

.fm-toast {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-toast, 1400);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 11px 18px;
  background: var(--surface-4);
  border: 1px solid var(--border-strong);
  border-radius: var(--radius-full);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  box-shadow: var(--shadow-sm-modal);
}
.fm-toast.success {
  border-color: var(--success);
  color: var(--success);
}
.fm-toast.error {
  border-color: var(--danger);
  color: var(--danger);
}
.toast-enter-active {
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out);
}
.toast-leave-active {
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-base) var(--ease-out);
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(12px);
}

@media (max-width: 640px) {
  .fm-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  }
  .fm-main-top {
    flex-direction: column;
  }
  .fm-cover {
    width: 100%;
    aspect-ratio: 16 / 9;
    flex: none;
  }
  .fm-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 374px) {
  .franchises-manager {
    gap: var(--space-3);
  }

  .fm-header {
    gap: var(--space-2);
  }

  .fm-header-title {
    gap: var(--space-2);
  }

  .fm-header-icon {
    width: 34px;
    height: 34px;
    border-radius: var(--radius-md);
  }

  .fm-header-icon svg {
    width: 18px;
    height: 18px;
  }

  .fm-header-title h2 {
    font-size: var(--text-md);
  }

  .fm-header-title p {
    font-size: var(--text-xs);
  }

  .fm-header-actions {
    width: 100%;
    gap: var(--space-1);
  }

  .fm-header-actions .fm-btn {
    flex: 1;
    padding: 0 var(--space-2);
    font-size: var(--text-xs);
    height: 34px;
  }

  .fm-toolbar {
    gap: var(--space-2);
  }

  .fm-search {
    min-width: 100%;
    height: 38px;
    padding: 0 var(--space-2);
  }

  .fm-search input {
    font-size: var(--text-xs);
  }

  .fm-count {
    font-size: var(--text-xs);
  }

  .fm-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-2);
  }

  .fm-card-body {
    padding: var(--space-2);
  }

  .fm-card-name {
    font-size: var(--text-xs);
  }

  .fm-card-meta {
    font-size: 10px;
  }

  .fm-card-badge {
    font-size: 9px;
    padding: 2px 6px;
  }

  .fm-pager {
    flex-wrap: wrap;
    gap: var(--space-2);
  }

  .fm-pager .fm-btn {
    flex: 1;
    padding: 0 var(--space-2);
    font-size: var(--text-xs);
    height: 34px;
  }

  .fm-paging {
    order: -1;
    min-width: 100%;
    text-align: center;
    font-size: var(--text-xs);
  }

  .fm-card {
    padding: var(--space-3);
    border-radius: var(--radius-lg);
  }

  .fm-main-top {
    gap: var(--space-3);
  }

  .fm-cover {
    border-radius: var(--radius-md);
  }

  .fm-main-fields {
    min-width: 0;
    gap: var(--space-2);
  }

  .fm-field-label {
    font-size: 10px;
  }

  .fm-input {
    padding: 8px 10px;
    font-size: var(--text-xs);
  }

  .fm-input-name {
    font-size: var(--text-md);
  }

  .fm-main-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-2);
    margin-top: var(--space-3);
    padding-top: var(--space-3);
  }

  .fm-meta {
    gap: var(--space-1);
  }

  .fm-chip {
    font-size: 10px;
    padding: 3px 8px;
    gap: 3px;
  }

  .fm-main-btns {
    margin-left: 0;
    width: 100%;
    gap: var(--space-1);
  }

  .fm-main-btns .fm-btn {
    flex: 1;
    padding: 0 var(--space-2);
    font-size: var(--text-xs);
    height: 34px;
  }

  .fm-section-head {
    margin-bottom: var(--space-3);
  }

  .fm-section-title-w h3 {
    font-size: var(--text-sm);
  }

  .fm-hint {
    font-size: 10px;
  }

  .fm-entry {
    gap: var(--space-2);
    padding: var(--space-2);
    flex-wrap: wrap;
  }

  .fm-order-num {
    flex: 0 0 22px;
    height: 22px;
    font-size: var(--text-xs);
  }

  .fm-entry-poster {
    width: 32px;
    flex: 0 0 32px;
  }

  .fm-entry-info {
    min-width: 0;
    flex: 1 1 calc(100% - 90px);
  }

  .fm-entry-title {
    font-size: var(--text-xs);
  }

  .fm-entry-meta {
    font-size: 10px;
    gap: 3px;
  }

  .fm-entry-meta span {
    padding: 1px 5px;
  }

  .fm-entry-actions {
    flex: 1 1 100%;
    justify-content: flex-end;
    margin-left: 0;
    gap: 4px;
  }

  .fm-tool {
    width: 28px;
    height: 28px;
  }

  .fm-empty {
    padding: var(--space-4);
    font-size: var(--text-xs);
  }

  .fm-state {
    padding: var(--space-6) var(--space-3);
    font-size: var(--text-sm);
  }

  .fm-add-search {
    height: 38px;
    padding: 0 var(--space-2);
  }

  .fm-add-search input {
    font-size: var(--text-xs);
  }

  .fm-add-result {
    gap: var(--space-2);
    padding: var(--space-2);
  }

  .fm-add-poster {
    width: 28px;
    flex: 0 0 28px;
  }

  .fm-add-result-title {
    font-size: var(--text-xs);
  }

  .fm-add-result-meta {
    font-size: 10px;
  }

  .fm-add-btn {
    width: 30px;
    height: 30px;
    flex: 0 0 30px;
  }

  .fm-toast {
    bottom: 16px;
    left: 12px;
    right: 12px;
    transform: none;
    font-size: var(--text-xs);
    padding: 9px 14px;
    justify-content: center;
  }

  .toast-enter-from,
  .toast-leave-to {
    transform: translateY(12px);
  }
}

@media (min-width: 375px) and (max-width: 767px) {
  .franchises-manager {
    gap: var(--space-3);
  }

  .fm-header {
    gap: var(--space-3);
  }

  .fm-header-icon {
    width: 38px;
    height: 38px;
  }

  .fm-header-title h2 {
    font-size: var(--text-lg);
  }

  .fm-header-actions {
    width: 100%;
    gap: var(--space-2);
  }

  .fm-header-actions .fm-btn {
    flex: 1;
  }

  .fm-search {
    min-width: 100%;
  }

  .fm-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: var(--space-3);
  }

  .fm-pager {
    flex-wrap: wrap;
  }

  .fm-pager .fm-btn {
    flex: 1;
  }

  .fm-paging {
    order: -1;
    min-width: 100%;
    text-align: center;
  }

  .fm-main-actions {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }

  .fm-main-btns {
    margin-left: 0;
    width: 100%;
  }

  .fm-main-btns .fm-btn {
    flex: 1;
  }

  .fm-entry {
    gap: var(--space-2);
    flex-wrap: wrap;
  }

  .fm-entry-info {
    flex: 1 1 calc(100% - 100px);
  }

  .fm-entry-actions {
    flex: 1 1 100%;
    justify-content: flex-end;
    margin-left: 0;
  }

  .fm-toast {
    bottom: 20px;
    left: 16px;
    right: 16px;
    transform: none;
    justify-content: center;
  }

  .toast-enter-from,
  .toast-leave-to {
    transform: translateY(12px);
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .fm-grid {
    grid-template-columns: repeat(auto-fill, minmax(155px, 1fr));
    gap: var(--space-3);
  }

  .fm-header-actions {
    gap: var(--space-2);
  }

  .fm-main-top {
    gap: var(--space-4);
  }

  .fm-cover {
    width: 110px;
    flex: 0 0 110px;
  }

  .fm-main-fields {
    min-width: 220px;
  }

  .fm-add-results {
    max-height: 320px;
  }
}

@media (min-width: 768px) and (max-width: 1023px) and (orientation: landscape) {
  .fm-grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }

  .fm-main-top {
    flex-wrap: nowrap;
  }
}

@media (hover: none) and (pointer: coarse) {
  .fm-card:hover {
    transform: none;
    box-shadow: none;
    border-color: var(--border-subtle);
  }

  .fm-card:active {
    transform: scale(0.99);
    border-color: var(--border-default);
  }

  .fm-btn:hover:not(:disabled) {
    background: var(--surface-4);
    border-color: var(--border-subtle);
    color: var(--text-secondary);
  }

  .fm-btn.primary:hover:not(:disabled) {
    background: var(--accent-subtle);
    box-shadow: none;
  }

  .fm-tool:hover:not(:disabled) {
    color: var(--text-tertiary);
    background: var(--surface-4);
    border-color: var(--border-subtle);
  }

  .fm-tool:active:not(:disabled) {
    background: var(--surface-5);
    color: var(--text-primary);
  }

  .fm-add-btn:hover:not(:disabled) {
    opacity: 1;
    transform: none;
  }

  .fm-add-btn:active:not(:disabled) {
    transform: scale(0.94);
  }

  .fm-add-results {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
}
.fm-entry-info { min-width: 0; }
.fm-entry-title { overflow-wrap: anywhere; }
@media (max-width: 767px) {
  .fm-entry { display: grid; grid-template-columns: 24px 38px minmax(0, 1fr); }
  .fm-entry-actions { grid-column: 2 / 4; justify-content: flex-end; margin-left: 0; }
  .fm-section-head { flex-wrap: wrap; }
  .fm-hint { white-space: normal; overflow-wrap: anywhere; }
}
</style>
