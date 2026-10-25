<template>
  <Toast :toasts="toasts" @remove="removeToast" />
</template>

<script setup lang="ts">
import { useToast as useToastComposable } from "@/composables/useToast"
import Toast from "./Toast.vue"
const { toasts, removeToast } = useToastComposable();
</script>
