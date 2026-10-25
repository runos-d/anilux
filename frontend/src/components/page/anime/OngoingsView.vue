<template>
  <CatalogView
    :anime-list="anime"
    :loading="loading"
    :error="error"
    :page="page"
    :total-pages="totalPages"
    :total-count="totalCount"
    :filters="filters"
    :page-size="filters?.page_size || 50"
    :show-status="false"
    :show-shuffle="false"
    :group-franchises="false"
    :scroll-on-page-change="false"
    @page-change="$emit('pageChange', $event)"
    @filter-change="$emit('filterChange', $event)"
    @refresh="$emit('refresh')"
  />
</template>

<script setup lang="ts">
import CatalogView from "./CatalogView.vue";
import type { FilterState } from "@/components/Filters/AnimeFilterBar.vue";
import type { Anime } from "@/types";

defineProps<{
  anime: Anime[];
  loading: boolean;
  error: string | null;
  page: number;
  totalPages: number;
  totalCount: number;
  filters?: FilterState;
  viewersMap?: Record<number, number>;
}>();

defineEmits<{
  refresh: [];
  pageChange: [page: number];
  filterChange: [filters: FilterState];
}>();
</script>
