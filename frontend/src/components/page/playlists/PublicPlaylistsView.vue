<script setup lang="ts">
import { onMounted } from "vue"
import { useRouter } from "vue-router"
const router = useRouter();

onMounted(() => {
  router.replace({ path: "/playlists", query: { tab: "public" } });
});
</script>

<template>
  <div></div>
</template>