<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal-content new-chat-modal">
      <div class="modal-header">
        <h2 class="modal-title">Новый чат</h2>
        <button @click="handleClose" class="modal-close" type="button">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="chat-type-selector">
          <button
            @click="chatType = 'private'"
            :class="['type-button', { active: chatType === 'private' }]"
            type="button"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>Личный чат</span>
          </button>
          <button
            @click="chatType = 'group'"
            :class="['type-button', { active: chatType === 'group' }]"
            type="button"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M17 21v-2a4 4 0 0 0-3-5.66M15 11a4 4 0 0 0-8 0 4 4 0 0 0 8 0zM5 21v-2a4 4 0 0 1 4-4h4"
              />
            </svg>
            <span>Группа</span>
          </button>
        </div>

        <div v-if="chatType === 'private'" class="form-section">
          <div class="form-group">
            <label class="form-label required">Поиск пользователя</label>
            <div class="search-input-wrapper">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Введите имя пользователя..."
                class="form-input"
                @input="searchUsers"
              />
            </div>
            <div v-if="isSearching" class="loading-spinner"></div>
            <div v-if="searchResults.length > 0" class="search-results">
              <div
                v-for="user in searchResults"
                :key="user.id"
                @click="selectUser(user)"
                :class="[
                  'user-item',
                  { selected: selectedUser?.id === user.id },
                ]"
              >
                <div class="user-avatar">
                  <img
                    v-if="user.avatar"
                    :src="user.avatar"
                    :alt="user.username"
                  />
                  <span v-else class="avatar-placeholder">{{
                    user.username.charAt(0).toUpperCase()
                  }}</span>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ user.username }}</div>
                  <div v-if="user.display_name" class="user-display-name">
                    {{ user.display_name }}
                  </div>
                </div>
              </div>
            </div>
            <div
              v-if="!isSearching && searchQuery && searchResults.length === 0"
              class="no-results"
            >
              Пользователи не найдены
            </div>
          </div>
        </div>

        <div v-if="chatType === 'group'" class="form-section">
          <div class="form-group group-avatar-field">
            <label class="form-label">Аватар группы</label>
            <button class="group-avatar-picker" type="button" @click="avatarInput?.click()">
              <span class="group-avatar-preview">
                <img v-if="groupAvatarPreview" :src="groupAvatarPreview" alt="Аватар группы" />
                <SakuraIcon v-else name="camera" :size="24" />
              </span>
              <span class="group-avatar-copy">
                <strong>{{ groupAvatarFile ? "Изменить аватар" : "Выбрать аватар" }}</strong>
                <small>Изображение можно обрезать перед созданием группы</small>
              </span>
            </button>
            <input
              ref="avatarInput"
              class="hidden-input"
              type="file"
              accept="image/*,.jpg,.jpeg,.png,.webp"
              @change="onAvatarSelected"
            />
          </div>
          <div class="form-group">
            <label class="form-label required">Название группы</label>
            <input
              v-model="groupForm.name"
              type="text"
              placeholder="Название группы"
              class="form-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Описание</label>
            <textarea
              v-model="groupForm.description"
              placeholder="Описание группы"
              class="form-textarea"
              rows="3"
            ></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">Добавить участников</label>
            <div class="search-input-wrapper">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              <input
                v-model="memberSearchQuery"
                type="text"
                placeholder="Поиск пользователей..."
                class="form-input"
                @input="searchUsersForMember"
              />
            </div>
            <div v-if="memberSearchResults.length > 0" class="search-results">
              <div
                v-for="user in memberSearchResults"
                :key="user.id"
                @click="toggleMember(user)"
                :class="[
                  'user-item',
                  { selected: selectedMembers.some((m) => m.id === user.id) },
                ]"
              >
                <div class="user-avatar">
                  <img
                    v-if="user.avatar"
                    :src="user.avatar"
                    :alt="user.username"
                  />
                  <span v-else class="avatar-placeholder">{{
                    user.username.charAt(0).toUpperCase()
                  }}</span>
                </div>
                <div class="user-info">
                  <div class="user-name">{{ user.username }}</div>
                  <div v-if="user.display_name" class="user-display-name">
                    {{ user.display_name }}
                  </div>
                </div>
                <div class="user-check">
                  <svg
                    v-if="selectedMembers.some((m) => m.id === user.id)"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
              </div>
            </div>
            <div v-if="selectedMembers.length > 0" class="selected-members">
              <div class="selected-members-label">
                Выбрано участников: {{ selectedMembers.length }}
              </div>
              <div class="members-chips">
                <span
                  v-for="member in selectedMembers"
                  :key="member.id"
                  class="member-chip"
                >
                  {{ member.username }}
                  <button
                    @click="removeMember(member)"
                    type="button"
                    class="chip-remove"
                   aria-label="Удалить">
                    <SakuraIcon name="x" :size="16" />
                  </button>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleClose" class="btn btn-secondary" type="button">
          Отмена
        </button>
        <button
          @click="handleCreate"
          :disabled="!canSubmit || isSubmitting"
          class="btn btn-primary"
          type="button"
        >
          <svg
            v-if="isSubmitting"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            class="spin"
          >
            <circle cx="12" cy="12" r="10" />
            <path
              d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"
            />
          </svg>
          {{ isSubmitting ? "Создание..." : "Создать" }}
        </button>
      </div>
    </div>
    <ImageCropEditor
      v-model:open="cropOpen"
      shape="circle"
      title="Аватар группы"
      :initial-file="cropSourceFile"
      @crop="applyAvatarCrop"
    />
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import ImageCropEditor from "@/components/modal/ImageCropEditor.vue";
import { ref, computed, watch, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import apiClient from "@/api/client";
import type { User } from "@/types";

interface Props {
  show: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  close: [];
  created: [data: { chatId: number; chatType: "private" | "group" }];
  chatCreated: [];
}>();

const router = useRouter();

const chatType = ref<"private" | "group">("private");
const searchQuery = ref("");
const searchResults = ref<User[]>([]);
const selectedUser = ref<User | null>(null);
const isSearching = ref(false);
const isSubmitting = ref(false);

const memberSearchQuery = ref("");
const memberSearchResults = ref<User[]>([]);
const selectedMembers = ref<User[]>([]);
const avatarInput = ref<HTMLInputElement | null>(null);
const cropOpen = ref(false);
const cropSourceFile = ref<File | null>(null);
const groupAvatarFile = ref<File | null>(null);
const groupAvatarPreview = ref("");

const groupForm = ref({
  name: "",
  description: "",
});

const canSubmit = computed(() => {
  if (chatType.value === "private") {
    return selectedUser.value !== null;
  } else {
    return groupForm.value.name.trim().length > 0;
  }
});

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

const searchUsers = () => {
  clearTimeout(searchTimeout ?? undefined);
  if (searchQuery.value.length < 2) {
    searchResults.value = [];
    return;
  }

  isSearching.value = true;
  searchTimeout = setTimeout(async () => {
    try {
      const response = await apiClient.get(
        `/users/search/?search=${encodeURIComponent(searchQuery.value)}`,
      );
      searchResults.value = response.data.results || response.data || [];
    } catch (error) {
      console.error("Error searching users:", error);
      searchResults.value = [];
    } finally {
      isSearching.value = false;
    }
  }, 300);
};

const selectUser = (user: User) => {
  selectedUser.value = user;
  searchResults.value = [];
  searchQuery.value = user.username;
};

const searchUsersForMember = () => {
  clearTimeout(searchTimeout ?? undefined);
  if (memberSearchQuery.value.length < 2) {
    memberSearchResults.value = [];
    return;
  }

  searchTimeout = setTimeout(async () => {
    try {
      const response = await apiClient.get(
        `/users/search/?q=${encodeURIComponent(memberSearchQuery.value)}`,
      );
      const results = response.data.results || response.data || [];
      memberSearchResults.value = results.filter(
        (u: User) => !selectedMembers.value.some((m) => m.id === u.id),
      );
    } catch (error) {
      console.error("Error searching users:", error);
      memberSearchResults.value = [];
    }
  }, 300);
};

const toggleMember = (user: User) => {
  const index = selectedMembers.value.findIndex((m) => m.id === user.id);
  if (index > -1) {
    selectedMembers.value.splice(index, 1);
  } else {
    selectedMembers.value.push(user);
  }
  memberSearchResults.value = memberSearchResults.value.filter(
    (u) => u.id !== user.id,
  );
};

const removeMember = (user: User) => {
  selectedMembers.value = selectedMembers.value.filter((m) => m.id !== user.id);
};

const setAvatarPreview = (file: File) => {
  if (groupAvatarPreview.value.startsWith("blob:")) {
    URL.revokeObjectURL(groupAvatarPreview.value);
  }
  groupAvatarPreview.value = URL.createObjectURL(file);
};

const onAvatarSelected = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  if (!file) return;
  cropSourceFile.value = file;
  cropOpen.value = true;
};

const applyAvatarCrop = (result: { file?: File; blob?: Blob }) => {
  const file = result.file || (result.blob
    ? new File([result.blob], "group-avatar.webp", { type: result.blob.type || "image/webp" })
    : null);
  if (!file) return;
  groupAvatarFile.value = file;
  setAvatarPreview(file);
  cropOpen.value = false;
};

const handleCreate = async () => {
  if (!canSubmit.value) return;

  isSubmitting.value = true;

  try {
    if (chatType.value === "private") {
      const response = await apiClient.post("/social/private-chats/", {
        user2: selectedUser.value!.id,
      });
      const chatId = response.data.id;
      
      emit("created", { chatId, chatType: "private" });
      
      handleClose();
      
      emit("chatCreated");
      
      router.push({ path: `/chats/${chatId}`, query: { type: "private" } });
    } else {
      const payload = new FormData();
      payload.append("name", groupForm.value.name.trim());
      payload.append("description", groupForm.value.description.trim());
      selectedMembers.value.forEach((member) => payload.append("participants", String(member.id)));
      if (groupAvatarFile.value) payload.append("avatar", groupAvatarFile.value);
      const response = await apiClient.post("/social/group-chats/", payload);
      const chatId = response.data.id;
      
      emit("created", { chatId, chatType: "group" });
      
      handleClose();
      
      emit("chatCreated");
      
      router.push({ path: `/chats/${chatId}`, query: { type: "group" } });
    }
  } catch (error: unknown) {
    console.error("Error creating chat:", error);
  } finally {
    isSubmitting.value = false;
  }
};


const handleClose = () => {
  emit("close");
  resetForm();
};

const resetForm = () => {
  chatType.value = "private";
  searchQuery.value = "";
  searchResults.value = [];
  selectedUser.value = null;
  memberSearchQuery.value = "";
  memberSearchResults.value = [];
  selectedMembers.value = [];
  groupForm.value = {
    name: "",
    description: "",
  };
  cropOpen.value = false;
  cropSourceFile.value = null;
  groupAvatarFile.value = null;
  if (groupAvatarPreview.value.startsWith("blob:")) URL.revokeObjectURL(groupAvatarPreview.value);
  groupAvatarPreview.value = "";
  isSubmitting.value = false;
};

watch(
  () => props.show,
  (newShow) => {
    if (!newShow) {
      resetForm();
    }
  },
);

onBeforeUnmount(() => {
  if (groupAvatarPreview.value.startsWith("blob:")) URL.revokeObjectURL(groupAvatarPreview.value);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background-color: var(--surface-3);
  border-radius: 1rem;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm-modal);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
}

.modal-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.modal-close:hover {
  background-color: var(--surface-4);
  color: #ef4444;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.chat-type-selector {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.type-button {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  background-color: var(--surface-4);
  border: 2px solid var(--border-strong);
  border-radius: 0.75rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
}

.type-button:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}

.type-button.active {
  border-color: var(--accent);
  background-color: rgba(58, 134, 255, 0.1);
  color: var(--accent);
}

.type-button svg {
  width: 24px;
  height: 24px;
}

.type-button span {
  font-size: 0.875rem;
  font-weight: 500;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.group-avatar-picker {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.75rem;
  background: var(--surface-4);
  color: var(--text-primary);
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.group-avatar-picker:hover {
  border-color: var(--accent);
  background: color-mix(in srgb, var(--surface-4) 88%, var(--accent));
}

.group-avatar-preview {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  flex: 0 0 64px;
  overflow: hidden;
  border-radius: 50%;
  background: var(--surface-3);
  color: var(--accent);
}

.group-avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.group-avatar-copy {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  min-width: 0;
}

.group-avatar-copy small { color: var(--text-tertiary); line-height: 1.35; }
.hidden-input { display: none; }

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

.form-label.required::after {
  content: " *";
  color: #ef4444;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.search-input-wrapper svg {
  position: absolute;
  left: 0.75rem;
  color: var(--text-tertiary);
}

.form-input {
  width: 100%;
  padding: 0.75rem 0.75rem 0.75rem 2.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
  background-color: var(--surface-3);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
}

.form-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  font-size: 0.9375rem;
  color: var(--text-primary);
  background-color: var(--surface-3);
  outline: none;
  transition: all 0.2s var(--transition-smooth);
  font-family: inherit;
  resize: vertical;
}

.form-textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(58, 134, 255, 0.1);
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-strong);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.search-results {
  margin-top: 0.5rem;
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  overflow: hidden;
  max-height: 200px;
  overflow-y: auto;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s var(--transition-smooth);
}

.user-item:hover {
  background-color: var(--surface-4);
}

.user-item.selected {
  background-color: rgba(58, 134, 255, 0.1);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-display-name {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-check {
  color: var(--accent);
}

.no-results {
  padding: 1rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.selected-members {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background-color: var(--surface-4);
  border-radius: 0.5rem;
}

.selected-members-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
}

.members-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.member-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background-color: var(--accent);
  color: white;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}

.chip-remove {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 0;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.chip-remove:hover {
  opacity: 1;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-top: 1px solid var(--border-subtle);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 0.625rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s var(--transition-smooth);
  border: 1px solid;
}

.btn-primary {
  background-color: var(--accent);
  border-color: var(--accent);
  color: var(--text-primary);
}

.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(58, 134, 255, 0.3);
}

.btn-secondary {
  background-color: transparent;
  border-color: var(--border-strong);
  color: var(--text-secondary);
}

.btn-secondary:hover {
  background-color: var(--surface-4);
  border-color: var(--accent);
  color: var(--accent);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@media (max-width: 768px) {
  .modal-content {
    max-height: 95vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .btn {
    width: 100%;
  }
}
</style>
