<template>
  <main class="legal-page">
    <article class="legal-document">
      <header class="legal-header">
        <p class="legal-eyebrow">Правовая информация</p>
        <h1>{{ title }}</h1>
        <p class="legal-subtitle">{{ subtitle }}</p>
        <div class="legal-meta">
          <span>Редакция от {{ updatedAt }}</span>
          <span v-if="effectiveAt">Действует с {{ effectiveAt }}</span>
        </div>
      </header>

      <div class="legal-intro">
        <slot name="intro" />
      </div>

      <nav class="legal-toc" aria-label="Содержание документа">
        <strong>Содержание</strong>
        <ol>
          <li v-for="section in sections" :key="section.id">
            <a :href="`#${section.id}`" @click="openSection(section.id)">{{ section.number }}. {{ section.title }}</a>
          </li>
        </ol>
        <button type="button" @click="toggleAll">{{ allOpen ? 'Свернуть все разделы' : 'Раскрыть все разделы' }}</button>
      </nav>

      <div class="legal-sections">
        <details
          v-for="(section, index) in sections"
          :id="section.id"
          :key="section.id"
          ref="details"
          class="legal-section"
          :open="index === 0"
          @toggle="syncOpenState"
        >
          <summary>
            <span class="section-number">{{ section.number }}</span>
            <span class="section-title">{{ section.title }}</span>
            <svg
              class="section-chevron"
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
          <div class="section-content">
            <slot :name="section.id" />
          </div>
        </details>
      </div>

      <footer class="legal-footer">
        <p>Актуальная редакция: {{ updatedAt }}.</p>
        <RouterLink to="/contacts">Контакты администрации</RouterLink>
      </footer>
    </article>
  </main>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue';

export interface LegalSection {
  id: string;
  number: string;
  title: string;
}

defineProps<{
  title: string;
  subtitle: string;
  updatedAt: string;
  effectiveAt?: string;
  sections: LegalSection[];
}>();

const details = ref<HTMLDetailsElement[]>([]);
const allOpen = ref(false);

function syncOpenState() {
  allOpen.value = details.value.length > 0 && details.value.every(item => item.open);
}

function openSection(id: string) {
  const section = details.value.find(item => item.id === id);
  if (section) section.open = true;
}

async function toggleAll() {
  const next = !allOpen.value;
  details.value.forEach(item => { item.open = next; });
  await nextTick();
  allOpen.value = next;
}
</script>

<style scoped>
.legal-page{min-height:100vh;padding:clamp(20px,4vw,52px) clamp(12px,3vw,28px) 72px;background:var(--page-bg,var(--surface-1));color:var(--text-primary)}
.legal-document{width:min(980px,100%);margin:0 auto;overflow:hidden;border:1px solid var(--border-subtle);border-radius:24px;background:var(--surface-2);box-shadow:var(--shadow-lg)}
.legal-header{padding:clamp(28px,5vw,58px) clamp(20px,6vw,64px) 30px;background:linear-gradient(145deg,color-mix(in srgb,var(--accent) 10%,var(--surface-3)),var(--surface-2));border-bottom:1px solid var(--border-subtle)}
.legal-eyebrow{margin:0 0 10px;color:var(--accent);font-size:12px;font-weight:800;letter-spacing:.1em;text-transform:uppercase}
.legal-header h1{margin:0 0 12px;font-family:var(--font-display);font-size:clamp(2rem,5vw,3.25rem);line-height:1.1;letter-spacing:-.035em}
.legal-subtitle{max-width:720px;margin:0;color:var(--text-secondary);font-size:clamp(.95rem,2vw,1.08rem);line-height:1.65}
.legal-meta{display:flex;flex-wrap:wrap;gap:8px 18px;margin-top:20px;color:var(--text-tertiary);font-size:12px}
.legal-intro{padding:26px clamp(20px,6vw,64px) 8px;color:var(--text-secondary);font-size:1rem;line-height:1.7}
.legal-intro :deep(p){margin:0 0 12px}.legal-intro :deep(strong){color:var(--text-primary)}
.legal-toc{margin:18px clamp(20px,6vw,64px) 26px;padding:20px;border:1px solid var(--border-subtle);border-radius:16px;background:var(--surface-3)}
.legal-toc strong{font-size:.9rem}.legal-toc ol{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px 22px;margin:14px 0 16px;padding-left:22px}
.legal-toc a{color:var(--text-secondary);font-size:.88rem;line-height:1.4;text-decoration:none}.legal-toc a:hover,.legal-toc a:focus-visible{color:var(--accent);text-decoration:underline}
.legal-toc button{padding:7px 11px;border:1px solid var(--border-default);border-radius:9px;background:var(--surface-2);color:var(--text-secondary);font:inherit;font-size:.8rem;cursor:pointer}.legal-toc button:hover{color:var(--accent);border-color:var(--accent)}
.legal-sections{padding:0 clamp(20px,6vw,64px) 30px}
.legal-section{scroll-margin-top:90px;border-top:1px solid var(--border-subtle)}
.legal-section:last-child{border-bottom:1px solid var(--border-subtle)}
.legal-section summary{display:grid;grid-template-columns:38px minmax(0,1fr) 24px;align-items:center;gap:12px;min-height:74px;padding:10px 2px;cursor:pointer;list-style:none}.legal-section summary::-webkit-details-marker{display:none}
.section-number{display:grid;place-items:center;width:34px;height:34px;border-radius:10px;background:var(--accent-subtle);color:var(--accent);font-size:.8rem;font-weight:800}
.section-title{font-family:var(--font-display);font-size:clamp(1rem,2.5vw,1.2rem);font-weight:750;line-height:1.3}.section-chevron{width:20px;height:20px;color:var(--text-tertiary);transition:transform .18s}.legal-section[open] .section-chevron{transform:rotate(180deg)}
.section-content{padding:0 4px 28px 50px;color:var(--text-secondary);font-size:.94rem;line-height:1.72}
.section-content :deep(p){margin:0 0 12px}.section-content :deep(p:last-child){margin-bottom:0}.section-content :deep(ul),.section-content :deep(ol){margin:8px 0 14px;padding-left:22px}.section-content :deep(li){margin:0 0 8px}.section-content :deep(strong){color:var(--text-primary)}.section-content :deep(a){color:var(--accent)}
.section-content :deep(h3){margin:22px 0 8px;color:var(--text-primary);font-size:.98rem}.section-content :deep(h3:first-child){margin-top:0}
.section-content :deep(.legal-note){padding:13px 15px;border-left:3px solid var(--accent);border-radius:8px;background:var(--accent-subtle)}
.section-content :deep(.legal-warning){padding:13px 15px;border:1px solid color-mix(in srgb,#f59e0b 45%,var(--border-subtle));border-radius:10px;background:color-mix(in srgb,#f59e0b 10%,var(--surface-2));color:var(--text-primary)}
.section-content :deep(.legal-table){width:100%;border-collapse:collapse;margin:12px 0;font-size:.88rem}.section-content :deep(.legal-table th),.section-content :deep(.legal-table td){padding:10px;border:1px solid var(--border-subtle);text-align:left;vertical-align:top}.section-content :deep(.legal-table th){background:var(--surface-3);color:var(--text-primary)}
.section-content :deep(.contact-actions){display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.section-content :deep(.contact-actions a){padding:9px 13px;border:1px solid var(--border-default);border-radius:10px;background:var(--surface-3);font-weight:650;text-decoration:none}
.legal-footer{display:flex;justify-content:space-between;gap:18px;padding:22px clamp(20px,6vw,64px);border-top:1px solid var(--border-subtle);color:var(--text-tertiary);font-size:.82rem}.legal-footer p{margin:0}.legal-footer a{color:var(--accent)}
@media(max-width:680px){.legal-document{border-radius:16px}.legal-toc ol{grid-template-columns:1fr}.section-content{padding-left:2px}.legal-section summary{grid-template-columns:34px minmax(0,1fr) 20px;gap:9px}.legal-footer{flex-direction:column}.section-content :deep(.legal-table){display:block;overflow-x:auto}}
@media(prefers-reduced-motion:reduce){.section-chevron{transition:none}}
</style>
