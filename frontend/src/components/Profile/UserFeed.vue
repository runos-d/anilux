<template>
  <div class="user-feed">
    <div v-if="loading" class="loading">
      <LoadingSpinner />
      <p>Загрузка ленты...</p>
    </div>
    <div v-else-if="posts.length === 0" class="empty">
      <p>Нет записей</p>
    </div>
    <div v-else class="posts-list">
      <PostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        :can-interact="canInteract"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import LoadingSpinner from "@/components/ui/LoadingSpinner.vue"
import PostCard from "@/components/Cards/PostCard.vue"
import { postsApi } from "@/api/feed"
import type { FeedPost } from "@/api/feed"

interface Post {
  id: number;
  author: { id: number; username: string; display_name: string | null; avatar: string | null };
  author_username: string;
  author_avatar: string | null;
  created_at: string;
  is_following: boolean;
  text: string;
  media_files: { media_type: string; url: string | null }[];
  image_url: string | null;
  image_file: string | null;
  video_url: string | null;
  video_file: string | null;
  media_url: string | null;
  post_type: string;
  playlist: { id: number; anime: { id: number; poster: string; title_ru: string }[] } | null;
  playlist_title: string | null;
  anime: { id: number; title_ru: string; title_en: string; poster?: string; poster_url?: string; poster_image_url?: string } | null;
  anime_title: string | null;
  original_post_data: { author_username: string; text: string } | null;
  likes_count: number;
  dislikes_count: number;
  comments_count: number;
  reposts_count: number;
  is_liked: boolean;
  is_disliked: boolean;
  is_favorited: boolean;
  allow_comments: boolean;
}

interface Props {
  userId: number;
}

const props = defineProps<Props>();

const authStore = useAuthStore();
const loading = ref(true);
const posts = ref<Post[]>([]);

const currentUser = computed(() => authStore.user);

const canInteract = computed(() => {
  return currentUser.value?.id === props.userId;
});

const toPostCardPost = (post: FeedPost): Post => {
  return {
    ...post,
    author: {
      id: post.author,
      username: post.author_username,
      display_name: post.author_display_name,
      avatar: post.author_avatar,
    },
    media_url: post.media_files?.[0]?.url ?? null,
    playlist_title: post.playlist?.title ?? null,
    anime_title: post.anime?.title_ru ?? null,
    original_post_data: post.original_post
      ? {
          author_username: post.original_post.author_username,
          text: post.original_post.text,
        }
      : null,
    is_favorited: post.is_bookmarked,
  } as Post;
};

onMounted(async () => {
  loading.value = true;
  try {
    const response = await postsApi.getUserPosts(props.userId);
    const rawPosts = response.data.results || response.data;
    posts.value = rawPosts.map(toPostCardPost);
  } catch (error) {
    console.error("Ошибка загрузки ленты:", error);
    posts.value = [];
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.user-feed {
  min-height: 400px;
}

.loading,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  color: var(--text-secondary);
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>