<template>
  <div class="message-actions">
    <div class="actions-trigger" @click="toggleMenu">
      <span class="trigger-icon">⋯</span>
    </div>

    <Transition name="fade">
      <div v-if="isOpen" class="actions-menu" @click.stop>
        <div class="menu-header">
          <span class="menu-title">Действия</span>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="menu-items">
          <button
            v-if="canPin"
            class="menu-item"
            @click="handlePin"
            :disabled="loading"
          >
            <span class="item-icon">
              <SakuraIcon v-if="message.is_pinned" name="pin" />
              <SakuraIcon v-else name="map-pin" />
            </span>
            <span class="item-text">{{
              message.is_pinned ? "Открепить" : "Закрепить"
            }}</span>
          </button>


          <button class="menu-item" @click="handleReply" :disabled="loading">
            <span class="item-icon"><SakuraIcon name="reply"/></span>
            <span class="item-text">Ответить</span>
          </button>

          <button
            v-if="message.sender_id === currentUserId"
            class="menu-item"
            @click="handleEdit"
            :disabled="loading"
          >
            <span class="item-icon"> <SakuraIcon name="edit" /> </span>
            <span class="item-text">Редактировать</span>
          </button>

          <button
            v-if="message.sender_id === currentUserId"
            class="menu-item delete"
            @click="handleDelete"
            :disabled="loading"
          >
            <span class="item-icon"> <SakuraIcon name="trash" /> </span>
            <span class="item-text">Удалить</span>
          </button>

          <button class="menu-item" @click="handleCopy" :disabled="loading">
            <span class="item-icon"> <SakuraIcon name="clipboard" /> </span>
            <span class="item-text">Копировать текст</span>
          </button>

          <button class="menu-item" @click="handleReport" :disabled="loading">
            <span class="item-icon"><SakuraIcon name="warning" />️</span>
            <span class="item-text">Пожаловаться</span>
          </button>
        </div>
      </div>
    </Transition>

    <ForwardMessageModal
      :is-open="showForwardModal"
      :message="message as any"
      :available-chats="availableChats as any"
      @close="showForwardModal = false"
      @forwarded="handleForwarded"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { useAuthStore } from "@/stores/auth";
import type { Message, Chat } from "@/types/chat";
import ForwardMessageModal from "../modal/chats/ForwardMessageModal.vue";

interface Props {
  message: Message;
  availableChats: Chat[];
  canPin?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  canPin: false,
});

const emit = defineEmits<{
  (e: "reply", message: Record<string, unknown>): void;
  (e: "edit", message: Record<string, unknown>): void;
  (e: "delete", messageId: number): void;
  (e: "pinned", message: Record<string, unknown>): void;
  (e: "unpinned", messageId: number): void;
  (e: "forwarded", data: Record<string, unknown>): void;
}>();

const chatExtrasStore = useChatExtrasStore();
const authStore = useAuthStore();

const showNotification = (message: string, type: "success" | "error") => {
  console.log(`[${type}] ${message}`);
};

const showModal = (type: string, data?: Record<string, unknown>) => {
  console.log(`Modal: ${type}`, data);
};

const isOpen = ref(false);
const loading = ref(false);
const showForwardModal = ref(false);

const currentUserId = computed(() => authStore.user?.id || 0);

const toggleMenu = () => {
  isOpen.value = !isOpen.value;
};

const close = () => {
  isOpen.value = false;
};

const handlePin = async () => {
  loading.value = true;
  try {
    if (props.message.is_pinned) {
      await chatExtrasStore.unpinMessage(props.message.id);
      emit("unpinned", props.message.id);
      showNotification("Сообщение откреплено", "success");
    } else {
      const result = await chatExtrasStore.pinMessage(props.message.id);
      emit("pinned", result);
      showNotification("Сообщение закреплено", "success");
    }
  } catch (error) {
    console.error("Error pinning message:", error);
    showNotification("Ошибка при закреплении сообщения", "error");
  } finally {
    loading.value = false;
    close();
  }
};

const handleForwarded = (data: unknown) => {
  emit("forwarded", data as Record<string, unknown>);
  showNotification("Сообщение переслано", "success");
};

const handleReply = () => {
  emit("reply", props.message);
  close();
};

const handleEdit = () => {
  emit("edit", props.message);
  close();
};

const handleDelete = () => {
  showModal("confirm", {
    title: "Удалить сообщение?",
    message: "Это действие нельзя отменить.",
    onConfirm: async () => {
      loading.value = true;
      try {
        emit("delete", props.message.id);
        showNotification("Сообщение удалено", "success");
      } catch (error) {
        console.error("Error deleting message:", error);
        showNotification("Ошибка при удалении сообщения", "error");
      } finally {
        loading.value = false;
      }
    },
  });
  close();
};

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(props.message.text || "");
    showNotification("Текст скопирован", "success");
  } catch (error) {
    console.error("Error copying text:", error);
    showNotification("Ошибка при копировании", "error");
  }
  close();
};

const handleReport = () => {
  showModal("report", {
    type: "message",
    id: props.message.id,
  });
  close();
};

const handleDocumentClick = () => {
  isOpen.value = false;
};

onMounted(() => {
  document.addEventListener("click", handleDocumentClick);
});

onUnmounted(() => {
  document.removeEventListener("click", handleDocumentClick);
});
</script>

<style scoped>
.message-actions {
  position: relative;
}

.actions-trigger {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--surface-1);
  border: 1px solid var(--border-strong);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.actions-trigger:hover {
  background: var(--surface-4);
  border-color: var(--accent);
}

.trigger-icon {
  font-size: 1.25rem;
  color: var(--text-secondary);
}

.actions-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  z-index: 100;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--border-strong);
}

.menu-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1.25rem;
  line-height: 1;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: var(--text-primary);
}

.menu-items {
  display: flex;
  flex-direction: column;
  padding: 0.5rem;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  background: none;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
  text-align: left;
  width: 100%;
}

.menu-item:hover:not(:disabled) {
  background: var(--surface-4);
}

.menu-item:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.menu-item.delete {
  color: #f44336;
}

.menu-item.delete:hover {
  background: rgba(244, 67, 54, 0.1);
}

.item-icon {
  font-size: 1.125rem;
}

.item-text {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.menu-item.delete .item-text {
  color: #f44336;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
