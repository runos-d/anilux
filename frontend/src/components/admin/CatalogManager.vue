<template>
  <div class="catalog-manager">
    <header class="cm-header">
      <div class="cm-header-title">
        <div class="cm-header-icon"><SakuraIcon name="filter" :size="22" /></div>
        <div>
          <h2>Каталог аниме</h2>
          <p>Скрытие аниме и жанров из каталога для всех пользователей</p>
        </div>
      </div>
      <div class="cm-stats">
        <span class="cm-stat"><SakuraIcon name="ban" :size="14" /> Правил: <b>{{ rules.length }}</b></span>
        <span class="cm-stat"><SakuraIcon name="eye-off" :size="14" /> Скрыто: <b>{{ hiddenCount }}</b></span>
      </div>
    </header>

    <section class="cm-card cm-settings">
      <div class="cm-card-head">
        <h3>Настройки каталога</h3>
      </div>
      <label class="cm-toggle-row">
        <span class="cm-toggle-text">
          <span class="cm-toggle-title">Карточки франшиз в главном каталоге</span>
          <span class="cm-toggle-desc">
            Если включено -все части франшизы (например, 53 части Ван-Писа) сворачиваются в одну карточку
            франшизы. Иначе показываются отдельными карточками.
          </span>
        </span>
        <button type="button" class="cm-switch" :class="{ on: settings.groupFranchises }" :aria-pressed="settings.groupFranchises" aria-label="Группировать карточки франшиз" :disabled="busy || !settingsReady" @click="toggleGroupFranchises">
          <span class="cm-switch-thumb" />
        </button>
      </label>
    </section>

    <div v-if="managementError" class="cm-card" role="alert">
      <h3>Управление скрытием сейчас недоступно</h3>
      <p>{{ managementError }}</p>
      <button class="cm-btn" @click="retryManagement">Повторить</button>
    </div>
    <div v-else class="cm-grid">
      <section class="cm-card">
        <div class="cm-card-head">
          <h3>Правила скрытия</h3>
          <span class="cm-count">{{ rules.length }}</span>
        </div>
        <p class="cm-desc">
          Аниме, подпадающие под правило, исчезают из каталога (по жанру, названию, франшизе, типу или студии).
          При удалении правила -аниме, которые больше не подпадают ни под одно правило, автоматически вернутся.
        </p>

        <div class="cm-form">
          <div class="cm-form-row">
            <select v-model="form.rule_type" class="form-control" @change="onRuleTypeChange">
              <option v-for="t in ruleTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
            <template v-if="form.rule_type === 'genre'">
              <div class="cm-genre-picker">
                <div class="cm-genre-picker-top">
                  <div class="cm-search cm-search-sm">
                    <SakuraIcon name="search" :size="14" />
                    <input
                      v-model="genreFilter"
                      class="form-control"
                      type="text"
                      placeholder="Поиск жанра..."
                    />
                  </div>
                  <span v-if="selectedGenres.length" class="cm-count">
                    {{ selectedGenres.length }} выбрано
                  </span>
                </div>
                <div class="cm-genre-list">
                  <button
                    v-for="g in filteredGenreOptions"
                    :key="g"
                    type="button"
                    :class="['cm-genre-chip', { active: selectedGenres.includes(g) }]"
                    @click="toggleGenre(g)"
                  >
                    {{ g }}
                  </button>
                </div>
                <div
                  v-if="!filteredGenreOptions.length"
                  class="empty-state"
                  style="padding: 14px; text-align: center; color: var(--text-tertiary, #9aa); font-size: var(--text-sm, 0.75rem)"
                >
                  Жанры не найдены
                </div>
              </div>
            </template>
            <template v-else-if="form.rule_type === 'studio' || form.rule_type === 'kind'">
              <select v-model="form.value" class="form-control" :disabled="busy">
                <option value="" disabled>Выберите значение...</option>
                <option v-for="opt in valueOptions" :key="opt" :value="opt">{{ opt }}</option>
              </select>
            </template>
            <template v-else>
              <input
                v-model="form.value"
                class="form-control"
                type="text"
                placeholder="Значение (например: Токийский гуль, франшиза...)"
                @keyup.enter="addRule"
              />
            </template>
          </div>
          <input
            v-model="form.note"
            class="form-control"
            type="text"
            placeholder="Комментарий (необязательно)"
          />
          <button class="btn-primary" @click="addRule" :disabled="busy">
            <SakuraIcon v-if="busy" name="spinner" :size="15" />
            <template v-else><SakuraIcon name="ban" :size="15" /></template>
            Добавить правило и скрыть найденные
          </button>
        </div>

        <div v-if="rulesLoading" class="cm-loading">
          <SakuraIcon name="spinner" :size="18" /> Загрузка...
        </div>

        <div v-else-if="rules.length" class="cm-rules">
          <div v-for="r in rules" :key="r.id" class="cm-rule">
            <div class="cm-rule-main">
              <span class="cm-rule-type">{{ r.rule_type_label }}</span>
              <span class="cm-rule-value">{{ r.value }}</span>
              <span v-if="r.note" class="cm-rule-note">{{ r.note }}</span>
            </div>
            <div class="cm-rule-meta">
              <span v-if="r.created_by" class="cm-rule-by">@{{ r.created_by }}</span>
              <span class="cm-rule-counts">нашёл: {{ r.matched_count }} · скрыто: {{ r.hidden_count }}</span>
              <span class="cm-rule-date">{{ formatShort(r.created_at) }}</span>
            </div>
            <div class="cm-rule-actions">
              <button class="cm-btn green" @click="applyRule(r)" :disabled="busy">
                <SakuraIcon name="refresh" :size="14" /> Применить
              </button>
              <button class="cm-btn gray" @click="deleteRule(r)" :disabled="busy">
                <SakuraIcon name="trash" :size="14" /> Удалить
              </button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 24px; text-align: center; color: var(--text-tertiary, #9aa); font-size: var(--text-sm, 0.75rem)">
          Правил пока нет
        </div>

        <button
          v-if="rules.length"
          class="btn-apply-all"
          @click="applyAllRules"
          :disabled="busy"
        >
          <SakuraIcon :name="busy ? 'spinner' : 'zap'" :size="15" />
          Применить все правила ко всему каталогу
        </button>
      </section>

      <section class="cm-card">
        <div class="cm-card-head">
          <h3>Скрытые из каталога</h3>
          <span class="cm-count">{{ hiddenCount }}</span>
        </div>

        <div class="cm-search">
          <SakuraIcon name="search" :size="15" />
          <input
            v-model="search"
            class="form-control"
            type="text"
            placeholder="Поиск по названию..."
            @keyup.enter="loadHidden(1)"
          />
        </div>

        <div v-if="hiddenLoading" class="cm-loading">
          <SakuraIcon name="spinner" :size="18" /> Загрузка...
        </div>

        <div v-else-if="hiddenAnime.length" class="cm-hidden-list">
          <div v-for="a in hiddenAnime" :key="a.id" class="cm-hidden-item">
            <img
              v-if="a.poster_url"
              class="cm-hidden-poster"
              :src="a.poster_url"
              :alt="a.title_ru"
              loading="lazy"
            />
            <div v-else class="cm-hidden-poster placeholder">
              <SakuraIcon name="film" :size="16" />
            </div>
            <div class="cm-hidden-info">
              <span class="cm-hidden-title">{{ a.title_ru }}</span>
              <span class="cm-hidden-meta">
                {{ a.year || "-" }}
                <template v-if="a.kind"> · {{ a.kind }}</template>
                <template v-if="a.score"> · <SakuraIcon name="star" :size="16" /> {{ Number(a.score).toFixed(2) }}</template>
              </span>
              <span v-if="a.franchise" class="cm-hidden-meta">Франшиза: {{ a.franchise.name }}</span>
            </div>
            <button class="cm-btn green" @click="restoreAnime(a)" :disabled="busy">
              <SakuraIcon name="check" :size="14" /> Вернуть
            </button>
          </div>
        </div>
        <div v-else class="empty-state" style="padding: 24px; text-align: center; color: var(--text-tertiary, #9aa); font-size: var(--text-sm, 0.75rem)">
          В каталоге всё чисто
        </div>

        <div v-if="hiddenCount > pageSize" class="cm-pager">
          <button class="cm-btn gray" :disabled="page <= 1 || hiddenLoading" @click="loadHidden(page - 1)">
            <SakuraIcon name="arrow-left" :size="16" />
          </button>
          <span class="cm-paging">{{ page }} / {{ totalPages }}</span>
          <button class="cm-btn gray" :disabled="page >= totalPages || hiddenLoading" @click="loadHidden(page + 1)">
            <SakuraIcon name="arrow-right" :size="16" />
          </button>
        </div>
      </section>
    </div>

    <section v-if="!managementError" class="cm-card">
      <div class="cm-card-head">
        <h3>Скрыть конкретное аниме вручную</h3>
      </div>
      <p class="cm-desc">
        Найдите аниме в каталоге и скройте его для всех пользователей (без создания правила).
      </p>
      <div class="cm-search">
        <SakuraIcon name="search" :size="15" />
        <input
          v-model="manualQuery"
          class="form-control"
          type="text"
          placeholder="Поиск по названию..."
          @input="debouncedManualSearch"
        />
      </div>

      <div v-if="manualLoading" class="cm-loading">
        <SakuraIcon name="spinner" :size="18" /> Поиск...
      </div>

      <div v-else-if="manualResults.length" class="cm-manual-list">
        <div v-for="a in manualResults" :key="a.id" class="cm-hidden-item">
          <img v-if="a.poster_url" class="cm-hidden-poster" :src="a.poster_url" :alt="a.title_ru" loading="lazy" />
          <div v-else class="cm-hidden-poster placeholder"><SakuraIcon name="film" :size="16" /></div>
          <div class="cm-hidden-info">
            <span class="cm-hidden-title">{{ a.title_ru }} <template v-if="a.title_en">({{ a.title_en }})</template></span>
            <span class="cm-hidden-meta">
              {{ a.year || "-" }}
              <template v-if="a.kind"> · {{ a.kind }}</template>
              <template v-if="a.score"> · <SakuraIcon name="star" :size="16" /> {{ Number(a.score).toFixed(2) }}</template>
            </span>
          </div>
          <button class="cm-btn danger" @click="hideAnime(a)" :disabled="busy">
            <SakuraIcon name="eye-off" :size="14" /> Скрыть
          </button>
        </div>
      </div>
      <div
        v-else-if="manualResults.length === 0 && manualQuery.trim().length >= 2 && !manualLoading"
        class="empty-state"
        style="padding: 24px; text-align: center; color: var(--text-tertiary, #9aa); font-size: var(--text-sm, 0.75rem)"
      >
        Ничего не найдено
      </div>
    </section>

    <div class="cm-toast" :class="{ visible: toast.visible }">
      <SakuraIcon :name="toast.icon" :size="15" />
      {{ toast.text }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import api from "@/api";
import { queryClient } from '@/lib/queryClient';
import SakuraIcon from "@/components/icons/SakuraIcon.vue";

interface HideRule {
  id: number;
  rule_type: string;
  rule_type_label: string;
  value: string;
  note: string;
  created_at: string;
  created_by?: string | null;
  matched_count: number;
  hidden_count: number;
}

interface HiddenAnimeItem {
  id: number;
  title_ru: string;
  title_en?: string;
  year?: number | null;
  kind?: string;
  score?: number | null;
  poster_url?: string;
  franchise?: { id: number; name: string } | null;
}

interface SearchAnimeItem {
  id: number;
  title_ru: string;
  title_en?: string;
  year?: number | null;
  kind?: string;
  score?: number | null;
  poster_url?: string;
  is_available?: boolean;
}

const ruleTypes = [
  { value: "genre", label: "По жанру" },
  { value: "title", label: "По названию" },
  { value: "franchise", label: "По франшизе" },
  { value: "kind", label: "По типу" },
  { value: "studio", label: "По студии" },
];

const catalogOptions = ref({ genres: [] as string[], studios: [] as string[], kinds: [] as string[] });
const valueOptions = computed(() => {
  if (form.value.rule_type === "genre") return catalogOptions.value.genres;
  if (form.value.rule_type === "studio") return catalogOptions.value.studios;
  if (form.value.rule_type === "kind") return catalogOptions.value.kinds;
  return [];
});

const genreFilter = ref("");
const selectedGenres = ref<string[]>([]);

const filteredGenreOptions = computed(() => {
  const q = genreFilter.value.trim().toLowerCase();
  const pool = q
    ? catalogOptions.value.genres.filter((g) => g.toLowerCase().includes(q))
    : catalogOptions.value.genres;
  const sel = new Set(selectedGenres.value);
  const selectedFirst = pool.filter((g) => sel.has(g));
  const rest = pool.filter((g) => !sel.has(g));
  return [...selectedFirst, ...rest];
});

const toggleGenre = (g: string) => {
  const i = selectedGenres.value.indexOf(g);
  if (i === -1) selectedGenres.value.push(g);
  else selectedGenres.value.splice(i, 1);
};

const rules = ref<HideRule[]>([]);
const rulesLoading = ref(false);
const hiddenAnime = ref<HiddenAnimeItem[]>([]);
const hiddenLoading = ref(false);
const hiddenCount = ref(0);
const search = ref("");
const page = ref(1);
const pageSize = 20;
const busy = ref(false);

const form = ref({ rule_type: "genre", value: "", note: "" });

const toast = ref({ visible: false, text: "", icon: "check" });

const settings = ref({ groupFranchises: true });
const settingsReady = ref(false);
const managementError = ref('');

const loadSettings = async () => {
  try {
    const { data } = await api.get("/anime/admin/catalog-settings/");
    settings.value.groupFranchises = data.group_franchises !== false;
    settingsReady.value = true;
  } catch (e) {
    console.error("Load settings error:", e);
  }
};

const loadOptions = async () => {
  try {
    const { data } = await api.get("/anime/admin/catalog-options/");
    catalogOptions.value = data;
    if (catalogOptions.value.genres.length && !form.value.value) {
      form.value.value = "";
    }
  } catch (e) {
    console.error("Load options error:", e);
    managementError.value = 'Не удалось загрузить правила и параметры каталога.';
  }
};

const toggleGroupFranchises = async () => {
  if (busy.value || !settingsReady.value) return;
  busy.value = true;
  try {
    const next = !settings.value.groupFranchises;
    const { data } = await api.patch("/anime/admin/catalog-settings/", {
      group_franchises: next,
    });
    settings.value.groupFranchises = data.group_franchises === true;
    await queryClient.invalidateQueries({queryKey: ['read', 'public', 'catalog-settings']});
    showToast(
      next
        ? "Франшизы снова группируются в каталоге"
        : "Группировка франшиз отключена",
    );
  } catch (e) {
    console.error("Toggle settings error:", e);
    showToast("Не удалось изменить настройку", "x");
  } finally {
    busy.value = false;
  }
};

const totalPages = computed(() => Math.max(1, Math.ceil(hiddenCount.value / pageSize)));

const showToast = (text: string, icon = "check") => {
  toast.value = { visible: true, text, icon };
  setTimeout(() => (toast.value.visible = false), 3500);
};

const loadRules = async () => {
  rulesLoading.value = true;
  try {
    const { data } = await api.get("/anime/admin/catalog-rules/");
    rules.value = data.results || [];
  } catch (e) {
    console.error("Load rules error:", e);
    managementError.value = 'Не удалось загрузить правила и параметры каталога.';
    showToast("Не удалось загрузить правила", "x");
  } finally {
    rulesLoading.value = false;
  }
};

const loadHidden = async (p = 1) => {
  hiddenLoading.value = true;
  try {
    const q = search.value.trim();
    const { data } = await api.get("/anime/admin/catalog-hidden/", {
      params: { page: p, page_size: pageSize, search: q },
    });
    hiddenAnime.value = data.results || [];
    hiddenCount.value = data.count || 0;
    page.value = data.page || 1;
  } catch (e) {
    console.error("Load hidden error:", e);
    managementError.value = 'Не удалось загрузить правила и параметры каталога.';
    showToast("Не удалось загрузить список скрытых", "x");
  } finally {
    hiddenLoading.value = false;
  }
};

const onRuleTypeChange = () => {
  form.value.value = "";
  selectedGenres.value = [];
  genreFilter.value = "";
};

const addRule = async () => {
  if (form.value.rule_type === "genre") {
    if (!selectedGenres.value.length) {
      showToast("Выберите хотя бы один жанр", "ban");
      return;
    }
    busy.value = true;
    let created = 0;
    let hiddenTotal = 0;
    let matchedTotal = 0;
    try {
      for (const g of selectedGenres.value) {
        const payload = {
          rule_type: "genre",
          value: g,
          note: form.value.note,
        };
        const { data } = await api.post("/anime/admin/catalog-rules/", payload);
        rules.value.unshift(data);
        created += 1;
        hiddenTotal += data.hidden_now ?? 0;
        matchedTotal += data.matched_count ?? 0;
      }
      showToast(
        `Создано правил: ${created} · скрыто: ${hiddenTotal} · всего нашлось: ${matchedTotal}`,
      );
      selectedGenres.value = [];
      form.value.note = "";
      loadHidden(1);
    } catch (e) {
      console.error("Add rule error:", e);
      showToast("Не удалось создать правило", "x");
    } finally {
      busy.value = false;
    }
    return;
  }

  const value = form.value.value.trim();
  if (!value) {
    showToast("Укажите значение правила", "ban");
    return;
  }
  busy.value = true;
  try {
    const { data } = await api.post("/anime/admin/catalog-rules/", form.value);
    rules.value.unshift(data);
    showToast(`Скрыто: ${data.hidden_now ?? 0} · всего нашлось: ${data.matched_count}`);
    form.value.value = "";
    form.value.note = "";
    loadHidden(1);
  } catch (e) {
    console.error("Add rule error:", e);
    showToast("Не удалось создать правило", "x");
  } finally {
    busy.value = false;
  }
};

const applyRule = async (r: HideRule) => {
  busy.value = true;
  try {
    const { data } = await api.post(`/anime/admin/catalog-rules/${r.id}/`);
    Object.assign(r, data);
    showToast(`Дополнительно скрыто: ${data.hidden_now ?? 0}`);
    loadHidden(page.value);
  } catch (e) {
    console.error("Apply rule error:", e);
    showToast("Не удалось применить правило", "x");
  } finally {
    busy.value = false;
  }
};

const applyAllRules = async () => {
  busy.value = true;
  try {
    const { data } = await api.post("/anime/admin/catalog-rules/apply-all/");
    showToast(`Скрыто всего: ${data.total_hidden ?? 0}`);
    loadRules();
    loadHidden(1);
  } catch (e) {
    console.error("Apply-all error:", e);
    showToast("Не удалось применить правила", "x");
  } finally {
    busy.value = false;
  }
};

const deleteRule = async (r: HideRule) => {
  if (!confirm(`Удалить правило "${r.rule_type_label}: ${r.value}"?`)) return;
  busy.value = true;
  try {
    const { data } = await api.delete(`/anime/admin/catalog-rules/${r.id}/`);
    rules.value = rules.value.filter((x) => x.id !== r.id);
    const restored = data?.restored ?? 0;
    showToast(
      restored
        ? `Правило удалено, возвращено аниме: ${restored}`
        : "Правило удалено",
    );
    loadHidden(page.value);
  } catch (e) {
    console.error("Delete rule error:", e);
    showToast("Не удалось удалить правило", "x");
  } finally {
    busy.value = false;
  }
};

const restoreAnime = async (a: HiddenAnimeItem) => {
  busy.value = true;
  try {
    await api.post(`/anime/admin/catalog-hidden/${a.id}/restore/`);
    hiddenAnime.value = hiddenAnime.value.filter((x) => x.id !== a.id);
    hiddenCount.value = Math.max(0, hiddenCount.value - 1);
    showToast(`«${a.title_ru}» возвращено в каталог`);
  } catch (e) {
    console.error("Restore error:", e);
    showToast("Не удалось вернуть аниме", "x");
  } finally {
    busy.value = false;
  }
};

const manualQuery = ref("");
const manualResults = ref<SearchAnimeItem[]>([]);
const manualLoading = ref(false);
let manualTimer: ReturnType<typeof setTimeout> | null = null;

const debouncedManualSearch = () => {
  if (manualTimer) clearTimeout(manualTimer);
  manualTimer = setTimeout(runManualSearch, 350);
};

const runManualSearch = async () => {
  const q = manualQuery.value.trim();
  if (q.length < 2) {
    manualResults.value = [];
    return;
  }
  manualLoading.value = true;
  try {
    const { data } = await api.get("/anime/admin/anime-search/", { params: { q } });
    manualResults.value = (data.results || []).map((a: SearchAnimeItem) => ({
      ...a,
      is_available: a.is_available ?? true,
    }));
  } catch (e) {
    console.error("Manual search error:", e);
    manualResults.value = [];
  } finally {
    manualLoading.value = false;
  }
};

const hideAnime = async (a: SearchAnimeItem) => {
  busy.value = true;
  try {
    const { data } = await api.post("/anime/admin/catalog-hidden/", { anime_id: a.id });
    manualResults.value = manualResults.value.filter((x) => x.id !== a.id);
    showToast(`«${data.title_ru}» скрыто из каталога`);
    loadHidden(1);
  } catch (e) {
    console.error("Hide anime error:", e);
    showToast("Не удалось скрыть аниме", "x");
  } finally {
    busy.value = false;
  }
};

const formatShort = (d?: string) => {
  if (!d) return "-";
  return new Date(d).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
};

const retryManagement = async () => {
  managementError.value = '';
  await Promise.allSettled([loadRules(), loadHidden(1), loadOptions()]);
};
onMounted(() => { void loadSettings(); void retryManagement(); });
</script>

<style scoped>
.catalog-manager {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cm-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.cm-header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}
.cm-header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: var(--accent-subtle, rgba(255, 126, 179, 0.14));
  color: var(--accent, #ff7eb3);
  flex-shrink: 0;
}
.cm-header-title h2 {
  margin: 0 0 2px;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary, #fff);
}
.cm-header-title p {
  margin: 0;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-tertiary, #9aa);
}
.cm-stats {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.cm-stat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  border-radius: 999px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-default, #333);
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-secondary, #ccc);
}
.cm-stat b {
  color: var(--text-primary, #fff);
}

.cm-card {
  background: var(--surface-3, #151023);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-lg, 15px);
  padding: 18px;
}
.cm-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}
.cm-card-head h3 {
  margin: 0;
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.cm-count {
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 700;
  color: var(--accent, #ff7eb3);
  background: var(--accent-subtle, rgba(255, 126, 179, 0.12));
  border-radius: 999px;
  padding: 2px 10px;
}
.cm-desc {
  margin: 0 0 14px;
  font-size: var(--text-sm, 0.75rem);
  line-height: 1.55;
  color: var(--text-tertiary, #9aa);
}

.cm-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  cursor: pointer;
}
.cm-toggle-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cm-toggle-title {
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.cm-toggle-desc {
  font-size: var(--text-sm, 0.75rem);
  line-height: 1.5;
  color: var(--text-tertiary, #9aa);
  max-width: 640px;
}
.cm-switch {
  position: relative;
  width: 52px;
  height: 28px;
  flex-shrink: 0;
  background: var(--surface-5, #2a2340);
  border: 1px solid var(--border-default, #333);
  border-radius: 999px;
  transition: background 0.2s, border-color 0.2s;
}
.cm-switch .cm-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--text-tertiary, #9aa);
  transition: transform 0.2s, background 0.2s;
}
.cm-switch.on {
  background: var(--accent-subtle, rgba(255, 126, 179, 0.25));
  border-color: var(--accent, #ff7eb3);
}
.cm-switch.on .cm-switch-thumb {
  transform: translateX(24px);
  background: var(--accent, #ff7eb3);
}

.cm-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.cm-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}
.cm-form-row {
  display: flex;
  gap: 8px;
}
.cm-form-row .form-control:first-child {
  width: 34%;
  flex-shrink: 0;
}
.form-control {
  box-sizing: border-box;
  width: 100%;
  padding: 9px 12px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-default, #333);
  border-radius: var(--radius-sm, 7px);
  color: var(--text-primary, #fff);
  font-size: var(--text-sm, 0.75rem);
  font-family: inherit;
}
.form-control:focus {
  outline: none;
  border-color: var(--accent, #ff7eb3);
}

.btn-primary {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 16px;
  background: var(--accent);
  color: var(--text-on-accent, #1a0a14);
  border: none;
  border-radius: var(--radius-md, 11px);
  font-weight: 700;
  font-size: var(--text-sm, 0.75rem);
  cursor: pointer;
  transition: opacity 0.15s, transform 0.15s;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.cm-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 32px;
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-tertiary, #9aa);
}
.cm-rules {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 460px;
  overflow-y: auto;
}
.cm-rule {
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-subtle, #222);
  border-radius: var(--radius-sm, 7px);
  padding: 10px 12px;
}
.cm-rule-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.cm-rule-type {
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 700;
  color: var(--accent, #ff7eb3);
  background: var(--accent-subtle, rgba(255, 126, 179, 0.12));
  border-radius: 999px;
  padding: 2px 9px;
}
.cm-rule-value {
  font-size: var(--text-sm, 0.75rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.cm-rule-note {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
}
.cm-rule-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  margin-bottom: 8px;
}
.cm-rule-counts {
  font-weight: 600;
  color: var(--text-secondary, #ccc);
}
.cm-rule-actions {
  display: flex;
  gap: 8px;
}

.cm-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--radius-sm, 7px);
  font-size: var(--text-sm, 0.75rem);
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
  background: transparent;
  border: none;
}
.cm-btn:hover:not(:disabled) {
  opacity: 0.8;
}
.cm-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cm-btn.green {
  background: var(--success-subtle);
  color: var(--success);
}
.cm-btn.gray {
  background: var(--surface-5);
  color: var(--text-tertiary);
  border: 1px solid var(--border-default);
}
.cm-btn.danger {
  background: var(--danger-subtle, rgba(215, 39, 39, 0.15));
  color: var(--danger, #ff6b6b);
}

.btn-apply-all {
  width: 100%;
  margin-top: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--info-subtle);
  color: var(--info);
  border: 1px solid transparent;
  border-radius: var(--radius-md, 11px);
  font-weight: 600;
  font-size: var(--text-sm, 0.75rem);
  cursor: pointer;
  transition: opacity 0.15s;
}
.btn-apply-all:hover:not(:disabled) {
  opacity: 0.85;
}
.btn-apply-all:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cm-search {
  position: relative;
  margin-bottom: 12px;
}
.cm-search .sakura-icon {
  position: absolute;
  left: 11px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-tertiary, #9aa);
}
.cm-search .form-control {
  padding-left: 34px;
}
.cm-search-sm {
  margin-bottom: 0;
  flex: 1;
  min-width: 140px;
}

.cm-genre-picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
  min-width: 0;
}
.cm-genre-picker-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.cm-genre-picker-top .cm-count {
  white-space: nowrap;
}
.cm-genre-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 132px;
  overflow-y: auto;
}
.cm-genre-chip {
  padding: 4px 11px;
  border-radius: 999px;
  border: 1px solid var(--border-default, #333);
  background: var(--surface-4, #1c162c);
  color: var(--text-secondary, #ccc);
  font-size: var(--text-xs, 0.6875rem);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s;
}
.cm-genre-chip:hover {
  border-color: var(--accent, #ff7eb3);
  color: var(--text-primary, #fff);
}
.cm-genre-chip.active {
  background: var(--accent, #ff7eb3);
  border-color: var(--accent, #ff7eb3);
  color: #1a0a14;
}

.cm-hidden-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 520px;
  overflow-y: auto;
}
.cm-manual-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow-y: auto;
}
.cm-hidden-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-subtle, #222);
  border-radius: var(--radius-sm, 7px);
}
.cm-hidden-poster {
  width: 44px;
  height: 62px;
  object-fit: cover;
  border-radius: 5px;
  flex-shrink: 0;
  background: var(--surface-5);
}
.cm-hidden-poster.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary, #9aa);
}
.cm-hidden-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}
.cm-hidden-title {
  font-size: var(--text-sm, 0.75rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cm-hidden-meta {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.cm-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 14px;
}
.cm-paging {
  font-size: var(--text-xs, 0.6875rem);
  color: var(--text-tertiary, #9aa);
}

.cm-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translate(-50%, 20px);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: var(--surface-4, #1c162c);
  border: 1px solid var(--border-strong, #555);
  border-radius: var(--radius-md, 11px);
  font-size: var(--text-sm, 0.75rem);
  color: var(--text-primary, #fff);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s, transform 0.2s;
  z-index: 1200;
}
.cm-toast.visible {
  opacity: 1;
  transform: translate(-50%, 0);
}

@media (max-width: 900px) {
  .cm-grid {
    grid-template-columns: 1fr;
  }
  .cm-form-row {
    flex-direction: column;
  }
  .cm-form-row .form-control:first-child {
    width: 100%;
  }
}

@media (max-width: 374px) {
  .catalog-manager {
    gap: 10px;
  }

  .cm-header {
    gap: 10px;
  }

  .cm-header-title {
    gap: 8px;
  }

  .cm-header-icon {
    width: 34px;
    height: 34px;
    border-radius: 10px;
  }

  .cm-header-icon svg {
    width: 18px;
    height: 18px;
  }

  .cm-header-title h2 {
    font-size: 0.95rem;
  }

  .cm-header-title p {
    font-size: 0.68rem;
  }

  .cm-stats {
    width: 100%;
    gap: 6px;
  }

  .cm-stat {
    flex: 1;
    justify-content: center;
    padding: 5px 8px;
    font-size: 0.68rem;
  }

  .cm-card {
    padding: 12px;
    border-radius: 11px;
  }

  .cm-card-head h3 {
    font-size: 0.85rem;
  }

  .cm-count {
    font-size: 0.62rem;
    padding: 2px 7px;
  }

  .cm-desc {
    font-size: 0.68rem;
    margin-bottom: 10px;
  }

  .cm-toggle-row {
    gap: 10px;
    align-items: flex-start;
  }

  .cm-toggle-title {
    font-size: 0.82rem;
  }

  .cm-toggle-desc {
    font-size: 0.68rem;
  }

  .cm-switch {
    width: 42px;
    height: 24px;
    flex-shrink: 0;
  }

  .cm-switch .cm-switch-thumb {
    width: 16px;
    height: 16px;
    top: 3px;
    left: 3px;
  }

  .cm-switch.on .cm-switch-thumb {
    transform: translateX(18px);
  }

  .form-control {
    padding: 8px 10px;
    font-size: 0.72rem;
  }

  .cm-search .form-control {
    padding-left: 30px;
  }

  .btn-primary {
    padding: 10px 12px;
    font-size: 0.72rem;
  }

  .cm-genre-list {
    max-height: 110px;
  }

  .cm-genre-chip {
    padding: 3px 9px;
    font-size: 0.62rem;
  }

  .cm-rules,
  .cm-hidden-list,
  .cm-manual-list {
    max-height: 380px;
  }

  .cm-rule {
    padding: 8px 10px;
  }

  .cm-rule-type {
    font-size: 0.62rem;
    padding: 2px 7px;
  }

  .cm-rule-value {
    font-size: 0.72rem;
  }

  .cm-rule-meta {
    font-size: 0.62rem;
    gap: 5px;
  }

  .cm-rule-actions {
    gap: 6px;
    flex-wrap: wrap;
  }

  .cm-btn {
    padding: 4px 9px;
    font-size: 0.68rem;
    flex: 1 1 auto;
    justify-content: center;
  }

  .btn-apply-all {
    padding: 9px 12px;
    font-size: 0.72rem;
  }

  .cm-hidden-item {
    padding: 6px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .cm-hidden-poster {
    width: 36px;
    height: 50px;
  }

  .cm-hidden-info {
    flex: 1 1 calc(100% - 52px);
  }

  .cm-hidden-title {
    font-size: 0.72rem;
  }

  .cm-hidden-meta {
    font-size: 0.62rem;
  }

  .cm-hidden-item .cm-btn {
    flex: 1 1 100%;
  }

  .cm-toast {
    bottom: 12px;
    left: 12px;
    right: 12px;
    transform: none;
    justify-content: center;
    padding: 8px 12px;
    font-size: 0.68rem;
  }

  .cm-toast.visible {
    transform: none;
  }
}

@media (min-width: 375px) and (max-width: 767px) {
  .catalog-manager {
    gap: 12px;
  }

  .cm-header {
    gap: 12px;
  }

  .cm-header-icon {
    width: 38px;
    height: 38px;
    border-radius: 12px;
  }

  .cm-header-title h2 {
    font-size: 1rem;
  }

  .cm-header-title p {
    font-size: 0.72rem;
  }

  .cm-stats {
    width: 100%;
    gap: 8px;
  }

  .cm-stat {
    flex: 1;
    justify-content: center;
  }

  .cm-card {
    padding: 14px;
  }

  .cm-toggle-row {
    gap: 12px;
  }

  .cm-rules,
  .cm-hidden-list,
  .cm-manual-list {
    max-height: 420px;
  }

  .cm-rule-actions {
    flex-wrap: wrap;
  }

  .cm-btn {
    flex: 1 1 auto;
    justify-content: center;
  }

  .cm-hidden-item {
    flex-wrap: wrap;
  }

  .cm-hidden-info {
    flex: 1 1 calc(100% - 60px);
  }

  .cm-hidden-item .cm-btn {
    flex: 1 1 100%;
  }

  .cm-toast {
    bottom: 16px;
    left: 16px;
    right: 16px;
    transform: none;
    justify-content: center;
  }

  .cm-toast.visible {
    transform: none;
  }
}

@media (min-width: 768px) and (max-width: 1023px) {
  .catalog-manager {
    gap: 14px;
  }

  .cm-grid {
    grid-template-columns: 1fr;
  }

  .cm-rules,
  .cm-hidden-list,
  .cm-manual-list {
    max-height: 400px;
  }

  .cm-form-row .form-control:first-child {
    width: 30%;
  }
}

@media (max-width: 767px) and (orientation: landscape) {
  .cm-rules,
  .cm-hidden-list,
  .cm-manual-list {
    max-height: 320px;
  }

  .cm-card {
    padding: 12px;
  }
}

@media (hover: none) and (pointer: coarse) {
  .btn-primary:hover:not(:disabled) {
    transform: none;
  }

  .btn-primary:active:not(:disabled) {
    transform: scale(0.98);
  }

  .cm-btn:hover:not(:disabled) {
    opacity: 1;
  }

  .cm-btn:active:not(:disabled) {
    opacity: 0.75;
  }

  .cm-genre-chip:hover {
    border-color: var(--border-default, #333);
    color: var(--text-secondary, #ccc);
  }

  .cm-genre-chip:active:not(.active) {
    border-color: var(--accent, #ff7eb3);
    color: var(--text-primary, #fff);
  }

  .cm-rules,
  .cm-hidden-list,
  .cm-manual-list,
  .cm-genre-list {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
}
</style>
