<template>
  <div class="ideas-page">
    <div class="ideas-glow ideas-glow-one" aria-hidden="true"></div>
    <div class="ideas-glow ideas-glow-two" aria-hidden="true"></div>

    <div class="ideas-shell">
      <header class="ideas-hero">
        <div class="hero-copy">
          <h1>Давайте сделаем AniLux <span>лучше</span></h1>
          <!-- <p>Предлагайте функции, сообщайте об ошибках</p> -->
        </div>

        <div class="hero-stats" aria-label="Статистика идей">
          <div class="stat-item">
            <strong>{{ ideas.length }}</strong>
            <span>предложений</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <strong>{{ activeCount }}</strong>
            <span>в работе</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item stat-success">
            <strong>{{ doneCount }}</strong>
            <span>готово</span>
          </div>
        </div>
      </header>

      <section class="quick-add" aria-labelledby="quick-add-title">
        <div class="quick-add-icon"><LightBulbIcon /></div>
        <button class="quick-add-main" type="button" @click="openCreate()">
          <strong id="quick-add-title">Есть идея или нашли ошибку?</strong>
          <span>Расскажите нам - это займёт меньше минуты</span>
        </button>
        <div class="quick-kinds" aria-label="Быстрый выбор типа">
          <button type="button" @click="openCreate('idea')"><LightBulbIcon /> Идея</button>
          <button type="button" @click="openCreate('bug')"><BugAntIcon /> Ошибка</button>
          <button type="button" @click="openCreate('improvement')"><SparklesIcon /> Улучшение</button>
        </div>
      </section>

      <section class="board-section">
        <div class="board-heading">
          <!-- <div>
            <div class="section-title-row">
              <h2>Доска идей</h2>
              <span v-if="isAdmin" class="admin-pill"><ShieldCheckIcon /> Режим управления</span>
            </div>
            <p>{{ resultCaption }}</p>
          </div> -->

          <div class="board-actions">
            <label class="search-box">
              <MagnifyingGlassIcon />
              <span class="sr-only">Найти идею</span>
              <input v-model.trim="search" type="search" placeholder="Найти идею…" />
              <button v-if="search" type="button" aria-label="Очистить поиск" @click="search = ''"><XMarkIcon /></button>
            </label>

            <div class="view-switch" aria-label="Вид списка">
              <button type="button" :class="{ active: viewMode === 'board' }" aria-label="Канбан" :aria-pressed="viewMode === 'board'" @click="viewMode = 'board'">
                <Squares2X2Icon />
              </button>
              <button type="button" :class="{ active: viewMode === 'list' }" aria-label="Список" :aria-pressed="viewMode === 'list'" @click="viewMode = 'list'">
                <ListBulletIcon />
              </button>
            </div>
          </div>
        </div>

        <div class="filter-bar">
          <div class="filter-group" aria-label="Тип записи">
            <button
              v-for="option in kindFilters"
              :key="option.value"
              type="button"
              :class="{ active: kindFilter === option.value }"
              @click="kindFilter = option.value"
            >
              <component :is="option.icon" /> {{ option.label }}
              <span>{{ countByKind(option.value) }}</span>
            </button>
          </div>
          <label class="status-filter">
            <FunnelIcon />
            <span class="sr-only">Фильтр статуса</span>
            <select v-model="statusFilter">
              <option value="all">Все статусы</option>
              <option v-for="status in statuses" :key="status.value" :value="status.value">{{ status.label }}</option>
            </select>
          </label>
          <button v-if="authStore.isAuthenticated" class="mine-filter" :class="{ active: mineOnly }" type="button" @click="mineOnly = !mineOnly">
            <UserCircleIcon /> Мои
          </button>
        </div>

        <div v-if="loading" class="ideas-loading" aria-live="polite">
          <div v-for="n in 4" :key="n" class="skeleton-card"><span></span><span></span><span></span></div>
        </div>

        <div v-else-if="loadError" class="state-card error-state">
          <ExclamationTriangleIcon />
          <div><strong>Не удалось загрузить доску</strong><p>{{ loadError }}</p></div>
          <button type="button" @click="loadIdeas"><ArrowPathIcon /> Повторить</button>
        </div>

        <div v-else-if="filteredIdeas.length === 0" class="state-card empty-state">
          <div class="empty-icon"><LightBulbIcon /></div>
          <strong>{{ hasFilters ? 'Ничего не найдено' : 'Здесь пока тихо' }}</strong>
          <p>{{ hasFilters ? 'Попробуйте изменить запрос или сбросить фильтры.' : 'Станьте первым, кто предложит улучшение.' }}</p>
          <button v-if="hasFilters" type="button" @click="resetFilters">Сбросить фильтры</button>
          <button v-else type="button" @click="openCreate()"><PlusIcon /> Добавить идею</button>
        </div>

        <div v-else-if="viewMode === 'board'" class="kanban" aria-label="Доска статусов">
          <section
            v-for="column in visibleColumns"
            :key="column.value"
            class="kanban-column"
            :class="[`column-${column.value}`, { 'drop-active': dragOverStatus === column.value }]"
            @dragover.prevent="onDragOver(column.value)"
            @dragleave="dragOverStatus = null"
            @drop="onDrop(column.value)"
          >
            <header>
              <span class="status-dot"></span>
              <h3>{{ column.label }}</h3>
              <span class="column-count">{{ ideasForStatus(column.value).length }}</span>
            </header>
            <p class="column-hint">{{ column.hint }}</p>

            <div class="column-cards">
              <article
                v-for="idea in ideasForStatus(column.value)"
                :key="idea.id"
                class="idea-card"
                :class="{ dragging: draggedId === idea.id }"
                :draggable="isAdmin"
                @dragstart="onDragStart(idea.id)"
                @dragend="onDragEnd"
              >
                <button class="card-open" type="button" @click="openDetail(idea.id)">
                  <div class="card-topline">
                    <span class="kind-badge" :class="`kind-${idea.kind}`">
                      <component :is="kindMeta[idea.kind].icon" /> {{ kindMeta[idea.kind].label }}
                    </span>
                    <span v-if="idea.priority === 'high' || idea.priority === 'critical'" class="priority-mark" :class="`priority-${idea.priority}`">
                      {{ priorityMeta[idea.priority] }}
                    </span>
                    <span class="idea-number">#{{ idea.id }}</span>
                  </div>
                  <h4>{{ idea.title }}</h4>
                  <p>{{ idea.description }}</p>
                </button>
                <footer>
                  <div class="author-line" :title="idea.author_name">
                    <img v-if="idea.author_avatar" :src="idea.author_avatar" alt="" />
                    <span v-else class="avatar-fallback">{{ authorInitial(idea) }}</span>
                    <span>{{ idea.author_name }}</span>
                    <time :datetime="idea.created_at">{{ formatRelativeDate(idea.created_at) }}</time>
                  </div>
                  <button class="vote-button" :class="{ voted: idea.is_voted }" type="button" :aria-label="idea.is_voted ? 'Убрать голос' : 'Поддержать идею'" @click="toggleVote(idea)">
                    <HandThumbUpIcon /> {{ idea.votes_count }}
                  </button>
                </footer>
              </article>

              <button v-if="column.value === 'pending'" class="column-add" type="button" @click="openCreate()"><PlusIcon /> Добавить запись</button>
              <div v-if="ideasForStatus(column.value).length === 0" class="column-empty">
                <CheckCircleIcon v-if="column.value === 'done'" />
                <InboxIcon v-else />
                <span>Пока пусто</span>
              </div>
            </div>
          </section>
        </div>

        <div v-else class="ideas-list">
          <button v-for="idea in filteredIdeas" :key="idea.id" class="list-row" type="button" @click="openDetail(idea.id)">
            <span class="list-kind" :class="`kind-${idea.kind}`"><component :is="kindMeta[idea.kind].icon" /></span>
            <span class="list-copy"><strong>{{ idea.title }}</strong><small>{{ idea.description }}</small></span>
            <span class="status-badge" :class="`status-${idea.status}`"><i></i>{{ statusMeta[idea.status].label }}</span>
            <span class="list-author">{{ idea.author_name }}</span>
            <span class="list-votes"><HandThumbUpIcon /> {{ idea.votes_count }}</span>
            <ChevronRightIcon class="list-arrow" />
          </button>
        </div>
      </section>
    </div>

    <Teleport to="body">
      <Transition name="modal-fade">
        <div v-if="createOpen" class="modal-layer" role="presentation" @mousedown.self="closeCreate">
          <section class="modal-card create-modal" role="dialog" aria-modal="true" aria-labelledby="create-modal-title">
            <header class="modal-header">
              <div>
                <span class="modal-kicker"><PlusIcon /> Новая запись</span>
                <h2 id="create-modal-title">Поделитесь своей мыслью</h2>
                <p>Чем точнее описание, тем быстрее мы сможем разобраться</p>
              </div>
              <button class="icon-button" type="button" aria-label="Закрыть" @click="closeCreate"><XMarkIcon /></button>
            </header>

            <form class="idea-form" @submit.prevent="submitIdea">
              <fieldset class="kind-picker">
                <legend>Что вы хотите добавить?</legend>
                <label v-for="kind in kinds" :key="kind.value" :class="{ selected: createForm.kind === kind.value }">
                  <input v-model="createForm.kind" type="radio" name="kind" :value="kind.value" />
                  <span class="picker-icon" :class="`kind-${kind.value}`"><component :is="kind.icon" /></span>
                  <span><strong>{{ kind.label }}</strong><small>{{ kind.description }}</small></span>
                  <CheckCircleIcon class="picker-check" />
                </label>
              </fieldset>

              <label class="field-label">
                <span>Короткий заголовок <b>{{ createForm.title.length }}/140</b></span>
                <input v-model="createForm.title" maxlength="140" required placeholder="Например: добавить историю просмотра" />
              </label>

              <label class="field-label">
                <span>Подробности <b>{{ createForm.description.length }}/5000</b></span>
                <textarea v-model="createForm.description" maxlength="5000" required rows="6" placeholder="Расскажите, что произошло или как должна работать функция…"></textarea>
              </label>

              <p v-if="createError" class="form-error"><ExclamationTriangleIcon /> {{ createError }}</p>

              <footer class="modal-footer">
                <p><ClockIcon /> Запись появится в статусе «Ожидает»</p>
                <div>
                  <button class="secondary-button" type="button" @click="closeCreate">Отмена</button>
                  <button class="primary-button" type="submit" :disabled="creating || !isCreateValid">
                    <ArrowPathIcon v-if="creating" class="spin" />
                    <PaperAirplaneIcon v-else />
                    {{ creating ? 'Отправляем…' : 'Отправить' }}
                  </button>
                </div>
              </footer>
            </form>
          </section>
        </div>
      </Transition>

      <Transition name="drawer-fade">
        <div v-if="selectedIdea" class="drawer-layer" role="presentation" @mousedown.self="closeDetail">
          <aside class="detail-drawer" role="dialog" aria-modal="true" aria-labelledby="detail-title">
            <header class="drawer-header">
              <div class="drawer-topline">
                <span class="kind-badge" :class="`kind-${selectedIdea.kind}`"><component :is="kindMeta[selectedIdea.kind].icon" />{{ kindMeta[selectedIdea.kind].label }}</span>
                <span class="idea-number">ANI-{{ String(selectedIdea.id).padStart(4, '0') }}</span>
              </div>
              <button class="icon-button" type="button" aria-label="Закрыть" @click="closeDetail"><XMarkIcon /></button>
            </header>

            <div class="drawer-scroll">
              <div class="drawer-title-block">
                <span class="status-badge large" :class="`status-${selectedIdea.status}`"><i></i>{{ statusMeta[selectedIdea.status].label }}</span>
                <h2 id="detail-title">{{ selectedIdea.title }}</h2>
                <div class="drawer-author">
                  <img v-if="selectedIdea.author_avatar" :src="selectedIdea.author_avatar" alt="" />
                  <span v-else class="avatar-fallback">{{ authorInitial(selectedIdea) }}</span>
                  <span><strong>{{ selectedIdea.author_name }}</strong><small>предложил{{ formatFullDate(selectedIdea.created_at) }}</small></span>
                </div>
              </div>

              <section class="detail-section">
                <h3>Описание</h3>
                <p class="idea-description">{{ selectedIdea.description }}</p>
              </section>

              <section v-if="selectedIdea.admin_note" class="admin-note">
                <div><ShieldCheckIcon /><strong>Комментарий команды</strong></div>
                <p>{{ selectedIdea.admin_note }}</p>
              </section>

              <section class="detail-meta">
                <div><span>Тип</span><strong>{{ kindMeta[selectedIdea.kind].label }}</strong></div>
                <div><span>Приоритет</span><strong :class="`text-priority-${selectedIdea.priority}`">{{ priorityMeta[selectedIdea.priority] }}</strong></div>
                <div><span>Обновлено</span><strong>{{ formatRelativeDate(selectedIdea.updated_at) }}</strong></div>
              </section>

              <section v-if="isAdmin" class="admin-controls">
                <div class="admin-controls-title"><ShieldCheckIcon /><div><strong>Управление записью</strong><span>Изменения видны всем пользователям</span></div></div>
                <div class="admin-fields">
                  <label><span>Статус</span><select v-model="adminDraft.status"><option v-for="item in statuses" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
                  <label><span>Приоритет</span><select v-model="adminDraft.priority"><option v-for="item in priorities" :key="item.value" :value="item.value">{{ item.label }}</option></select></label>
                </div>
                <label class="field-label admin-textarea"><span>Комментарий команды</span><textarea v-model="adminDraft.admin_note" maxlength="2000" rows="4" placeholder="Например: добавили в план на следующий релиз"></textarea></label>
                <button class="admin-save" type="button" :disabled="adminSaving || !adminHasChanges" @click="saveAdminChanges">
                  <ArrowPathIcon v-if="adminSaving" class="spin" /><CheckIcon v-else />{{ adminSaving ? 'Сохраняем…' : 'Сохранить изменения' }}
                </button>
              </section>
            </div>

            <footer class="drawer-footer">
              <button class="drawer-vote" :class="{ voted: selectedIdea.is_voted }" type="button" @click="toggleVote(selectedIdea)">
                <HandThumbUpIcon />
                <span><strong>{{ selectedIdea.is_voted ? 'Вы поддержали' : 'Поддержать идею' }}</strong><small>{{ selectedIdea.votes_count }} {{ pluralVotes(selectedIdea.votes_count) }}</small></span>
              </button>
              <button v-if="canDelete(selectedIdea)" class="delete-button" type="button" aria-label="Удалить запись" @click="deleteIdea(selectedIdea)"><TrashIcon /></button>
            </footer>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, markRaw, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  ArrowPathIcon,
  BugAntIcon,
  CheckCircleIcon,
  CheckIcon,
  ChevronRightIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  HandThumbUpIcon,
  InboxIcon,
  LightBulbIcon,
  ListBulletIcon,
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
  PlusIcon,
  ShieldCheckIcon,
  SparklesIcon,
  Squares2X2Icon,
  TrashIcon,
  UserCircleIcon,
  XMarkIcon,
} from "@heroicons/vue/24/outline";
import { ideasApi, type Idea, type IdeaKind, type IdeaPriority, type IdeaStatus } from "@/api/ideas";
import { useAuthStore } from "@/stores/auth";
import { useToast } from "@/composables/useToast";

type FilterValue = IdeaKind | "all";

const authStore = useAuthStore();
const toast = useToast();
const router = useRouter();
const route = useRoute();

const ideas = ref<Idea[]>([]);
const loading = ref(true);
const loadError = ref("");
const search = ref("");
const kindFilter = ref<FilterValue>("all");
const statusFilter = ref<IdeaStatus | "all">("all");
const mineOnly = ref(false);
const viewMode = ref<"board" | "list">((localStorage.getItem("ideas-view") as "board" | "list") || "board");
const createOpen = ref(false);
const creating = ref(false);
const createError = ref("");
const selectedId = ref<number | null>(null);
const draggedId = ref<number | null>(null);
const dragOverStatus = ref<IdeaStatus | null>(null);
const adminSaving = ref(false);
const createForm = reactive({ kind: "idea" as IdeaKind, title: "", description: "" });
const adminDraft = reactive({ status: "pending" as IdeaStatus, priority: "normal" as IdeaPriority, admin_note: "" });

const kinds = [
  { value: "idea" as const, label: "Идея", description: "Новая функция или возможность", icon: markRaw(LightBulbIcon) },
  { value: "bug" as const, label: "Ошибка", description: "Что-то работает не так", icon: markRaw(BugAntIcon) },
  { value: "improvement" as const, label: "Улучшение", description: "Можно сделать удобнее", icon: markRaw(SparklesIcon) },
];

const kindMeta = Object.fromEntries(kinds.map((item) => [item.value, item])) as Record<IdeaKind, typeof kinds[number]>;
const kindFilters = [{ value: "all" as const, label: "Все", icon: markRaw(Squares2X2Icon) }, ...kinds];
const statuses = [
  { value: "pending" as const, label: "Ожидает", hint: "Новые предложения" },
  { value: "planned" as const, label: "Запланировано", hint: "Добавлено в план" },
  { value: "in_progress" as const, label: "В процессе", hint: "Уже работаем" },
  { value: "review" as const, label: "На проверке", hint: "Проверяем результат" },
  { value: "done" as const, label: "Готово", hint: "Уже в AniLux" },
  { value: "declined" as const, label: "Отклонено", hint: "Не вошло в план" },
];
const statusMeta = Object.fromEntries(statuses.map((item) => [item.value, item])) as Record<IdeaStatus, typeof statuses[number]>;
const priorities = [
  { value: "low" as const, label: "Низкий" },
  { value: "normal" as const, label: "Обычный" },
  { value: "high" as const, label: "Высокий" },
  { value: "critical" as const, label: "Критический" },
];
const priorityMeta = Object.fromEntries(priorities.map((item) => [item.value, item.label])) as Record<IdeaPriority, string>;

const isAdmin = computed(() => Boolean(authStore.user?.is_admin || authStore.user?.is_staff || authStore.user?.is_superuser));
const selectedIdea = computed(() => ideas.value.find((idea) => idea.id === selectedId.value) || null);
const activeCount = computed(() => ideas.value.filter((idea) => ["planned", "in_progress", "review"].includes(idea.status)).length);
const doneCount = computed(() => ideas.value.filter((idea) => idea.status === "done").length);
const hasFilters = computed(() => Boolean(search.value || kindFilter.value !== "all" || statusFilter.value !== "all" || mineOnly.value));
const isCreateValid = computed(() => createForm.title.trim().length >= 5 && createForm.description.trim().length >= 15);
const adminHasChanges = computed(() => {
  const item = selectedIdea.value;
  return Boolean(item && (adminDraft.status !== item.status || adminDraft.priority !== item.priority || adminDraft.admin_note.trim() !== item.admin_note));
});

const filteredIdeas = computed(() => {
  const needle = search.value.toLocaleLowerCase("ru-RU");
  return ideas.value.filter((idea) => {
    if (kindFilter.value !== "all" && idea.kind !== kindFilter.value) return false;
    if (statusFilter.value !== "all" && idea.status !== statusFilter.value) return false;
    if (mineOnly.value && !idea.is_owner) return false;
    if (needle && !`${idea.title} ${idea.description} ${idea.author_name}`.toLocaleLowerCase("ru-RU").includes(needle)) return false;
    return true;
  });
});

const visibleColumns = computed(() => statusFilter.value === "all" ? statuses : statuses.filter((item) => item.value === statusFilter.value));
const resultCaption = computed(() => {
  const count = filteredIdeas.value.length;
  if (!hasFilters.value) return "Всё, над чем думает и работает команда";
  return `Найдено: ${count}`;
});

function ideasForStatus(status: IdeaStatus) {
  return filteredIdeas.value.filter((idea) => idea.status === status);
}

function countByKind(kind: FilterValue) {
  return kind === "all" ? ideas.value.length : ideas.value.filter((idea) => idea.kind === kind).length;
}

function authorInitial(idea: Idea) {
  return idea.author_name.trim().charAt(0).toLocaleUpperCase("ru-RU") || "A";
}

function formatRelativeDate(value: string) {
  const date = new Date(value);
  const days = Math.round((date.getTime() - Date.now()) / 86_400_000);
  if (days === 0) return "сегодня";
  if (days === -1) return "вчера";
  if (days > -7) return new Intl.RelativeTimeFormat("ru", { numeric: "auto" }).format(days, "day");
  return new Intl.DateTimeFormat("ru", { day: "numeric", month: "short" }).format(date);
}

function formatFullDate(value: string) {
  return ` ${new Intl.DateTimeFormat("ru", { day: "numeric", month: "long", year: "numeric" }).format(new Date(value))}`;
}

function pluralVotes(value: number) {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) return "голос";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return "голоса";
  return "голосов";
}

function getErrorMessage(error: unknown, fallback: string) {
  const rawPayload = (error as { response?: { data?: unknown } })?.response?.data;
  if (!rawPayload || typeof rawPayload !== "object" || Array.isArray(rawPayload)) return fallback;

  const payload = rawPayload as Record<string, unknown>;
  const first = Object.values(payload)[0];
  if (typeof payload.detail === "string") return payload.detail;
  if (typeof first === "string") return first;
  if (Array.isArray(first) && typeof first[0] === "string") return first[0];
  return fallback;
}

async function loadIdeas() {
  loading.value = true;
  loadError.value = "";
  try {
    ideas.value = await ideasApi.list();
    const queryId = Number(route.query.idea);
    if (queryId && ideas.value.some((idea) => idea.id === queryId)) selectedId.value = queryId;
  } catch (error) {
    loadError.value = getErrorMessage(error, "Проверьте соединение и попробуйте ещё раз.");
  } finally {
    loading.value = false;
  }
}

function requireAuth() {
  if (authStore.isAuthenticated) return true;
  toast.info("Войдите, чтобы добавить или поддержать идею");
  void router.push({ path: "/login", query: { redirect: "/ideas" } });
  return false;
}

function openCreate(kind?: IdeaKind) {
  if (!requireAuth()) return;
  if (kind) createForm.kind = kind;
  createError.value = "";
  createOpen.value = true;
}

function closeCreate() {
  if (!creating.value) createOpen.value = false;
}

async function submitIdea() {
  if (!isCreateValid.value || creating.value) return;
  creating.value = true;
  createError.value = "";
  try {
    const created = await ideasApi.create({
      kind: createForm.kind,
      title: createForm.title.trim(),
      description: createForm.description.trim(),
    });
    ideas.value.unshift(created);
    createOpen.value = false;
    createForm.title = "";
    createForm.description = "";
    toast.success("Запись добавлена и ждёт рассмотрения");
    openDetail(created.id);
  } catch (error) {
    createError.value = getErrorMessage(error, "Не удалось отправить запись.");
  } finally {
    creating.value = false;
  }
}

function openDetail(id: number) {
  selectedId.value = id;
  void router.replace({ query: { ...route.query, idea: String(id) } });
}

function closeDetail() {
  selectedId.value = null;
  const query = { ...route.query };
  delete query.idea;
  void router.replace({ query });
}

async function toggleVote(idea: Idea) {
  if (!requireAuth()) return;
  const wasVoted = idea.is_voted;
  const oldCount = idea.votes_count;
  idea.is_voted = !wasVoted;
  idea.votes_count = Math.max(0, oldCount + (wasVoted ? -1 : 1));
  try {
    const result = await ideasApi.vote(idea.id);
    idea.is_voted = result.is_voted;
    idea.votes_count = result.votes_count;
  } catch (error) {
    idea.is_voted = wasVoted;
    idea.votes_count = oldCount;
    toast.error(getErrorMessage(error, "Не удалось сохранить голос"));
  }
}

function onDragStart(id: number) {
  if (!isAdmin.value) return;
  draggedId.value = id;
}

function onDragOver(status: IdeaStatus) {
  if (isAdmin.value && draggedId.value) dragOverStatus.value = status;
}

function onDragEnd() {
  draggedId.value = null;
  dragOverStatus.value = null;
}

async function onDrop(status: IdeaStatus) {
  const id = draggedId.value;
  onDragEnd();
  if (!id || !isAdmin.value) return;
  const idea = ideas.value.find((item) => item.id === id);
  if (!idea || idea.status === status) return;
  const previous = idea.status;
  idea.status = status;
  try {
    const updated = await ideasApi.update(id, { status });
    Object.assign(idea, updated);
    toast.success(`Перемещено в «${statusMeta[status].label}»`);
  } catch (error) {
    idea.status = previous;
    toast.error(getErrorMessage(error, "Не удалось изменить статус"));
  }
}

async function saveAdminChanges() {
  const item = selectedIdea.value;
  if (!item || !isAdmin.value || !adminHasChanges.value) return;
  adminSaving.value = true;
  try {
    const updated = await ideasApi.update(item.id, {
      status: adminDraft.status,
      priority: adminDraft.priority,
      admin_note: adminDraft.admin_note.trim(),
    });
    Object.assign(item, updated);
    toast.success("Изменения сохранены");
  } catch (error) {
    toast.error(getErrorMessage(error, "Не удалось сохранить изменения"));
  } finally {
    adminSaving.value = false;
  }
}

function canDelete(idea: Idea) {
  return isAdmin.value || (idea.is_owner && idea.status === "pending");
}

async function deleteIdea(idea: Idea) {
  if (!window.confirm("Удалить эту запись? Отменить действие не получится.")) return;
  try {
    await ideasApi.remove(idea.id);
    ideas.value = ideas.value.filter((item) => item.id !== idea.id);
    closeDetail();
    toast.success("Запись удалена");
  } catch (error) {
    toast.error(getErrorMessage(error, "Не удалось удалить запись"));
  }
}

function resetFilters() {
  search.value = "";
  kindFilter.value = "all";
  statusFilter.value = "all";
  mineOnly.value = false;
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== "Escape") return;
  if (createOpen.value) closeCreate();
  else if (selectedId.value) closeDetail();
}

watch(viewMode, (value) => localStorage.setItem("ideas-view", value));
watch(selectedIdea, (idea) => {
  if (!idea) return;
  adminDraft.status = idea.status;
  adminDraft.priority = idea.priority;
  adminDraft.admin_note = idea.admin_note;
});
watch([createOpen, selectedId], ([isCreating, id]) => {
  document.documentElement.style.overflow = isCreating || id ? "hidden" : "";
});

onMounted(() => {
  void loadIdeas();
  window.addEventListener("keydown", onKeydown);
});
onBeforeUnmount(() => {
  document.documentElement.style.overflow = "";
  window.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.ideas-page {
  position: relative;
  min-height: calc(100vh - var(--navbar-height));
  overflow: hidden;
  background:
    radial-gradient(circle at 18% 4%, color-mix(in srgb, var(--accent) 7%, transparent), transparent 27rem),
    radial-gradient(circle at 88% 14%, color-mix(in srgb, var(--accent-2) 8%, transparent), transparent 24rem);
}

.ideas-glow { position: absolute; width: 320px; height: 320px; border-radius: 50%; filter: blur(90px); opacity: .08; pointer-events: none; }
.ideas-glow-one { top: 10%; left: -180px; background: var(--accent); }
.ideas-glow-two { top: 42%; right: -200px; background: var(--accent-2); }
.ideas-shell { position: relative; width: min(100%, 1540px); margin: 0 auto; padding: 40px clamp(20px, 3vw, 48px) 72px; }

.ideas-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 40px; padding: 24px 0 34px; }
.hero-copy { max-width: 720px; }
.eyebrow { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 16px; color: var(--accent); font-size: var(--text-sm); font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.eyebrow svg { width: 17px; }
.hero-copy h1 { font-size: clamp(2.15rem, 4vw, 3.65rem); line-height: 1.04; letter-spacing: -.045em; color: var(--text-primary); }
.hero-copy h1 span { color: var(--accent); }
.hero-copy p { max-width: 650px; margin-top: 18px; color: var(--text-tertiary); font-size: clamp(.95rem, 1.3vw, 1.08rem); }
.hero-stats { display: flex; align-items: center; flex: 0 0 auto; margin-top: 10px; padding: 16px 20px; border: 1px solid var(--border-default); border-radius: var(--radius-xl); background: color-mix(in srgb, var(--container-bg) 84%, transparent); box-shadow: var(--shadow-sm); backdrop-filter: blur(16px); }
.stat-item { min-width: 86px; text-align: center; }
.stat-item strong { display: block; color: var(--text-primary); font-family: var(--font-display); font-size: 1.5rem; line-height: 1; }
.stat-item span { display: block; margin-top: 6px; color: var(--text-tertiary); font-size: var(--text-xs); }
.stat-success strong { color: var(--success); }
.stat-divider { width: 1px; height: 34px; margin: 0 8px; background: var(--border-default); }

.quick-add { display: flex; align-items: center; gap: 16px; padding: 16px 18px; border: 1px solid color-mix(in srgb, var(--accent) 34%, var(--border-default)); border-radius: var(--radius-xl); background: linear-gradient(110deg, color-mix(in srgb, var(--accent) 10%, var(--container-bg)), var(--container-bg) 48%, color-mix(in srgb, var(--accent-2) 7%, var(--container-bg))); box-shadow: var(--shadow-md); }
.quick-add-icon { display: grid; width: 48px; height: 48px; flex: 0 0 auto; place-items: center; color: var(--accent); border-radius: 15px; background: var(--accent-subtle); }
.quick-add-icon svg { width: 25px; }
.quick-add-main { flex: 1; min-width: 170px; text-align: left; border: 0; background: none; color: inherit; cursor: pointer; }
.quick-add-main strong, .quick-add-main span { display: block; }
.quick-add-main strong { color: var(--text-primary); font-size: var(--text-md); }
.quick-add-main span { margin-top: 3px; color: var(--text-tertiary); font-size: var(--text-sm); }
.quick-kinds { display: flex; gap: 6px; }
.quick-kinds button { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 11px; color: var(--text-secondary); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: color-mix(in srgb, var(--surface-4) 75%, transparent); font: inherit; font-size: var(--text-sm); cursor: pointer; transition: border-color .15s, color .15s, transform .15s; }
.quick-kinds button:hover { color: var(--text-primary); border-color: var(--border-strong); transform: translateY(-1px); }
.quick-kinds svg { width: 16px; }

.primary-button, .secondary-button { display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; padding: 0 18px; border-radius: var(--radius-md); font: inherit; font-weight: 700; cursor: pointer; transition: transform .15s, box-shadow .15s, opacity .15s; }
.primary-button { color: var(--text-on-accent); border: 1px solid var(--accent); background: var(--accent); box-shadow: 0 8px 22px var(--accent-glow-sm); }
.primary-button:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 28px var(--accent-glow); }
.primary-button:disabled { cursor: not-allowed; opacity: .48; }
.primary-button svg, .secondary-button svg { width: 18px; }
.secondary-button { color: var(--text-secondary); border: 1px solid var(--border-default); background: var(--surface-4); }
.secondary-button:hover { color: var(--text-primary); border-color: var(--border-strong); }

.board-section { margin-top: 40px; }
.board-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  width: 100%; /* на всякий случай */
}

.board-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}
.section-title-row { display: flex; align-items: center; gap: 12px; }
.board-heading h2 { color: var(--text-primary); font-size: clamp(1.4rem, 2vw, 1.75rem); }
.board-heading p { margin-top: 5px; color: var(--text-tertiary); font-size: var(--text-sm); }
.admin-pill { display: inline-flex; align-items: center; gap: 6px; padding: 5px 9px; color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 30%, transparent); border-radius: 999px; background: var(--accent-subtle); font-size: var(--text-xs); font-weight: 700; }
.admin-pill svg { width: 14px; }
.search-box {
  display: flex;
  align-items: center;
  flex: 1 1 auto;          /* растягивается */
  max-width: 260px;        /* ограничиваем максимум */
  height: 40px;
  padding: 0 6px 0 13px;   /* справа меньше, т.к. есть кнопка */
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-3);
  transition: border-color .15s, box-shadow .15s;
}
.search-box:focus-within { border-color: var(--accent); box-shadow: var(--border-glow); }
.search-box > svg { width: 18px; flex: 0 0 auto; color: var(--text-tertiary); }
.search-box input { width: 100%; min-width: 0; padding: 0 9px; color: var(--text-primary); border: 0; outline: 0; background: none; font: inherit; }
.search-box input::placeholder { color: var(--text-tertiary); }
.search-box button {
  display: grid;
  width: 26px;
  height: 26px;
  flex: 0 0 26px;
  place-items: center;
  color: var(--text-tertiary);
  border: 0;
  background: none;
  cursor: pointer;
}
.search-box button svg { width: 16px; }
.view-switch { display: flex; margin-left: auto; padding: 3px; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-3); }
.view-switch button { display: grid; width: 34px; height: 32px; place-items: center; color: var(--text-tertiary); border: 0; border-radius: 8px; background: transparent; cursor: pointer; }
.view-switch button.active { color: var(--accent); background: var(--accent-subtle); }
.view-switch svg { width: 18px; }

.filter-bar { display: flex; align-items: center; gap: 10px; margin-top: 20px; padding-bottom: 14px; border-bottom: 1px solid var(--border-subtle); }
.filter-group { display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; }
.filter-group::-webkit-scrollbar { display: none; }
.filter-group button, .mine-filter { display: inline-flex; align-items: center; gap: 7px; height: 34px; flex: 0 0 auto; padding: 0 10px; color: var(--text-tertiary); border: 1px solid transparent; border-radius: var(--radius-md); background: transparent; font: inherit; font-size: var(--text-sm); cursor: pointer; }
.filter-group button:hover, .mine-filter:hover { color: var(--text-secondary); background: var(--surface-4); }
.filter-group button.active, .mine-filter.active { color: var(--text-primary); border-color: var(--border-default); background: var(--surface-4); }
.filter-group svg, .mine-filter svg { width: 16px; }
.filter-group button > span { min-width: 19px; padding: 1px 5px; border-radius: 999px; background: var(--surface-5); color: var(--text-tertiary); font-size: 10px; text-align: center; }
.status-filter { display: flex; align-items: center; height: 34px; margin-left: auto; padding: 0 8px 0 10px; color: var(--text-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-3); }
.status-filter svg { width: 15px; }
.status-filter select { height: 100%; padding: 0 6px; color: var(--text-secondary); border: 0; outline: none; background: transparent; font: inherit; font-size: var(--text-sm); cursor: pointer; }
.status-filter option, .admin-fields option { color: var(--text-primary); background: var(--surface-3); }

.kanban { display: grid; grid-auto-columns: minmax(280px, 1fr); grid-auto-flow: column; gap: 14px; margin-top: 18px; padding: 2px 2px 18px; overflow-x: auto; overscroll-behavior-inline: contain; scrollbar-width: thin; scrollbar-color: var(--border-strong) transparent; }
.kanban-column { min-height: 390px; padding: 13px; border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); background: color-mix(in srgb, var(--surface-2) 84%, transparent); transition: border-color .15s, background .15s; }
.kanban-column.drop-active { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 7%, var(--surface-2)); }
.kanban-column > header { display: flex; align-items: center; gap: 8px; }
.kanban-column h3 { color: var(--text-secondary); font-family: var(--font-sans); font-size: var(--text-sm); font-weight: 700; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--text-tertiary); box-shadow: 0 0 0 4px color-mix(in srgb, var(--text-tertiary) 12%, transparent); }
.column-planned .status-dot { background: var(--warning); box-shadow: 0 0 0 4px var(--warning-subtle); }
.column-in_progress .status-dot { background: var(--info); box-shadow: 0 0 0 4px var(--info-subtle); }
.column-review .status-dot { background: var(--accent); box-shadow: 0 0 0 4px var(--accent-subtle); }
.column-done .status-dot { background: var(--success); box-shadow: 0 0 0 4px var(--success-subtle); }
.column-declined .status-dot { background: var(--danger); box-shadow: 0 0 0 4px var(--danger-subtle); }
.column-count { margin-left: auto; min-width: 23px; padding: 2px 6px; color: var(--text-tertiary); border-radius: 999px; background: var(--surface-4); font-size: 10px; text-align: center; }
.column-hint { margin: 4px 0 12px 16px; color: var(--text-tertiary); font-size: 10px; }
.column-cards { display: flex; flex-direction: column; gap: 10px; }
.idea-card { border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--container-bg); box-shadow: var(--shadow-sm); overflow: hidden; transition: transform .18s var(--ease-petal), border-color .18s, box-shadow .18s, opacity .15s; }
.idea-card:hover { transform: translateY(-2px); border-color: var(--border-strong); box-shadow: var(--shadow-card-hover); }
.idea-card[draggable="true"] { cursor: grab; }
.idea-card.dragging { opacity: .4; transform: rotate(1deg) scale(.98); }
.card-open { display: block; width: 100%; padding: 14px 14px 11px; text-align: left; color: inherit; border: 0; background: none; cursor: pointer; }
.card-topline { display: flex; align-items: center; min-width: 0; gap: 6px; }
.kind-badge { display: inline-flex; align-items: center; gap: 5px; padding: 4px 7px; border-radius: 7px; font-size: 10px; font-weight: 700; }
.kind-badge svg { width: 13px; }
.kind-idea { color: var(--warning); background: var(--warning-subtle); }
.kind-bug { color: var(--danger); background: var(--danger-subtle); }
.kind-improvement { color: var(--info); background: var(--info-subtle); }
.priority-mark { padding: 3px 6px; border-radius: 6px; font-size: 9px; font-weight: 700; }
.priority-high { color: var(--warning); background: var(--warning-subtle); }
.priority-critical { color: var(--danger); background: var(--danger-subtle); }
.idea-number { margin-left: auto; color: var(--text-disabled); font-family: var(--font-mono); font-size: 9px; }
.card-open h4 { margin-top: 12px; color: var(--text-primary); font-family: var(--font-sans); font-size: var(--text-md); line-height: 1.38; }
.card-open > p { display: -webkit-box; margin-top: 7px; overflow: hidden; color: var(--text-tertiary); font-size: var(--text-sm); line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 3; }
.idea-card footer { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-top: 1px solid var(--border-subtle); }
.author-line { display: flex; align-items: center; min-width: 0; flex: 1; gap: 6px; color: var(--text-tertiary); font-size: 10px; }
.author-line img, .author-line .avatar-fallback { width: 20px; height: 20px; flex: 0 0 auto; }
.author-line > span:not(.avatar-fallback) { max-width: 78px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.author-line time::before { content: "·"; margin-right: 6px; }
.avatar-fallback { display: inline-grid; place-items: center; color: var(--text-on-accent); border-radius: 50%; background: linear-gradient(135deg, var(--accent), var(--accent-2)); font-size: 10px; font-weight: 800; }
.author-line img { object-fit: cover; border-radius: 50%; }
.vote-button { display: inline-flex; align-items: center; gap: 5px; min-width: 41px; height: 28px; justify-content: center; color: var(--text-tertiary); border: 1px solid var(--border-subtle); border-radius: 9px; background: var(--surface-4); font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.vote-button:hover, .vote-button.voted { color: var(--accent); border-color: color-mix(in srgb, var(--accent) 30%, transparent); background: var(--accent-subtle); }
.vote-button svg { width: 14px; }
.vote-button.voted svg { fill: currentColor; }
.column-add { display: flex; align-items: center; justify-content: center; gap: 6px; width: 100%; height: 38px; color: var(--text-tertiary); border: 1px dashed var(--border-default); border-radius: var(--radius-md); background: transparent; font: inherit; font-size: var(--text-sm); cursor: pointer; }
.column-add:hover { color: var(--accent); border-color: var(--accent); background: var(--accent-subtle); }
.column-add svg { width: 16px; }
.column-empty { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 28px 8px; color: var(--text-disabled); font-size: var(--text-xs); }
.column-empty svg { width: 24px; opacity: .6; }

.ideas-list { display: flex; flex-direction: column; gap: 7px; margin-top: 18px; }
.list-row { display: grid; grid-template-columns: 38px minmax(240px, 1fr) 130px 130px 56px 18px; align-items: center; gap: 14px; width: 100%; padding: 11px 14px; text-align: left; color: inherit; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: color-mix(in srgb, var(--container-bg) 90%, transparent); cursor: pointer; transition: border-color .15s, transform .15s, background .15s; }
.list-row:hover { transform: translateX(2px); border-color: var(--border-strong); background: var(--surface-4); }
.list-kind { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 10px; }
.list-kind svg { width: 18px; }
.list-copy { min-width: 0; }
.list-copy strong, .list-copy small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.list-copy strong { color: var(--text-primary); font-size: var(--text-sm); }
.list-copy small { margin-top: 3px; color: var(--text-tertiary); }
.status-badge { display: inline-flex; align-items: center; width: fit-content; flex-shrink: 0; gap: 7px; padding: 5px 8px; color: var(--text-tertiary); border-radius: 8px; background: var(--surface-4); font-size: 10px; font-weight: 700; white-space: nowrap; }
.status-badge i { width: 6px; height: 6px; flex-shrink: 0; border-radius: 50%; background: currentColor; }
.status-planned { color: var(--warning); background: var(--warning-subtle); }
.status-in_progress { color: var(--info); background: var(--info-subtle); }
.status-review { color: var(--accent); background: var(--accent-subtle); }
.status-done { color: var(--success); background: var(--success-subtle); }
.status-declined { color: var(--danger); background: var(--danger-subtle); }
.list-author { overflow: hidden; color: var(--text-tertiary); font-size: var(--text-xs); text-overflow: ellipsis; white-space: nowrap; }
.list-votes { display: flex; align-items: center; gap: 5px; color: var(--text-tertiary); font-size: var(--text-xs); font-weight: 700; }
.list-votes svg { width: 15px; }
.list-arrow { width: 17px; color: var(--text-disabled); }

.ideas-loading { display: grid; grid-template-columns: repeat(4, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }
.skeleton-card { height: 190px; padding: 18px; border: 1px solid var(--border-subtle); border-radius: var(--radius-lg); background: var(--surface-2); }
.skeleton-card span { display: block; height: 12px; margin-bottom: 18px; border-radius: 8px; background: linear-gradient(90deg, var(--surface-4), var(--surface-5), var(--surface-4)); background-size: 200% 100%; animation: skeleton 1.4s linear infinite; }
.skeleton-card span:first-child { width: 35%; }
.skeleton-card span:nth-child(2) { width: 82%; height: 18px; }
.skeleton-card span:last-child { width: 62%; }
@keyframes skeleton { to { background-position: -200% 0; } }
.state-card { display: flex; align-items: center; justify-content: center; gap: 14px; min-height: 220px; margin-top: 18px; padding: 28px; color: var(--text-tertiary); border: 1px dashed var(--border-default); border-radius: var(--radius-xl); background: color-mix(in srgb, var(--surface-2) 75%, transparent); text-align: center; }
.state-card > svg { width: 30px; }
.state-card strong { display: block; color: var(--text-primary); font-size: var(--text-lg); }
.state-card p { margin-top: 5px; }
.state-card button { display: inline-flex; align-items: center; gap: 6px; margin-top: 12px; padding: 8px 12px; color: var(--accent); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-4); font: inherit; cursor: pointer; }
.state-card button svg { width: 16px; }
.empty-state { flex-direction: column; }
.empty-icon { display: grid; width: 54px; height: 54px; place-items: center; color: var(--accent); border-radius: 50%; background: var(--accent-subtle); }
.empty-icon svg { width: 27px; }

.modal-layer, .drawer-layer { position: fixed; inset: 0; z-index: var(--z-modal); display: flex; background: rgba(4, 3, 8, .72); backdrop-filter: blur(10px); }
.modal-layer { align-items: center; justify-content: center; padding: 20px; }
.modal-card { width: min(100%, 670px); max-height: min(90vh, 850px); overflow-y: auto; border: 1px solid var(--border-strong); border-radius: var(--radius-2xl); background: var(--surface-2); box-shadow: var(--shadow-modal); }
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; padding: 24px 26px 20px; border-bottom: 1px solid var(--border-subtle); }
.modal-kicker { display: flex; align-items: center; gap: 6px; color: var(--accent); font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: .08em; }
.modal-kicker svg { width: 15px; }
.modal-header h2 { margin-top: 7px; font-size: 1.55rem; }
.modal-header p { margin-top: 6px; color: var(--text-tertiary); font-size: var(--text-sm); }
.icon-button { display: grid; width: 36px; height: 36px; flex: 0 0 auto; place-items: center; color: var(--text-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-4); cursor: pointer; }
.icon-button:hover { color: var(--text-primary); border-color: var(--border-strong); }
.icon-button svg { width: 19px; }
.idea-form { padding: 22px 26px 24px; }
.kind-picker { border: 0; }
.kind-picker legend, .field-label > span { display: flex; width: 100%; justify-content: space-between; margin-bottom: 9px; color: var(--text-secondary); font-size: var(--text-sm); font-weight: 700; }
.kind-picker { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.kind-picker legend { grid-column: 1 / -1; }
.kind-picker label { position: relative; display: flex; align-items: center; gap: 9px; min-height: 70px; padding: 10px; border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-3); cursor: pointer; }
.kind-picker label:hover, .kind-picker label.selected { border-color: var(--accent); background: var(--accent-subtle); }
.kind-picker input { position: absolute; opacity: 0; }
.picker-icon { display: grid; width: 34px; height: 34px; flex: 0 0 auto; place-items: center; border-radius: 10px; }
.picker-icon svg { width: 18px; }
.kind-picker label > span:nth-of-type(2) { min-width: 0; }
.kind-picker strong, .kind-picker small { display: block; }
.kind-picker strong { color: var(--text-primary); font-size: var(--text-sm); }
.kind-picker small { margin-top: 2px; color: var(--text-tertiary); font-size: 9px; line-height: 1.25; }
.picker-check { width: 16px; flex: 0 0 16px; margin-left: auto; color: var(--accent); opacity: 0; }
.selected .picker-check { opacity: 1; }
.field-label { display: block; margin-top: 18px; }
.field-label b { color: var(--text-disabled); font-size: 10px; font-weight: 500; }
.field-label input, .field-label textarea, .admin-fields select { width: 100%; color: var(--text-primary); border: 1px solid var(--border-default); border-radius: var(--radius-md); outline: none; background: var(--surface-3); font: inherit; transition: border-color .15s, box-shadow .15s; }
.field-label input { height: 44px; padding: 0 13px; }
.field-label textarea { resize: vertical; min-height: 110px; padding: 12px 13px; line-height: 1.5; }
.field-label input:focus, .field-label textarea:focus, .admin-fields select:focus { border-color: var(--accent); box-shadow: var(--border-glow); }
.field-label input::placeholder, .field-label textarea::placeholder { color: var(--text-disabled); }
.form-error { display: flex; gap: 7px; align-items: center; margin-top: 14px; padding: 10px; color: var(--danger); border-radius: var(--radius-md); background: var(--danger-subtle); font-size: var(--text-sm); }
.form-error svg { width: 18px; }
.modal-footer { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin-top: 22px; padding-top: 18px; border-top: 1px solid var(--border-subtle); }
.modal-footer > p { display: flex; align-items: center; gap: 6px; color: var(--text-tertiary); font-size: var(--text-xs); }
.modal-footer > p svg { width: 15px; }
.modal-footer > div { display: flex; gap: 8px; }
.search-box input::-webkit-search-cancel-button,
.search-box input::-webkit-search-decoration {
  -webkit-appearance: none;
  appearance: none;
}
.drawer-layer { justify-content: flex-end; }
.detail-drawer { display: flex; flex-direction: column; width: min(100%, 560px); height: 100%; border-left: 1px solid var(--border-strong); background: var(--surface-2); box-shadow: -18px 0 60px rgba(0, 0, 0, .45); }
.drawer-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 17px 20px; border-bottom: 1px solid var(--border-subtle); }
.drawer-topline { display: flex; align-items: center; gap: 9px; }
.drawer-scroll { flex: 1; min-height: 0; overflow-y: auto; }
.drawer-title-block { padding: 28px 28px 24px; border-bottom: 1px solid var(--border-subtle); }
.status-badge.large { padding: 6px 9px; font-size: var(--text-xs); }
.drawer-title-block h2 { margin-top: 16px; font-size: clamp(1.55rem, 3vw, 2rem); line-height: 1.18; }
.drawer-author { display: flex; align-items: center; gap: 10px; margin-top: 20px; }
.drawer-author img, .drawer-author > .avatar-fallback { width: 36px; height: 36px; object-fit: cover; border-radius: 50%; }
.drawer-author > span:last-child { display: flex; flex-direction: column; }
.drawer-author strong { color: var(--text-secondary); font-size: var(--text-sm); }
.drawer-author small { margin-top: 2px; color: var(--text-tertiary); font-size: var(--text-xs); }
.detail-section { padding: 24px 28px; }
.detail-section h3 { color: var(--text-secondary); font-family: var(--font-sans); font-size: var(--text-sm); }
.idea-description { margin-top: 12px; color: var(--text-secondary); line-height: 1.72; white-space: pre-wrap; overflow-wrap: anywhere; }
.admin-note { margin: 0 28px 24px; padding: 16px; border: 1px solid color-mix(in srgb, var(--accent) 28%, transparent); border-radius: var(--radius-lg); background: var(--accent-subtle); }
.admin-note > div { display: flex; align-items: center; gap: 7px; color: var(--accent); font-size: var(--text-sm); }
.admin-note svg { width: 17px; }
.admin-note p { margin-top: 8px; color: var(--text-secondary); line-height: 1.55; white-space: pre-wrap; }
.detail-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; margin: 0 28px 24px; border: 1px solid var(--border-subtle); border-radius: var(--radius-md); background: var(--border-subtle); overflow: hidden; }
.detail-meta > div { padding: 12px; background: var(--surface-3); }
.detail-meta span, .detail-meta strong { display: block; }
.detail-meta span { color: var(--text-tertiary); font-size: 10px; }
.detail-meta strong { margin-top: 4px; color: var(--text-secondary); font-size: var(--text-xs); }
.text-priority-high { color: var(--warning) !important; }
.text-priority-critical { color: var(--danger) !important; }
.admin-controls { margin: 0 28px 28px; padding: 18px; border: 1px solid var(--border-default); border-radius: var(--radius-lg); background: var(--surface-3); }
.admin-controls-title { display: flex; align-items: center; gap: 10px; }
.admin-controls-title > svg { width: 22px; color: var(--accent); }
.admin-controls-title div { display: flex; flex-direction: column; }
.admin-controls-title strong { color: var(--text-primary); font-size: var(--text-sm); }
.admin-controls-title span { color: var(--text-tertiary); font-size: 10px; }
.admin-fields { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.admin-fields label > span { display: block; margin-bottom: 6px; color: var(--text-tertiary); font-size: var(--text-xs); }
.admin-fields select { height: 39px; padding: 0 10px; }
.admin-textarea { margin-top: 13px; }
.admin-textarea textarea { min-height: 80px; }
.admin-save { display: flex; align-items: center; justify-content: center; gap: 7px; width: 100%; height: 40px; margin-top: 12px; color: var(--text-on-accent); border: 0; border-radius: var(--radius-md); background: var(--accent); font: inherit; font-weight: 700; cursor: pointer; }
.admin-save:disabled { cursor: default; opacity: .45; }
.admin-save svg { width: 17px; }
.drawer-footer { display: flex; align-items: center; gap: 9px; padding: 14px 20px max(14px, env(safe-area-inset-bottom)); border-top: 1px solid var(--border-default); background: var(--surface-2); }
.drawer-vote { display: flex; flex: 1; align-items: center; justify-content: center; gap: 10px; min-height: 48px; color: var(--text-secondary); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-4); font: inherit; cursor: pointer; }
.drawer-vote:hover, .drawer-vote.voted { color: var(--accent); border-color: var(--accent); background: var(--accent-subtle); }
.drawer-vote > svg { width: 20px; }
.drawer-vote.voted > svg { fill: currentColor; }
.drawer-vote span { display: flex; flex-direction: column; text-align: left; }
.drawer-vote strong { font-size: var(--text-sm); }
.drawer-vote small { margin-top: 1px; color: var(--text-tertiary); font-size: 10px; }
.delete-button { display: grid; width: 48px; height: 48px; place-items: center; color: var(--text-tertiary); border: 1px solid var(--border-default); border-radius: var(--radius-md); background: var(--surface-4); cursor: pointer; }
.delete-button:hover { color: var(--danger); border-color: var(--danger); background: var(--danger-subtle); }
.delete-button svg { width: 19px; }

.spin { animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.modal-fade-enter-active, .modal-fade-leave-active, .drawer-fade-enter-active, .drawer-fade-leave-active { transition: opacity .2s ease; }
.modal-fade-enter-active .modal-card, .modal-fade-leave-active .modal-card { transition: transform .24s var(--ease-petal), opacity .2s; }
.modal-fade-enter-from, .modal-fade-leave-to, .drawer-fade-enter-from, .drawer-fade-leave-to { opacity: 0; }
.modal-fade-enter-from .modal-card, .modal-fade-leave-to .modal-card { opacity: 0; transform: translateY(12px) scale(.98); }
.drawer-fade-enter-active .detail-drawer, .drawer-fade-leave-active .detail-drawer { transition: transform .26s var(--ease-petal); }
.drawer-fade-enter-from .detail-drawer, .drawer-fade-leave-to .detail-drawer { transform: translateX(100%); }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }

@media (max-width: 1100px) {
  .ideas-hero { align-items: flex-start; }
  .hero-stats { display: none; }
  .quick-kinds { display: none; }
  .ideas-loading { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 800px) {
  .ideas-shell { padding: 24px 16px 54px; }
  .ideas-hero { padding: 14px 0 26px; }
  .quick-add { gap: 11px; padding: 13px; }
  .quick-add-icon { width: 42px; height: 42px; }
  .quick-add .primary-button { padding: 0 13px; font-size: 0; }
  .quick-add .primary-button svg { width: 19px; }
  .board-section { margin-top: 30px; }
  .board-heading { align-items: flex-start; }
  .board-actions { flex: 1; justify-content: flex-end; }
  .search-box { width: min(100%, 260px); }

  .filter-bar { flex-wrap: wrap; }
  .filter-group { width: 100%; }
  .status-filter { margin-left: 0; }
  .kanban { margin-right: -16px; padding-right: 16px; }
  .list-row { grid-template-columns: 36px minmax(0, 1fr) auto 16px; gap: 10px; }
  .list-author, .list-votes { display: none; }
  .ideas-loading { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 560px) {
  .hero-copy h1 { font-size: 2.15rem; }
  .hero-copy p { font-size: var(--text-sm); }
  .quick-add-icon { display: none; }
  .quick-add-main span { display: none; }
  .board-heading { display: block; }
  .board-actions { justify-content: space-between; margin-top: 14px; }
  .search-box { width: calc(100% - 84px); }
  .admin-pill { display: none; }
  .kanban { grid-auto-columns: minmax(272px, 86vw); }
  .list-row { grid-template-columns: 34px minmax(0, 1fr) 16px; }
  .list-row .status-badge { grid-column: 2; grid-row: 2; }
  .list-arrow { grid-column: 3; grid-row: 1 / 3; }
  .ideas-loading { grid-template-columns: 1fr; }
  .modal-layer { align-items: flex-end; padding: 0; }
  .modal-card { max-height: 94dvh; border-radius: 22px 22px 0 0; }
  .modal-header { padding: 20px 18px 16px; }
  .idea-form { padding: 17px 18px max(20px, env(safe-area-inset-bottom)); }
  .kind-picker { grid-template-columns: 1fr; }
  .kind-picker label { min-height: 58px; }
  .modal-footer { align-items: stretch; flex-direction: column; }
  .modal-footer > div { display: grid; grid-template-columns: 1fr 1fr; }
  .detail-drawer { width: 100%; border-left: 0; }
  .drawer-title-block, .detail-section { padding-inline: 20px; }
  .admin-note, .detail-meta, .admin-controls { margin-inline: 20px; }
  .detail-meta { grid-template-columns: 1fr; }
  .admin-fields { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation-duration: .01ms !important; transition-duration: .01ms !important; }
}
</style>
