<template>
  <CommentsModal v-if="show" :post="post" @close="$emit('close')" @comment-added="$emit('comment-added', $event)" />
</template>
<script setup lang="ts">
import CommentsModal from '@/components/feed/CommentsModal.vue';
import type { FeedPost, PostComment } from '@/api/feed';
withDefaults(defineProps<{ show?: boolean; post: FeedPost }>(), { show: true });
defineEmits<{ close: []; 'comment-added': [comment: PostComment] }>();
</script>
