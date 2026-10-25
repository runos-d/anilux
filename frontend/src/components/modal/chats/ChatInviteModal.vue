<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Приглашение в чат</h3>
          <button class="close-btn" @click="close" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
        </div>

        <div class="modal-body">
          <div v-if="invite" class="invite-info">
            <div class="invite-link-container">
              <label class="section-title">Ссылка-приглашение</label>
              <div class="invite-link">
                <input
                  :value="inviteLink"
                  readonly
                  class="invite-input"
                  ref="inviteLinkInput"
                />
                <button class="copy-btn" @click="copyLink" :disabled="copying">
                  {{ copying ? "Скопировано!" : "Копировать" }}
                </button>
              </div>
            </div>
          </div>

          <div v-else class="create-invite">
            <div class="loading-spinner"></div>
            <p>Генерация ссылки...</p>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref, computed, watch, nextTick } from "vue"
import { useChatExtrasStore } from "@/stores/chatExtras"
import type { ChatInviteLink } from "@/api/chats"
interface Props {
  isOpen: boolean;
  chatId: number;
  existingInvite?: ChatInviteLink | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "close"): void;
  (e: "created", invite: ChatInviteLink): void;
}>();

const chatExtrasStore = useChatExtrasStore();

const loading = ref(false);
const copying = ref(false);
const invite = ref<ChatInviteLink | null>(props.existingInvite || null);
const inviteLinkInput = ref<HTMLInputElement>();

const inviteLink = computed(() => {
  const token = invite.value?.invite_link;
  if (!token) return "";
  return `${window.location.origin}/chats/invite/${token}`;
});

watch(
  () => props.existingInvite,
  (newVal) => {
    invite.value = newVal || null;
  },
);

watch(
  () => props.isOpen,
  async (isOpen) => {
    if (isOpen && !invite.value) {
      await createInvite();
    }
  },
);

const createInvite = async () => {
  loading.value = true;
  try {
    const expiresAt = new Date(
      Date.now() + 24 * 60 * 60 * 1000,
    ).toISOString();

    const newInvite = await chatExtrasStore.createInvite({
      chat: props.chatId,
      name: "Приглашение",
      expires_at: expiresAt,
    });

    invite.value = newInvite;
    emit("created", newInvite);
  } catch (error) {
    console.error("Error creating invite:", error);
  } finally {
    loading.value = false;
  }
};

const copyLink = async () => {
  if (!inviteLinkInput.value) return;
  copying.value = true;
  try {
    await navigator.clipboard.writeText(inviteLink.value);
    setTimeout(() => {
      copying.value = false;
    }, 2000);
  } catch (error) {
    console.error("Error copying link:", error);
    copying.value = false;
  }
};

const close = () => {
  emit("close");
  invite.value = null;
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--surface-3);
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: var(--text-tertiary);
  cursor: pointer;
  width: 32px;
  height: 32px;
  min-width: 32px;
  min-height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.close-btn:hover {
  background: var(--surface-4);
}

.modal-body {
  padding: 1.5rem;
}

.invite-info {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.invite-link-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.section-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.invite-link {
  display: flex;
  gap: 0.5rem;
}

.invite-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  font-size: 0.875rem;
  background: var(--surface-1);
  color: var(--text-primary);
}

.copy-btn {
  padding: 0.75rem 1rem;
  background: var(--accent);
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: white;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.copy-btn:hover {
  background: var(--accent-hover);
}

.copy-btn:disabled {
  background: var(--text-disabled);
  cursor: not-allowed;
}

.create-invite {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 2rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-strong);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>