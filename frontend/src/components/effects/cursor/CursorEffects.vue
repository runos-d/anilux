<template>
  <SakuraCursor v-if="sakuraEnabled" />
  <NewYearCursor v-if="newYearEnabled" />
  <HalloweenCursor v-if="halloweenEnabled" />
  <LoveDayCursor v-if="loveDayEnabled" />
</template>

<script setup lang="ts">
import { defineAsyncComponent } from "vue";
const SakuraCursor = defineAsyncComponent(() => import("./SakuraCursor.vue"));
const NewYearCursor = defineAsyncComponent(() => import("./NewYearCursor.vue"));
const HalloweenCursor = defineAsyncComponent(() => import("./HalloweenCursor.vue"));
const LoveDayCursor = defineAsyncComponent(() => import("./LoveDayCursor.vue"));
import { useSakuraOverlay } from "@/composables/useSakuraOverlay";
import { useNewYearOverlay } from "@/composables/useNewYearOverlay";
import { useHalloweenOverlay } from "@/composables/useHalloweenOverlay";
import { useLoveDayOverlay } from "@/composables/useLoveDayOverlay";

const { sakuraEnabled } = useSakuraOverlay();
const { newYearEnabled } = useNewYearOverlay();
const { halloweenEnabled } = useHalloweenOverlay();
const { loveDayEnabled } = useLoveDayOverlay();
</script>
