<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useRoute } from "vue-router"
import apiClient, { getMediaUrl } from "@/api/client"
const route = useRoute();

interface Announcement {
  title_ru: string;
  title_en?: string;
  created_at: string;
  description?: string;
  release_date?: string;
  poster_url?: string;
}

const announcement = ref<Announcement | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const description = computed(() => new DOMParser().parseFromString(announcement.value?.description || '', 'text/html').body.textContent || '');

onMounted(async () => {
  try {
    const slug = route.params.slug;
    const response = await apiClient.get(`/anime/announcements/${slug}/`);
    announcement.value = response.data;
  } catch (e: unknown) {
    error.value =
      (e as { response?: { data?: { detail?: string } } })?.response?.data
        ?.detail || "Ошибка загрузки анонса"
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="announcement-detail">
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="announcement" class="content">
      <h1>{{ announcement.title_ru || announcement.title_en }}</h1>
      <img v-if="announcement.poster_url" :src="getMediaUrl(announcement.poster_url) || announcement.poster_url" :alt="`Постер ${announcement.title_ru || announcement.title_en}`" width="240" height="360" fetchpriority="high">
      <div class="meta">
        <span>{{
          new Date(announcement.created_at).toLocaleDateString()
        }}</span>
      </div>
      <p v-if="announcement.release_date">Выход: {{ announcement.release_date }}</p>
      <p class="body">{{ description }}</p>
    </div>
  </div>
</template>

<style scoped>
.announcement-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
h1 {
  font-size: 2rem;
  margin-bottom: 1rem;
}
.meta {
  color: #888;
  margin-bottom: 2rem;
}
.body {
  line-height: 1.6;
}

@media (max-width: 900px) and (min-width: 601px) {
  .announcement-detail {
    max-width: 100%;
    padding: 1.75rem 1.5rem;
  }
  h1 {
    font-size: 1.75rem;
    margin-bottom: 0.85rem;
  }
  .meta {
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
  }
  .body {
    font-size: 0.95rem;
    line-height: 1.65;
  }
}

@media (max-width: 600px) {
  .announcement-detail {
    max-width: 100%;
    padding: 1.25rem 1rem;
  }
  h1 {
    font-size: 1.45rem;
    margin-bottom: 0.75rem;
    line-height: 1.3;
  }
  .meta {
    margin-bottom: 1.25rem;
    font-size: 0.875rem;
  }
  .body {
    font-size: 0.9375rem;
    line-height: 1.65;
  }
  .loading,
  .error {
    font-size: 0.95rem;
  }
}

@media (max-width: 380px) {
  .announcement-detail {
    padding: 1rem 0.75rem;
  }
  h1 {
    font-size: 1.25rem;
    margin-bottom: 0.6rem;
  }
  .meta {
    margin-bottom: 1rem;
    font-size: 0.8rem;
  }
  .body {
    font-size: 0.875rem;
    line-height: 1.6;
  }
  .loading,
  .error {
    font-size: 0.9rem;
  }
}
</style>
