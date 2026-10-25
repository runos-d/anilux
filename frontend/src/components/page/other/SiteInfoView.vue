<template>
  <div class="anime-view">
    <section class="av-container">
      <h1>{{ document?.name || 'Контакты' }}</h1>
      <div v-html="document?.text || ''"></div>
      <a :href="'mailto:' + navigation.email">{{ navigation.email }}</a>
    </section>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import navigation from '@/site-navigation.json';
const route = useRoute();
const document = computed(() => navigation.documents.find(item => item.path === route.path));
</script>
