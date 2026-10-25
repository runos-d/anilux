<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="report-modal" @click.stop>
      <div class="modal-header">
        <h2>Пожаловаться</h2>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

      <div class="modal-body">
        <p class="description">Выберите причину жалобы:</p>

        <div class="reason-options">
          <label
            v-for="reason in reasons"
            :key="reason.id"
            class="reason-option"
            :class="{ selected: selectedReason === reason.id }"
          >
            <input type="radio" :value="reason.id" v-model="selectedReason" />
            <span class="reason-icon">{{ reason.icon }}</span>
            <span class="reason-label">{{ reason.label }}</span>
          </label>
        </div>

        <div class="comment-section">
          <label>Комментарий (опционально):</label>
          <textarea
            v-model="comment"
            placeholder="Дополнительные пояснения..."
            maxlength="500"
          ></textarea>
          <span class="char-count">{{ comment.length }}/500</span>
        </div>
        <p v-if="submitError" class="submit-error" role="alert">{{ submitError }}</p>
      </div>

      <div class="modal-footer">
        <button class="btn-cancel" @click="$emit('close')">Отмена</button>
        <button
          class="btn-submit"
          :disabled="!selectedReason || submitting"
          @click="submitReport"
        >
          {{ submitting ? "Отправка..." : "Отправить жалобу" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import apiClient from "@/api/client";
import { useToast } from "@/composables/useToast";
import { useAuthStore } from "@/stores/auth";
import { useModalStore } from "@/stores/modal";

const props = defineProps<{
  contentType: "post" | "comment" | "user";
  contentId: string | number | undefined;
}>();

const emit = defineEmits<{
  close: [];
  submitted: [];
}>();

const reasons = [
  { id: "spam", icon: "📢", label: "Спам" },
  { id: "copyright", icon: "©️", label: "Нарушение авторских прав" },
  { id: "harassment", icon: "😠", label: "Оскорбления / травля" },
  { id: "inappropriate", icon: "🔞", label: "Неприемлемый контент (18+)" },
  { id: "other", icon: "❓", label: "Другое" },
];

const selectedReason = ref("");
const comment = ref("");
const submitting = ref(false);
const submitError = ref("");
const toast = useToast();
const authStore = useAuthStore();
const modalStore = useModalStore();

const submitReport = async () => {
  if (!selectedReason.value || !props.contentId) return;
  if (!authStore.isAuthenticated) {
    modalStore.openAuthModal();
    emit("close");
    return;
  }

  submitting.value = true;
  submitError.value = "";

  try {
    const payload = {
      content_type: props.contentType,
      content_id: props.contentId,
      reason: selectedReason.value,
      comment: comment.value,
    };
    const { data } = await apiClient.post("/social/reports/", payload);

    toast.success(data?.message || "Жалоба отправлена. Мы сообщим о результате рассмотрения.", {
      title: "Спасибо за обращение",
      duration: 5000,
    });
    emit("submitted");
    emit("close");
  } catch (error: unknown) {
    console.error("Error submitting report:", error);
    const response = (error as {
      response?: { status?: number; data?: { error?: string; detail?: string; message?: string } };
    })?.response;
    if (response?.status === 401 || response?.status === 403) {
      modalStore.openAuthModal();
      emit("close");
      return;
    }
    submitError.value = response?.data?.error
      || response?.data?.detail
      || response?.data?.message
      || "Не удалось отправить жалобу. Проверьте подключение и попробуйте ещё раз.";
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.report-modal {
  background: #111;
  border-radius: 16px;
  width: 100%;
  max-width: 450px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #1f1f1f;
}

.modal-header h2 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 1.25rem;
  cursor: pointer;
}

.modal-body {
  padding: 1.5rem;
}

.description {
  color: #888;
  margin-bottom: 1rem;
}

.reason-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.reason-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: #1a1a1a;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.reason-option:hover {
  background: #252525;
}

.reason-option.selected {
  background: #252525;
  border: 1px solid #667eea;
}

.reason-option input {
  display: none;
}

.reason-icon {
  font-size: 1.25rem;
}

.reason-label {
  color: #ddd;
}

.comment-section {
  margin-top: 1.5rem;
}

.comment-section label {
  display: block;
  color: #888;
  margin-bottom: 0.5rem;
}

.comment-section textarea {
  width: 100%;
  min-height: 80px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 0.75rem;
  color: #ddd;
  resize: vertical;
}

.comment-section textarea:focus {
  outline: none;
  border-color: #667eea;
}

.char-count {
  display: block;
  text-align: right;
  color: #555;
  font-size: 0.8rem;
  margin-top: 0.5rem;
}

.submit-error {
  margin: 1rem 0 0;
  padding: 0.75rem 1rem;
  border: 1px solid color-mix(in srgb, var(--danger, #ef4444) 45%, transparent);
  border-radius: 8px;
  background: color-mix(in srgb, var(--danger, #ef4444) 12%, transparent);
  color: var(--danger, #ef4444);
  font-size: 0.875rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #1f1f1f;
}

.btn-cancel {
  background: #1a1a1a;
  color: #888;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
}

.btn-submit {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-submit:hover:not(:disabled) {
  background: #dc2626;
}
</style>
