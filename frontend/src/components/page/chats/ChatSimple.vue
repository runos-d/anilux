<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { useRoute } from "vue-router";
import apiClient from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import { webSocketProtocols } from '@/lib/chatTimeline';

const route = useRoute();
const authStore = useAuthStore();

const chatId = computed(() => {
  const p = route.params.id;
  if (!p || p === "undefined") return undefined;
  const n = parseInt(String(p), 10);
  return isNaN(n) ? undefined : n;
});

interface ChatSummary {
  id: number;
  name?: string | null;
}

interface ChatMessage {
  id: number | string;
  text: string;
}

const chat = ref<ChatSummary | null>(null);
const messages = ref<ChatMessage[]>([]);
const loading = ref(false);
const ws = ref<WebSocket | null>(null);

const loadChat = async () => {
  const id = chatId.value;
  if (!id) return;
  loading.value = true;
  try {
    const res = await apiClient.get(`/social/chats/${id}/`);
    chat.value = res.data || null;
  } catch {
    chat.value = null;
  } finally {
    loading.value = false;
  }
};

const connect = () => {
  if (ws.value) { try { ws.value.close(); } catch {} ws.value = null; }
  const id = chatId.value;
  if (!id) return;
  const token = authStore.token || "";
  const url = `${window.location.origin.replace(/^http/, "ws")}/ws/chat/${id}/`;
  ws.value = new WebSocket(url, webSocketProtocols(token));
  ws.value.onopen = () => {};
  ws.value.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data) as {
        action?: string;
        messages?: ChatMessage[];
        message?: ChatMessage;
      };
      if (d.action === "init") messages.value = d.messages || [];
      else if (d.action === "new_message" && d.message) messages.value = [...messages.value, d.message];
    } catch {}
  };
};

watch(chatId, () => { messages.value = []; loadChat(); connect(); });

onMounted(() => { loadChat(); connect(); });
onUnmounted(() => { if (ws.value) try { ws.value.close(); } catch {}; });
</script>

<template>
  <div class="chat-simple">
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="!chat" class="empty">Чат не найден</div>
    <div v-else class="chat-body">
      <h2>{{ chat.name || "Чат" }}</h2>
      <div class="messages">
        <div v-for="m in messages" :key="m.id" class="msg">{{ m.text }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-simple { display:flex; flex-direction:column; height:100%; padding:1rem; background:#111; color:#eee; }
.loading, .empty { padding:2rem; text-align:center; }
.chat-body { flex:1; overflow:auto; }
.messages { display:flex; flex-direction:column; gap:.5rem; }
.msg { background:#222; padding:.5rem .75rem; border-radius:.5rem; }
</style>
