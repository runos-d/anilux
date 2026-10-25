<template>
  <div class="anime-view">
    <section class="av-container">
      <h1>{{ docName }}</h1>
      <div v-if="error" class="error">{{ error }}</div>
      <div v-else v-html="content"></div>
      <a v-if="navigation.email" :href="'mailto:' + navigation.email" class="contact-link">
        {{ navigation.email }}
      </a>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import navigation from '@/site-navigation.json';

const route = useRoute();
const docName = computed(() => {
  const doc = navigation.documents.find(item => item.path === route.path);
  return doc ? doc.name : 'Документ';
});

const content = ref('');
const error = ref<string | null>(null);

onMounted(async () => {
  const path = route.path; // e.g., "/terms"
  const filePath = `${path.slice(1)}.html`;
  try {
    const resp = await fetch(filePath, { cache: 'no-store' });
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const text = await resp.text();
    content.value = text;
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : String(e);
    error.value = `Не удалось загрузить документ: ${message}`;
    console.error(e);
  }
});
</script>

<style scoped>
.anime-view {
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.av-container {
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
h1 {
  color: #111;
  margin-top: 0;
}
.error {
  color: #d32f2f;
  background: #ffebee;
  padding: 1rem;
  border-radius: 4px;
  margin: 1rem 0;
}
.contact-link {
  display: inline-block;
  margin-top: 1.5rem;
  color: #1976d2;
  text-decoration: none;
}
.contact-link:hover {
  text-decoration: underline;
}
</style>
