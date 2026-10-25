<template>
  <div v-if="variant === 'directory'" class="collection-links-groups collection-links-groups--directory">
    <section v-for="group in groups" :key="group.name" class="collection-links-group directory-card">
      <h3>{{ group.name }}</h3>
      <p>{{ directoryCopy[group.name]?.description || 'Выберите подходящую подборку.' }}</p>
      <details v-if="group.links.length" class="directory-picker" @toggle="handleDirectoryToggle">
        <summary>
          {{ directoryCopy[group.name]?.placeholder || 'Выберите раздел' }}
          <svg
            class="directory-picker-chevron"
            aria-hidden="true"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </summary>
        <div class="directory-options">
          <RouterLink v-for="link in group.links" :key="link.path" :to="link.path">{{ link.name }}</RouterLink>
        </div>
      </details>
      <div v-else class="directory-empty">Пока нет доступных вариантов</div>
    </section>
  </div>
  <div v-else class="collection-links-groups">
    <section v-for="group in groups" :key="group.name" class="collection-links-group">
      <h3>{{ group.name }}</h3>
      <div class="collection-links-list">
        <RouterLink v-for="link in group.links" :key="link.path" :to="link.path">{{ link.name }}</RouterLink>
      </div>
    </section>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';
type Link = { name: string; path: string };
const props = withDefaults(defineProps<{ links?: Link[]; groups?: Array<{ name: string; links: Link[] }>; variant?: 'footer' | 'directory' }>(), {
  variant: 'footer',
});
const directoryCopy: Record<string, { description: string; placeholder: string }> = {
  'По годам': { description: 'Аниме, выпущенные в выбранном году.', placeholder: 'Выберите год' },
  'Жанры': { description: 'Подборки по настроению и тематике.', placeholder: 'Выберите жанр' },
  'Сезоны': { description: 'Премьеры зимы, весны, лета и осени.', placeholder: 'Выберите сезон' },
  'Статусы': { description: 'Онгоинги, завершённые и анонсированные тайтлы.', placeholder: 'Выберите статус' },
  'Разделы каталога': { description: 'Основные разделы каталога аниме.', placeholder: 'Выберите раздел' },
};
function handleDirectoryToggle(event: Event) {
  const current = event.currentTarget as HTMLDetailsElement;
  if (!current.open) return;
  document.querySelectorAll<HTMLDetailsElement>('.directory-picker[open]').forEach(picker => {
    if (picker !== current) picker.open = false;
  });
}
const groups = computed(() => {
  if (props.groups) return props.groups;
  const map = new Map<string, Link[]>();
  for (const link of props.links || []) {
    const facet = link.path.includes('genres=') ? 'genre' : (link.path.split('/')[2] || '');
    const name = ({ year: 'По годам', genre: 'Жанры', type: 'Форматы', status: 'Статусы'} as Record<string, string>)[facet] || 'Разделы каталога';
    if (!map.has(name)) map.set(name, []);
    if (!map.get(name)!.some(item => item.path === link.path)) map.get(name)!.push(link);
  }
  if (props.variant === 'directory') {
    return ['По годам', 'Жанры', 'Форматы', 'Статусы']
      .map(name => ({ name, links: map.get(name) || [] }));
  }
  return [...map].map(([name, links]) => ({ name, links }));
});
</script>
<style scoped>
.collection-links-groups {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: clamp(1rem, 1.5vw, 1.5rem);
  min-width: 0;
}

.collection-links-group {
  min-width: 0;
}

.collection-links-group h3 {
  margin: 0 0 var(--space-3);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-weight: 650;
}

.collection-links-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.collection-links-list a {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
  min-width: 0;
  min-height: 30px;
  box-sizing: border-box;
  padding: 5px 8px 5px 18px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  line-height: 1.4;
  overflow-wrap: anywhere;
  text-decoration: none;
  transition: color .15s, border-color .15s, background .15s, transform .15s;
}

.collection-links-list a::before {
  content: "";
  position: absolute;
  left: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.55;
}

.collection-links-list a:hover,
.collection-links-list a:focus-visible {
  background: var(--accent-subtle);
  border-color: var(--border-default);
  color: var(--text-accent);
  transform: translateX(2px);
}

.collection-links-groups--directory {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  align-items: start;
  gap: var(--space-4);
}

.directory-card {
  padding: clamp(18px, 2vw, 24px);
  background: var(--color-background-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
}

.directory-card h3 {
  margin-bottom: var(--space-2);
  font-size: var(--text-base);
  font-weight: 700;
}

.directory-card > p {
  min-height: 42px;
  margin: 0 0 var(--space-4);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  line-height: 1.55;
}

.directory-picker {
  position: relative;
}

.directory-picker[open] {
  z-index: 30;
}

.directory-picker summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 44px;
  box-sizing: border-box;
  padding: 10px 14px;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  font-weight: 600;
  cursor: pointer;
  list-style: none;
  transition: color .15s, border-color .15s, background .15s;
}

.directory-empty {
  display: flex;
  align-items: center;
  min-height: 44px;
  box-sizing: border-box;
  padding: 10px 14px;
  background: var(--surface-2);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
}

.directory-picker summary::-webkit-details-marker {
  display: none;
}

.directory-picker-chevron {
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  color: var(--text-tertiary);
  transition: transform .15s;
}

.directory-picker[open] summary,
.directory-picker summary:hover,
.directory-picker summary:focus-visible {
  border-color: var(--accent);
  color: var(--text-accent);
}

.directory-picker[open] .directory-picker-chevron {
  transform: rotate(180deg);
}

.directory-options {
  position: absolute;
  top: calc(100% + var(--space-2));
  left: 0;
  right: 0;
  z-index: 30;
  display: grid;
  gap: 4px;
  max-height: 280px;
  padding: var(--space-2);
  overflow-y: auto;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: 0 18px 42px rgba(0, 0, 0, 0.32);
}

.directory-options a {
  padding: 9px 10px;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  text-decoration: none;
}

.directory-options a:hover,
.directory-options a:focus-visible {
  background: var(--accent-subtle);
  color: var(--text-accent);
}

@media (max-width: 1100px) {
  .collection-links-groups {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767px) {
  .collection-links-groups {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--space-6) var(--space-3);
  }

  .collection-links-list a {
    min-height: 38px;
    padding-top: 7px;
    padding-bottom: 7px;
  }

  .collection-links-groups--directory {
    grid-template-columns: 1fr;
    gap: var(--space-3);
  }
}

@media (max-width: 299px) {
  .collection-links-groups {
    grid-template-columns: 1fr;
  }
}
</style>
