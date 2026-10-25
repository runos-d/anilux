<template>
  <div class="kodik-import-page">
    <div class="page-header">
      <h1><SakuraIcon name="package" /> Импорт аниме и франшизы</h1>
      <p class="page-description">
        Импорт аниме из Kodik API и сбор франшиз из живой Shikimori API.
        Всё выполняется в фоне на сервере.
      </p>
    </div>

    <!-- ===================== СТАТИСТИКА ===================== -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">Всего аниме в базе</div>
          <div class="stat-value">{{ formatNum(stats.anime_total) }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">Аниме из Kodik</div>
          <div class="stat-value">{{ formatNum(stats.anime_kodik) }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">Франшиз</div>
          <div class="stat-value">{{ formatNum(stats.franchises) }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-info">
          <div class="stat-label">Аниме во франшизах</div>
          <div class="stat-value">{{ formatNum(stats.anime_in_franchises) }}</div>
        </div>
      </div>
      <div class="stat-card stat-status">
        <div class="stat-info">
          <div class="stat-label">Статус фоновой задачи</div>
          <div class="stat-value" :class="statusClass">
            {{ statusText }}
        <div class="option-group">
          <label class="dp-toggle-row">
            <span class="dp-toggle-text">
              <span class="dp-toggle-title">Скачивать постеры</span>
              <span class="dp-toggle-desc">Сохранять постеры локально в каталоге вместо использования внешних ссылок Kodik</span>
            </span>
            <span class="dp-switch" :class="{ on: downloadPosters }" @click="downloadPosters = !downloadPosters">
              <span class="dp-switch-thumb" />
            </span>
          </label>
        </div>
        </div>
      </div>
    </div>

    <!-- ===================== ИМПОРТ KODIK ===================== -->
    <div class="control-panel">
      <h2><SakuraIcon name="download" /> Импорт аниме из Kodik</h2>

      <div class="import-options">
        <div class="option-group">
          <label class="option-label">Режим:</label>
          <select v-model="kodikMode" class="select-input">
            <option value="update">
              Продолжение: добавить новые + обновить существующие
            </option>
            <option value="new">Только новые (не трогать существующие)</option>
            <option value="full">Полная перезапись с нуля (очистить базу)</option>
          </select>
        </div>

        <div class="option-group">
          <label class="option-label">
            <input type="checkbox" v-model="useLimit" />
            Ограничить количество
          </label>
          <input
            v-if="useLimit"
            type="number"
            v-model.number="limit"
            min="1"
            class="limit-input"
          />
        </div>

        <div class="option-group">
          <label class="option-label">
            <input type="checkbox" v-model="skipEpisodes" />
            Не тянуть сезоны/серии (быстрее)
          </label>
        </div>

        </div>
      </div>

      <div class="action-buttons">
        <button @click="runKodikImport" :disabled="busy" class="btn btn-primary">
          <SakuraIcon name="rocket" /> Запустить в фоне
        </button>
      </div>
    </div>

    <!-- ===================== ФРАНШИЗЫ ===================== -->
    <div class="control-panel">
      <h2><SakuraIcon name="network" /> Сбор франшиз (живая Shikimori API)</h2>
      <p class="panel-hint">
        Каждая франшиза строится по официальному дереву Шикимори
        (<code>/animes/:id/franchise</code>). Части внутри франшизы сортируются
        по порядку просмотра (sequel / prequel / parent_story и т.п.).
      </p>

      <div class="import-options">
        <div class="option-group">
          <label class="option-label">Режим:</label>
          <select v-model="frMode" class="select-input">
            <option value="incremental">
              Продолжение: только аниме без франшизы (существующие не трогаем)
            </option>
            <option value="full">Полная пересборка с нуля</option>
          </select>
        </div>
      </div>

      <div class="action-buttons">
        <button
          @click="runFranchiseRebuild"
          :disabled="busy"
          class="btn btn-primary"
        >
          <SakuraIcon name="refresh" /> Запустить в фоне
        </button>
        <div v-if="frMode === 'incremental'" class="btn-hint">
          Безопасно: можно запускать повторно после нового импорта аниме
        </div>
      </div>
    </div>

    <!-- ===================== ОСТАНОВКА ===================== -->
    <div v-if="job.running" class="control-panel stop-panel">
      <h2><SakuraIcon name="square" /> Остановить фоновую задачу</h2>
      <p class="panel-hint">
        Текущая задача ещё выполняется на сервере. Остановка завершает процесс
        принудительно -незавершённая работа будет откачена частично.
      </p>
      <div class="action-buttons">
        <button @click="stopJob" :disabled="stopping" class="btn btn-stop">
          <SakuraIcon name="square" />
          {{ stopping ? "Останавливаем..." : "Остановить задачу" }}
        </button>
      </div>
    </div>

    <!-- ===================== DANGER ZONE ===================== -->
    <div class="control-panel danger-panel">
      <h2><SakuraIcon name="ban" /> Опасная зона: полная очистка</h2>
      <p class="panel-hint">
        Удаление выполняется на сервере напрямую и без отката. Перед очисткой
        остановите фоновые задачи.
      </p>
      <div class="action-buttons">
        <button
          @click="wipeAll(['franchises'])"
          :disabled="busy"
          class="btn btn-danger"
        >
          <SakuraIcon name="trash" /> Удалить все франшизы
        </button>
        <button
          @click="wipeAll(['anime'])"
          :disabled="busy"
          class="btn btn-danger"
        >
          <SakuraIcon name="trash" /> Удалить все аниме
        </button>
        <button
          @click="wipeAll(['anime', 'franchises'])"
          :disabled="busy"
          class="btn btn-danger-strong"
        >
          <SakuraIcon name="trash" /> Удалить всё (аниме + франшизы)
        </button>
      </div>
      <div v-if="wipeResult" class="btn-hint wipe-result">{{ wipeResult }}</div>
    </div>

    <!-- ===================== ПРОГРЕСС ===================== -->
    <div v-if="jobHasContent" class="progress-section">
      <div class="progress-header">
        <h3><SakuraIcon name="chart" /> {{ jobTitle }}</h3>
        <div class="progress-stats">
          <span v-if="job.running" class="pulse">Выполняется...</span>
          <span v-else-if="job.finished && job.stopped" class="warn-text"
            >Остановлена пользователем</span
          >
          <span v-else-if="job.finished && job.success === true" class="ok"
            >Завершено успешно</span
          >
          <span v-else-if="job.finished" class="err">Завершено с ошибкой</span>
          <button
            v-if="job.running"
            @click="stopJob"
            :disabled="stopping"
            class="btn btn-stop"
          >
            <SakuraIcon name="square" /> Остановить
          </button>
        </div>
      </div>

      <div class="progress-bar-container">
        <div
          class="progress-bar-fill"
          :class="{
            done: job.finished && job.success === true,
            err: job.finished && !job.stopped && !job.success,
            warn: job.finished && job.stopped,
          }"
          :style="progressStyle"
        ></div>
      </div>

      <div
        v-if="alreadyRunning"
        class="warning"
      >
        Другая фоновая задача уже выполняется. Подождите её завершения.
      </div>

      <div class="logs-container">
        <div
          v-for="(line, index) in logLines"
          :key="index"
          class="log-entry"
        >
          {{ line }}
        </div>
        <div v-if="!logLines.length" class="log-entry log-empty">
          Лог пуст...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import apiClient from "@/api/client";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";

const stats = ref({
  anime_total: 0,
  anime_kodik: 0,
  franchises: 0,
  anime_in_franchises: 0,
});

const kodikMode = ref<"new" | "update" | "full">("update");
const useLimit = ref(false);
const limit = ref(100);
const skipEpisodes = ref(false);
const downloadPosters = ref(false);

const frMode = ref<"incremental" | "full">("incremental");

const job = ref({
  running: false,
  finished: false,
  stopped: false,
  success: null as boolean | null,
  already_running: false,
  type: "" as string | null,
  command: "" as string | null,
  log: "",
});
const pollTimer = ref<ReturnType<typeof setInterval> | null>(null);
const stopping = ref(false);
const wipeResult = ref("");

const statusText = computed(() => {
  if (job.value.running) return "Выполняется";
  if (job.value.finished && job.value.stopped) return "Остановлена";
  if (job.value.finished && job.value.success === true) return "Готово";
  if (job.value.finished && job.value.success === false) return "Ошибка";
  return "Простаивает";
});

const statusClass = computed(() => {
  if (job.value.running) return "st-running";
  if (job.value.finished && job.value.stopped) return "st-err";
  if (job.value.finished && job.value.success === true) return "st-ok";
  if (job.value.finished && job.value.success === false) return "st-err";
  return "st-idle";
});

const jobHasContent = computed(
  () => job.value.running || job.value.finished || job.value.already_running,
);

const jobTitle = computed(() => {
  if (job.value.command === "import_from_kodik") return "Импорт аниме из Kodik";
  if (job.value.command === "rebuild_franchises") return "Сбор франшиз из Shikimori";
  return job.value.command || "Фоновая задача";
});

const alreadyRunning = computed(
  () => !job.value.running && job.value.already_running,
);

const logLines = computed(() => {
  const log = job.value.log || "";
  const lines = log.split(/\r?\n/).filter((l) => l.trim());
  return lines.slice(-30);
});

const progressStyle = computed(() => {
  if (job.value.running) return { width: "100%" };
  return { width: "100%" };
});

const busy = computed(
  () =>
    (job.value.running && !job.value.already_running) ||
    job.value.already_running,
);

const formatNum = (n: number) => {
  if (!n && n !== 0) return "-";
  return n.toLocaleString("ru-RU");
};

const applyStatus = (data: {
  running?: boolean;
  finished?: boolean;
  stopped?: boolean;
  success?: boolean | null;
  already_running?: boolean;
  type?: string | null;
  command?: string | null;
  log?: string;
  stats?: Record<string, unknown>;
}) => {
  job.value = {
    running: !!data.running,
    finished: !!data.finished,
    stopped: !!data.stopped,
    success: data.success === null ? null : !!data.success,
    already_running: !!data.already_running,
    type: (data.type as string | null) || null,
    command: (data.command as string | null) || null,
    log: (data.log as string) || "",
  };
  if (data.stats) stats.value = data.stats as { anime_total: number; anime_kodik: number; franchises: number; anime_in_franchises: number };
};

const loadStatus = async () => {
  try {
    const { data } = await apiClient.get("/admin/import-status/");
    applyStatus(data);
  } catch {
    /* ignore */
  }
};

const startPolling = async () => {
  await loadStatus();
  stopPolling();
  pollTimer.value = setInterval(loadStatus, 2500);
};

const stopPolling = () => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
};

const runKodikImport = async () => {
  try {
    const res = await apiClient.post("/admin/run-kodik-import/", {
      mode: kodikMode.value,
      limit: useLimit.value ? limit.value : undefined,
      skip_episodes: skipEpisodes.value,
      download_posters: downloadPosters.value,
    });
    if (res.data?.started === false) {
      job.value.already_running = true;
    }
    await startPolling();
  } catch (error: unknown) {
    job.value.finished = true;
    job.value.success = false;
    job.value.log =
      "Ошибка запуска: " +
      ((error as Error)?.message || "неизвестная ошибка");
  }
};

const runFranchiseRebuild = async () => {
  try {
    const res = await apiClient.post("/admin/run-franchise-rebuild/", {
      mode: frMode.value,
    });
    if (res.data?.started === false) {
      job.value.already_running = true;
    }
    await startPolling();
  } catch (error: unknown) {
    job.value.finished = true;
    job.value.success = false;
    job.value.log =
      "Ошибка запуска: " +
      ((error as Error)?.message || "неизвестная ошибка");
  }
};

const stopJob = async () => {
  stopping.value = true;
  try {
    const { data } = await apiClient.post("/admin/stop-import/");
    if (data?.stopped) {
      job.value.log += "\n[остановка запрошена...]";
    }
    await startPolling();
  } catch (error: unknown) {
    job.value.log +=
      "\nОшибка остановки: " +
      ((error as Error)?.message || "неизвестная ошибка");
  } finally {
    stopping.value = false;
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
    const { data } = await apiClient.post("/admin/wipe-all/", { targets });
    const parts: string[] = [];
    if (typeof data?.anime_deleted === "number")
      parts.push(`аниме: ${data.anime_deleted}`);
    if (typeof data?.franchises_deleted === "number")
      parts.push(`франшиз: ${data.franchises_deleted}`);
    wipeResult.value =
      "Очищено -" + (parts.length ? parts.join(", ") : "ничего не удалено");
    await loadStatus();
  } catch (error: unknown) {
    wipeResult.value =
      "Ошибка очистки: " + ((error as Error)?.message || "неизвестная ошибка");
  }
};

onMounted(loadStatus);
onUnmounted(stopPolling);
</script>

<style scoped>
.kodik-import-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}
.page-header h1 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.page-description {
  color: var(--text-secondary);
  font-size: 0.95rem;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1rem 1.25rem;
}
.stat-label {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin-bottom: 0.25rem;
}
.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-primary);
}
.stat-value.st-ok {
  color: var(--success);
}
.stat-value.st-err {
  color: var(--danger);
}
.stat-value.st-running {
  color: var(--accent);
}
.stat-value.st-idle {
  color: var(--text-tertiary);
}

.control-panel {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}
.control-panel h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.panel-hint {
  color: var(--text-secondary);
  font-size: 0.85rem;
  margin: 0 0 1rem 0;
}
.panel-hint code {
  background: var(--surface-4);
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.8rem;
}

.import-options {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 1.25rem;
  align-items: center;
}
.option-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.option-label {
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  white-space: nowrap;
}
.select-input,
.limit-input {
  height: 36px;
  padding: 0 10px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  outline: none;
  font-size: 0.875rem;
}
.limit-input {
  width: 90px;
}

.action-buttons {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}
.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  height: 38px;
  padding: 0 18px;
  border-radius: var(--radius-md);
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  border: 1px solid transparent;
  transition: opacity 0.15s ease;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-hint {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}
.btn-stop {
  background: var(--warning);
  color: #1a1a1a;
}
.btn-stop:hover:not(:disabled) {
  filter: brightness(1.08);
}
.btn-danger,
.btn-danger-strong {
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
.danger-panel {
  border-color: color-mix(in srgb, var(--danger) 35%, transparent);
}
.wipe-result {
  margin-top: 0.5rem;
  color: var(--text-secondary);
}
.stop-panel {
  border-color: color-mix(in srgb, var(--warning) 45%, transparent);
}

.progress-section {
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 1.25rem 1.5rem;
}
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}
.progress-header h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.progress-stats {
  font-size: 0.875rem;
  font-weight: 600;
}
.pulse {
  color: var(--accent);
  animation: blinker 1.2s ease-in-out infinite;
}
.ok {
  color: var(--success);
}
.err {
  color: var(--danger);
}
.warn-text {
  color: var(--warning);
}
@keyframes blinker {
  50% {
    opacity: 0.35;
  }
}

.progress-bar-container {
  height: 8px;
  background: var(--surface-4);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}
.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--accent-hover));
  transition: width 0.4s ease;
  animation: load 1.4s ease-in-out infinite;
}
.progress-bar-fill.done {
  background: var(--success);
  animation: none;
}
.progress-bar-fill.err {
  background: var(--danger);
  animation: none;
}
.progress-bar-fill.warn {
  background: var(--warning);
  animation: none;
}
@keyframes load {
  0% {
    width: 40%;
  }
  50% {
    width: 90%;
  }
  100% {
    width: 40%;
  }
}

.warning {
  background: color-mix(in srgb, var(--warning) 15%, transparent);
  color: var(--warning);
  border-radius: var(--radius-md);
  padding: 0.5rem 0.75rem;
  font-size: 0.85rem;
  margin-bottom: 0.75rem;
}

.logs-container {
  background: var(--surface-4);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
  max-height: 340px;
  overflow-y: auto;
  font-family: "Consolas", monospace;
  font-size: 0.8rem;
}
.log-entry {
  color: var(--text-secondary);
  padding: 0.15rem 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.log-empty {
  color: var(--text-tertiary);
}

.dp-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  cursor: pointer;
  user-select: none;
}
.dp-toggle-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dp-toggle-title {
  font-size: var(--text-md, 0.9375rem);
  font-weight: 600;
  color: var(--text-primary, #fff);
}
.dp-toggle-desc {
  font-size: var(--text-sm, 0.75rem);
  line-height: 1.45;
  color: var(--text-tertiary, #9aa);
  max-width: 560px;
}
.dp-switch {
  position: relative;
  width: 52px;
  height: 28px;
  flex-shrink: 0;
  background: var(--surface-5, #2a2340);
  border: 1px solid var(--border-default, #333);
  border-radius: 999px;
  transition: background 0.2s, border-color 0.2s;
}
.dp-switch .dp-switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--text-tertiary, #9aa);
  transition: transform 0.2s, background 0.2s;
}
.dp-switch.on {
  background: var(--accent-subtle, rgba(255, 126, 179, 0.25));
  border-color: var(--accent, #ff7eb3);
}
.dp-switch.on .dp-switch-thumb {
  transform: translateX(24px);
  background: var(--accent, #ff7eb3);
}

@media (max-width: 768px) {
  .kodik-import-page {
    padding: 1rem;
  }
  .import-options {
    flex-direction: column;
    align-items: flex-start;
  }
  .action-buttons {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>