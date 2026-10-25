<template>
  <SakuraCursor v-if="sakuraEnabled" />
  <NewYearCursor v-if="newYearEnabled" />
  <HalloweenCursor v-if="halloweenEnabled" />
  <LoveDayCursor v-if="loveDayEnabled" />
</template>

<script setup lang="ts">
import SakuraCursor from "./SakuraCursor.vue";
import NewYearCursor from "./NewYearCursor.vue";
import HalloweenCursor from "./HalloweenCursor.vue";
import LoveDayCursor from "./LoveDayCursor.vue";
import { useSakuraOverlay } from "@/composables/useSakuraOverlay";
import { useNewYearOverlay } from "@/composables/useNewYearOverlay";
import { useHalloweenOverlay } from "@/composables/useHalloweenOverlay";
import { useLoveDayOverlay } from "@/composables/useLoveDayOverlay";

const { sakuraEnabled } = useSakuraOverlay();
const { newYearEnabled } = useNewYearOverlay();
const { halloweenEnabled } = useHalloweenOverlay();
const { loveDayEnabled } = useLoveDayOverlay();
</script>
