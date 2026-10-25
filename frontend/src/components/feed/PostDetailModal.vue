<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="post-detail-modal" @click.stop>
      <button class="close-btn" @click="$emit('close')">✕</button>

      <div class="post-detail" v-if="post">
        <PostCard :post="post" :comments-inline="false"
          @like="handleLike" @dislike="handleDislike" @repost="$emit('repost', post)"
          @comment="$emit('comment', post)" @bookmark="bookmark" />

        <CommentSection :post-id="post.id" :post="post" mode="modal" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import apiClient from '@/api/client';
import CommentSection from './CommentSection.vue';
import PostCard from './PostCard.vue';
import { usePostStore } from '@/stores/posts';
import type { FeedPost } from '@/api/feed';

const props = defineProps<{ post: FeedPost | null }>();
const store = usePostStore();
const post = computed(() => props.post ? store.entities[String(props.post.id)] || props.post : null);
defineEmits<{ close: []; comment: [post: FeedPost]; repost: [post: FeedPost] }>();
const handleLike = async () => { if (post.value) await store.react(post.value, 'like'); };
const handleDislike = async () => { if (post.value) await store.react(post.value, 'dislike'); };
const bookmark = async () => {
  if (!post.value) return;
  const id = post.value.id;
  await apiClient.post(`/social/posts/${id}/bookmark/`, { active: !post.value.is_bookmarked, client_action_id: crypto.randomUUID() });
  await store.refresh(id);
};
onMounted(() => { if (props.post) store.upsert(props.post); });
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.post-detail-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
}

.close-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
}

.author-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  cursor: pointer;
}

.author-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.name {
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.username,
.time {
  color: #666;
  font-size: 0.85rem;
}

.btn-follow {
  background: #667eea;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
}

.post-title {
  color: #fff;
  padding: 1.5rem 1.5rem 0;
}

.post-text {
  padding: 1rem 1.5rem;
  color: #ddd;
  line-height: 1.6;
}

.hashtags {
  padding: 0 1.5rem 1rem;
}

.hashtag {
  color: #667eea;
  margin-right: 0.5rem;
  cursor: pointer;
}

.media-gallery {
  padding: 0 1.5rem 1rem;
}

.media-item img,
.media-item video {
  width: 100%;
  border-radius: 8px;
}

.single-media {
  padding: 0 1.5rem 1rem;
}

.single-media img,
.single-media video {
  width: 100%;
  max-height: 500px;
  object-fit: contain;
  background: #000;
  border-radius: 8px;
}

.anime-card {
  margin: 0 1.5rem 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 0.75rem;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 1rem;
}

.playlist-card {
  margin: 0 1.5rem 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.anime-poster {
  width: 80px;
  height: 120px;
  object-fit: cover;
  border-radius: 6px;
  flex-shrink: 0;
}

.anime-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.anime-info .title {
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
}

.anime-info .title-en {
  color: #888;
  font-size: 0.8rem;
}

.anime-info .rating {
  color: #667eea;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.stats-bar {
  display: flex;
  gap: 1.5rem;
  padding: 0.75rem 1.5rem;
  border-top: 1px solid #1f1f1f;
  border-bottom: 1px solid #1f1f1f;
  color: #666;
  font-size: 0.9rem;
}

.actions-bar {
  display: flex;
  justify-content: space-around;
  padding: 0.75rem 1.5rem;
}

.actions-bar button {
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0.5rem;
  border-radius: 8px;
  transition: background 0.2s;
}

.actions-bar button:hover {
  background: #1a1a1a;
}

.actions-bar button.active {
  color: #667eea;
}

.comments-section {
  padding: 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.comments-section h3 {
  color: #fff;
  margin-bottom: 1rem;
}

.sort-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.sort-tabs button {
  background: #1a1a1a;
  color: #666;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  cursor: pointer;
}

.sort-tabs button.active {
  background: #667eea;
  color: white;
}

.comment-input {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.avatar-sm {
  width: 32px;
  height: 32px;
  border-radius: 50%;
}

.comment-input input {
  flex: 1;
  background: #1a1a1a;
  border: none;
  color: #ddd;
  padding: 0.75rem;
  border-radius: 20px;
}

.comment-input input:focus {
  outline: none;
}

.comment-input button {
  background: #667eea;
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
}

.comment-input button:disabled {
  opacity: 0.5;
}

.comments-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.comment {
  display: flex;
  gap: 0.75rem;
}

.comment-content {
  flex: 1;
  background: #1a1a1a;
  padding: 0.75rem;
  border-radius: 8px;
}

.comment-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.comment-header .author {
  color: #fff;
  font-weight: 600;
}

.comment-header .time {
  color: #555;
  font-size: 0.8rem;
}

.comment-content p {
  color: #ddd;
  margin-bottom: 0.5rem;
}

.comment-actions {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.comment-actions button {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: none;
  border: none;
  color: var(--text-tertiary);
  padding: 0.35rem 0.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.15s var(--ease-petal);
}

.comment-actions button:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.comment-actions button.liked {
  color: var(--danger);
}

.comment-actions button.disliked {
  color: var(--warning);
}

.no-comments {
  text-align: center;
  color: #666;
  padding: 2rem;
}
</style>
