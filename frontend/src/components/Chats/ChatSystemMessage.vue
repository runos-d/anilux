<template>
  <div class="chat-system-message" :class="{ 'chat-system-message--block': message.system_action === 'block' }" role="status">
    <SakuraIcon :name="message.system_action === 'block' ? 'lock' : 'unlock'" :size="18" />
    <span>{{ text }}</span>
    <time :datetime="message.created_at">{{ new Date(message.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) }}</time>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import SakuraIcon from '@/components/icons/SakuraIcon.vue';
import type { Message } from '@/types/chat';
const props = defineProps<{ message: Message; userId?: number }>();
const text = computed(() => {
  const message = props.message;
  const action = message.system_action === 'block' ? 'заблокировал(а)' : message.system_action === 'unblock' ? 'разблокировал(а)' : null;
  if (!action) return message.text || 'Системное сообщение';
  if (message.sender_id === props.userId) return message.system_action === 'block' ? 'Вы заблокировали пользователя' : 'Вы разблокировали пользователя';
  if (Number(message.system_target_user) === props.userId) return `${message.sender_username || 'Пользователь'} ${action} вас`;
  return message.text || `${message.sender_username || 'Пользователь'} ${action} пользователя`;
});
</script>

<style scoped>
.chat-system-message { display: flex; align-items: center; justify-content: center; gap: 8px; width: fit-content; max-width: 90%; margin: 12px auto; padding: 10px 14px; border: 1px solid var(--border-subtle, #3b3b50); border-radius: 10px; background: var(--surface-2, #171722); color: var(--text-secondary, #b9bacb); font-size: 13px; text-align: center; }
.chat-system-message--block { border-color: #cf657955; background: #cf657918; }
.chat-system-message time { opacity: .65; font-size: 11px; flex-shrink: 0; }
</style>
