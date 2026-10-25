<template>
  <article
    class="crc"
    :class="{ 'is-premiere': item.is_upcoming }"
    :style="{ '--tint': kindColor(item.anime.kind) }"
    role="link"
    tabindex="0"
    @click="emit('click')"
    @keydown.enter.space.prevent="emit('click')"
  >
    <div class="crc-poster-wrap">
      <img
        v-if="item.anime.poster_url"
        :src="item.anime.poster_url"
        :alt="item.anime.title_ru"
        class="crc-poster"
        loading="lazy"
      />
      <div v-else class="crc-poster crc-poster-empty">
        {{ initial }}
      </div>
    </div>

    <div class="crc-body">
      <div class="crc-title-row">
        <span class="crc-title">
          {{ item.anime.title_ru || item.anime.title_en }}
        </span>
      </div>
      <div class="crc-meta">
        <span class="crc-time">{{ item.time }}</span>
        <span class="crc-kind">{{ itemLabel(item) }}</span>
      </div>
      <span v-if="item.schedule_uncertain" class="crc-uncertain">Расписание уточняется</span>
    </div>

    <span v-if="item.anime.score" class="crc-score">
      {{ item.anime.score.toFixed(1) }}
    </span>
    <button v-if="auth.isAuthenticated && item.calendar_release_id && (item.episode_number || item.anime.kind === 'movie')"
      class="crc-reminder" :class="{ 'is-active': !!reminder }" type="button" :disabled="savingReminder"
      :aria-pressed="!!reminder"
      :aria-label="reminder ? 'Отключить напоминание' : `Напомнить о серии ${item.episode_number || 1}`"
      :title="reminder ? `Отключить напоминание (${new Date(reminder.reminder_time).toLocaleString('ru-RU')})` : 'Напомнить о выходе серии'"
      @click.stop="toggleReminder">
      <SakuraIcon :name="reminder ? 'bell-off' : 'bell'" :size="16" />
    </button>
  </article>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { CalendarItem } from "@/api/anime";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notifications';
import { useToast } from '@/composables/useToast';

const props = defineProps<{ item: CalendarItem }>();
const emit = defineEmits<{ click: [] }>();
const auth = useAuthStore();
const notifications = useNotificationStore();
const toast = useToast();
const savingReminder = ref(false);
const reminder = computed(() => notifications.reminders.find(r =>
  r.calendar_release === props.item.calendar_release_id && r.is_active));
const toggleReminder = async () => {
  if (savingReminder.value) return;
  savingReminder.value = true;
  try {
    if (reminder.value) {
      await notifications.deactivateReminder(reminder.value.id);
      toast.success('Напоминание отключено');
    } else {
      await notifications.createReminder({ calendar_release_id: props.item.calendar_release_id,
        follow_schedule: true, timezone_name: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC' });
      toast.success('Напоминание о серии установлено');
    }
  } catch {
    toast.error(reminder.value ? 'Не удалось отключить напоминание' : 'Не удалось установить напоминание');
  } finally { savingReminder.value = false; }
};

const KIND_COLORS: Record<string, string> = {
  tv: "var(--accent)",
  movie: "var(--accent-3, #f59e0b)",
  special: "var(--accent-2, #2dd4bf)",
  ova: "var(--accent-4, #a78bfa)",
  ona: "var(--accent-2, #22d3ee)",
  music: "var(--accent, #f472b6)",
};

const KIND_LABELS: Record<string, string> = {
  tv: "ТВ-сериал",
  movie: "Фильм",
  ova: "OVA",
  special: "Спецвыпуск",
  ona: "ONA",
  music: "Клип",
  franchise: "Франшиза",
};
const kindColor = (k?: string) => (k ? KIND_COLORS[k] : "var(--accent)");
const kindLabel = (k?: string) => (k ? KIND_LABELS[k] || k : "");

const itemLabel = (item: CalendarItem) => {
  if (item.anime.kind === "movie") return "Фильм";
  if (item.episode_number) return `Серия ${item.episode_number}`;
  return kindLabel(item.anime.kind);
};

const initial = computed(() => {
  const t = props.item.anime.title_ru || props.item.anime.title_en || "?";
  return (t as string).trim().charAt(0).toUpperCase();
});
</script>

<style scoped>
.crc-reminder { display: grid; place-items: center; flex-shrink: 0; width: 36px; height: 36px; border: 1px solid var(--border-subtle); border-radius: 50%; background: var(--surface-3); color: var(--text-primary); cursor: pointer; }
.crc-reminder:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.crc-reminder.is-active { border-color: var(--accent); background: var(--accent-subtle); color: var(--accent); }
.crc-reminder:disabled { opacity: .65; cursor: default; }
.crc-uncertain { font-size: 11px; color: var(--text-secondary); }
.crc {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 46px;
  padding: 5px var(--space-3) 5px 5px;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.16s var(--ease-out);
}

.crc:hover {
  border-color: color-mix(in srgb, var(--tint, var(--accent)) 60%, var(--border-default));
  background: var(--surface-5);
  transform: translateX(2px);
  box-shadow: 0 4px 14px color-mix(in srgb, var(--tint, var(--accent)) 12%, transparent);
}

.crc:hover .crc-poster {
  transform: scale(1.06);
}

.crc.is-premiere {
  border-color: color-mix(in srgb, var(--accent) 42%, var(--border-subtle));
  background: color-mix(in srgb, var(--accent) 7%, var(--surface-4));
}

.crc-poster-wrap {
  position: relative;
  flex-shrink: 0;
}

.crc-poster {
  width: 34px;
  height: 46px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  display: block;
  background: var(--surface-5);
  border: 1px solid var(--border-subtle);
  transition: transform 0.16s var(--ease-out);
}

.crc-poster-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  font-weight: 850;
  color: var(--text-tertiary);
  background: linear-gradient(
    150deg,
    var(--surface-5),
    color-mix(in srgb, var(--tint, var(--accent)) 18%, var(--surface-5))
  );
}

.crc-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.crc-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.crc-title {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.crc-premiere {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent) 70%, #7c3aed));
  color: white;
  box-shadow: 0 2px 8px var(--accent-glow);
}

.crc-premiere :deep(.sakura-icon) {
  color: white;
}

.crc-meta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.crc-time {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 800;
  color: var(--text-primary);
  background: color-mix(in srgb, var(--tint, var(--accent)) 18%, var(--surface-3));
  padding: 1px 7px;
  border-radius: var(--radius-full);
  font-variant-numeric: tabular-nums;
}

.crc-kind {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.crc-score {
  flex-shrink: 0;
  font-size: var(--text-xs);
  font-weight: 800;
  color: var(--text-secondary);
  font-variant-numeric: tabular-nums;
  padding-right: 2px;
}
</style>
