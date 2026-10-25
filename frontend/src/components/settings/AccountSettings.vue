<template>
  <div class="account-settings">
    <transition name="toast">
      <div v-if="toast.visible" :class="['toast', toast.type]">
        {{ toast.message }}
      </div>
    </transition>

    <div class="settings-group">
      <h3><SakuraIcon name="image" /> Баннер профиля</h3>
      <div
        class="banner-preview"
        :class="{ 'has-cover': form.cover_image_url }"
        :style="bannerPreviewStyle"
      >
        <div v-if="!form.cover_image_url" class="banner-placeholder">
          <SakuraIcon name="image" />
          <span>Баннер не установлен</span>
        </div>
        <div class="banner-actions">
          <button class="btn-primary" @click="pickCoverFile" :disabled="saving.cover">
            <SakuraIcon name="upload" />
            {{ form.cover_image_url ? "Изменить" : "Загрузить" }}
          </button>
          <button
            v-if="form.cover_image_url"
            class="btn-danger"
            @click="removeCover"
            :disabled="saving.cover"
          >
            <SakuraIcon name="trash" /> Удалить
          </button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="camera" /> Аватар</h3>
      <div class="avatar-row">
        <div class="avatar-preview">
          <img v-if="form.avatar_url" :src="form.avatar_url" alt="Аватар" />
          <div v-else class="avatar-placeholder">{{ userInitials }}</div>
        </div>
        <div class="avatar-actions">
          <button class="btn-primary" @click="pickAvatarFile" :disabled="saving.avatar">
            <span v-if="saving.avatar">Загрузка...</span>
            <span v-else><SakuraIcon name="upload" /> Загрузить фото</span>
          </button>
          <button
            v-if="form.avatar_url"
            class="btn-danger"
            @click="removeAvatar"
            :disabled="saving.avatar"
          >
            <SakuraIcon name="trash" /> Удалить
          </button>
        </div>
        <p class="hint">JPEG / PNG / WebP, до 5 МБ</p>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="user" /> Имя</h3>
      <div class="field">
        <label>Отображаемое имя</label>
        <input
          v-model="form.display_name"
          type="text"
          placeholder="Твоё имя"
          class="input"
          :class="{ error: errors.display_name }"
          maxlength="50"
          @input="clearError('display_name')"
        />
        <span v-if="errors.display_name" class="error-msg">{{ errors.display_name }}</span>
      </div>
      <div class="field">
        <label>Никнейм</label>
        <input
          v-model="form.nickname"
          type="text"
          placeholder="username"
          class="input"
          :class="{ error: errors.nickname }"
          maxlength="32"
          @input="clearError('nickname')"
        />
        <span v-if="errors.nickname" class="error-msg">{{ errors.nickname }}</span>
      </div>
    </div>

    <div class="settings-group">
      <div class="bio-header">
        <h3><SakuraIcon name="file-text" /> О себе</h3>
        <button
          type="button"
          class="bio-mode-toggle"
          :class="{ active: bioPreviewMode }"
          @click="bioPreviewMode = !bioPreviewMode"
        >
          <svg v-if="!bioPreviewMode" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" />
            <circle cx="12" cy="12" r="3" />
          </svg>
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          <span>{{ bioPreviewMode ? "Редактировать" : "Превью" }}</span>
        </button>
      </div>

      <template v-if="bioPreviewMode">
        <div class="bio-preview-wrap">
          <div
            v-if="form.bio && form.bio.trim()"
            class="bio-preview bio--md"
            v-html="previewBio"
          ></div>
          <p v-else class="bio-preview bio-preview--empty">
            Пользователь пока ничего не написал о себе
          </p>
        </div>
      </template>

      <template v-else>
        <textarea
          v-model="form.bio"
          class="textarea"
          rows="6"
          maxlength="500"
          placeholder="Расскажи о себе..."
        ></textarea>
        <div class="char-count">{{ form.bio?.length || 0 }} / 500</div>
        <p class="bio-hint">
          Поддерживается Markdown: <code>**жирный**</code>, <code>*курсив*</code>,
          <code>[ссылка](url)</code>, <code>- список</code>, <code>&gt; цитата</code>.
        </p>
      </template>
    </div>

    <div class="actions">
      <button
        class="btn-save"
        @click="saveProfile"
        :disabled="!hasChanges || saving.profile || !isValid"
      >
        <span v-if="saving.profile"><SakuraIcon name="hourglass" /> Сохранение...</span>
        <span v-else><SakuraIcon name="save" /> Сохранить изменения</span>
      </button>
      <button class="btn-reset" @click="resetForm" :disabled="!hasChanges">
        <SakuraIcon name="reply" :size="16" /> Отменить
      </button>
    </div>

    <input
      ref="avatarFileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden-file-input"
      @change="onAvatarFilePicked"
    />
    <input
      ref="coverFileInput"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      class="hidden-file-input"
      @change="onCoverFilePicked"
    />

    <ImageCropEditor
      v-model:open="avatarEditorOpen"
      shape="circle"
      title="Изменить аватар"
      :initial-src="avatarInitialSrc"
      :initial-file="avatarPickedFile ?? undefined"
      @crop="handleAvatarCrop"
    />

    <ImageCropEditor
      v-model:open="coverEditorOpen"
      shape="rect"
      title="Изменить баннер"
      :initial-src="coverInitialSrc"
      :initial-file="coverPickedFile ?? undefined"
      :initial-x="form.cover_position_x ?? 50"
      :initial-y="form.cover_position_y ?? 50"
      hide-preview
      @crop="handleCoverCrop"
    />
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import apiClient from "@/api/client";
import { useAuthStore } from "@/stores/auth";
import { useSafeMarkdown } from "@/composables/useSafeMarkdown";
import ImageCropEditor from "@/components/modal/ImageCropEditor.vue";

interface SocialLink {
  name: string;
  url: string;
}

interface ProfileForm {
  avatar_url: string;
  cover_image_url: string;
  cover_position_x: number;
  cover_position_y: number;
  display_name: string;
  nickname: string;
  bio: string;
  birth_date: string;
  social_links: SocialLink[];
  status: string;
}

interface UserData {
  avatar_url?: string;
  avatar?: string;
  display_name?: string;
  nickname?: string;
  bio?: string;
  birth_date?: string;
  social_links?: SocialLink[];
  status?: string;
  cover_image_url?: string;
  cover_position_x?: number;
  cover_position_y?: number;
}

const authStore = useAuthStore();

const form = ref<ProfileForm>({
  avatar_url: "",
  cover_image_url: "",
  cover_position_x: 50,
  cover_position_y: 50,
  display_name: "",
  nickname: "",
  bio: "",
  birth_date: "",
  social_links: [],
  status: "online",
});

const original = ref<string>("");
const errors = ref<Record<string, string>>({});
const saving = ref({ profile: false, avatar: false, cover: false });
const toast = ref({ visible: false, message: "", type: "success" });

const bioPreviewMode = ref(false);

const avatarEditorOpen = ref(false);
const coverEditorOpen = ref(false);

const avatarFileInput = ref<HTMLInputElement | null>(null);
const coverFileInput = ref<HTMLInputElement | null>(null);

const avatarInitialSrc = ref<string | undefined>(undefined);
const coverInitialSrc = ref<string | undefined>(undefined);
const avatarPickedFile = ref<File | null>(null);
const coverPickedFile = ref<File | null>(null);

const hasChanges = computed(() => JSON.stringify(form.value) !== original.value);
const isValid = computed(() => Object.keys(errors.value).length === 0);

const userInitials = computed(() => {
  const name = form.value.display_name || form.value.nickname || "";
  return name.slice(0, 2).toUpperCase() || "?";
});

const bannerPreviewStyle = computed(() => {
  if (form.value.cover_image_url) {
    return {
      backgroundImage: `url(${form.value.cover_image_url})`,
      backgroundSize: "cover",
      backgroundPosition: `${form.value.cover_position_x ?? 50}% ${form.value.cover_position_y ?? 50}%`,
    };
  }
  return {};
});

const previewBio = useSafeMarkdown(
  computed(() => form.value.bio || ""),
);

const loadProfile = async () => {
  try {
    const { data } = await apiClient.get("/users/me/");
    applyToForm(data);
  } catch {
    showToast("Не удалось загрузить профиль", "error");
  }
};

const applyToForm = (data: UserData) => {
  form.value = {
    avatar_url: data.avatar_url || data.avatar || "",
    cover_image_url: data.cover_image_url || "",
    cover_position_x: data.cover_position_x ?? 50,
    cover_position_y: data.cover_position_y ?? 50,
    display_name: data.display_name || "",
    nickname: data.nickname || "",
    bio: data.bio || "",
    birth_date: data.birth_date || "",
    social_links: Array.isArray(data.social_links) ? data.social_links : [],
    status: data.status || "online",
  };
  original.value = JSON.stringify(form.value);
};

const clearError = (field: string) => {
  delete errors.value[field];
};

const pickAvatarFile = () => {
  avatarFileInput.value?.click();
};

const pickCoverFile = () => {
  coverFileInput.value?.click();
};

const revokeIfBlob = (url: string | undefined) => {
  if (url && url.startsWith("blob:")) {
    URL.revokeObjectURL(url);
  }
};

const onAvatarFilePicked = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showToast("Пожалуйста, выберите изображение", "error");
    input.value = "";
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("Размер файла не должен превышать 10 МБ", "error");
    input.value = "";
    return;
  }
  revokeIfBlob(avatarInitialSrc.value);
  avatarInitialSrc.value = URL.createObjectURL(file);
  avatarPickedFile.value = file;
  avatarEditorOpen.value = true;
  input.value = "";
};

const onCoverFilePicked = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith("image/")) {
    showToast("Пожалуйста, выберите изображение", "error");
    input.value = "";
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    showToast("Размер файла не должен превышать 10 МБ", "error");
    input.value = "";
    return;
  }
  revokeIfBlob(coverInitialSrc.value);
  coverInitialSrc.value = URL.createObjectURL(file);
  coverPickedFile.value = file;
  coverEditorOpen.value = true;
  input.value = "";
};

const handleAvatarCrop = async (payload: { file?: File; blob?: Blob; x: number; y: number }) => {
  const file =
    payload.file ??
    (payload.blob
      ? new File([payload.blob], "avatar.jpg", { type: "image/jpeg" })
      : undefined);
  if (!file) {
    showToast("Файл не выбран", "error");
    return;
  }
  saving.value.avatar = true;
  try {
    const fd = new FormData();
    fd.append("avatar", file);
    fd.append("avatar_position_x", String(payload.x));
    fd.append("avatar_position_y", String(payload.y));
    const { data } = await apiClient.post("/users/avatar/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    form.value.avatar_url = data.avatar_url || data.avatar || "";
    original.value = JSON.stringify(form.value);
    await authStore.fetchUser();
    showToast("Аватар обновлён");
  } catch {
    showToast("Ошибка загрузки аватара", "error");
  } finally {
    saving.value.avatar = false;
    avatarEditorOpen.value = false;
    revokeIfBlob(avatarInitialSrc.value);
    avatarInitialSrc.value = undefined;
    avatarPickedFile.value = null;
  }
};

const removeAvatar = async () => {
  saving.value.avatar = true;
  try {
    await apiClient.delete("/users/avatar/");
    form.value.avatar_url = "";
    original.value = JSON.stringify(form.value);
    await authStore.fetchUser();
    showToast("Аватар удалён");
  } catch {
    showToast("Ошибка удаления аватара", "error");
  } finally {
    saving.value.avatar = false;
  }
};

const handleCoverCrop = async (payload: { file?: File; blob?: Blob; x: number; y: number }) => {
  const file =
    payload.file ??
    (payload.blob
      ? new File([payload.blob], "cover.jpg", { type: "image/jpeg" })
      : undefined);
  saving.value.cover = true;
  try {
    const fd = new FormData();
    if (file) {
      fd.append("cover_image", file);
    }
    fd.append("cover_position_x", String(payload.x));
    fd.append("cover_position_y", String(payload.y));
    await apiClient.patch("/users/profile/update/", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await loadProfile();
    showToast("Баннер обновлён");
  } catch {
    showToast("Ошибка загрузки баннера", "error");
  } finally {
    saving.value.cover = false;
    coverEditorOpen.value = false;
    revokeIfBlob(coverInitialSrc.value);
    coverInitialSrc.value = undefined;
    coverPickedFile.value = null;
  }
};

const removeCover = async () => {
  saving.value.cover = true;
  try {
    const { data } = await apiClient.patch("/users/profile/update/", {
      cover_image: null,
    });
    form.value.cover_image_url = data.cover_image_url || "";
    form.value.cover_position_x = data.cover_position_x ?? 50;
    form.value.cover_position_y = data.cover_position_y ?? 50;
    original.value = JSON.stringify(form.value);
    await authStore.fetchUser();
    showToast("Баннер удалён");
  } catch {
    showToast("Ошибка удаления баннера", "error");
  } finally {
    saving.value.cover = false;
  }
};

const saveProfile = async () => {
  if (!hasChanges.value || saving.value.profile) return;

  errors.value = {};
  const nick = form.value.nickname;
  if (nick && nick.length < 3) {
    errors.value.nickname = "Минимум 3 символа";
    return;
  }
  if (nick && !/^[a-zA-Z0-9_-]+$/.test(nick)) {
    errors.value.nickname = "Только латиница, цифры, _ и -";
    return;
  }
  const name = form.value.display_name;
  if (name && name.length > 50) {
    errors.value.display_name = "Максимум 50 символов";
    return;
  }

  saving.value.profile = true;
  try {
    const payload = {
      display_name: form.value.display_name,
      nickname: form.value.nickname,
      bio: form.value.bio,
      birth_date: form.value.birth_date || null,
      social_links: form.value.social_links,
      status: form.value.status,
    };
    const { data } = await apiClient.put("/users/me/", payload);
    applyToForm(data);
    await authStore.fetchUser();
    showToast("Профиль сохранён");
  } catch (err: unknown) {
    const detail = (err as { response?: { data?: unknown } })?.response?.data;
    if (detail && typeof detail === "object") {
      for (const [k, v] of Object.entries(detail)) {
        errors.value[k] = Array.isArray(v) ? v[0] : String(v);
      }
      showToast("Проверьте поля формы", "error");
    } else {
      showToast("Ошибка сохранения профиля", "error");
    }
  } finally {
    saving.value.profile = false;
  }
};

const resetForm = () => {
  form.value = JSON.parse(original.value);
  errors.value = {};
};

let toastTimer: ReturnType<typeof setTimeout> | null = null;
const showToast = (message: string, type: "success" | "error" = "success") => {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { visible: true, message, type };
  toastTimer = setTimeout(() => (toast.value.visible = false), 3000);
};

onMounted(loadProfile);

onBeforeUnmount(() => {
  revokeIfBlob(avatarInitialSrc.value);
  revokeIfBlob(coverInitialSrc.value);
  if (toastTimer) clearTimeout(toastTimer);
});
</script>

<style scoped>
.account-settings {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.hidden-file-input {
  display: none;
}

.toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 9999;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  pointer-events: none;
}
.toast.success {
  background: #22c55e;
  color: #fff;
}
.toast.error {
  background: #ef4444;
  color: #fff;
}
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.settings-group {
  padding: 22px 24px;
  border-bottom: 1px solid var(--border-default);
}
.settings-group:last-of-type {
  border-bottom: none;
}
.settings-group > h3 {
  margin: 0 0 16px;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.banner-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 7;
  border-radius: 15px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  overflow: hidden;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.banner-preview.has-cover {
  border-color: var(--border-strong);
}
.banner-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.banner-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-tertiary);
  font-size: 14px;
}
.banner-actions {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(0, 0, 0, 0.45);
  opacity: 0;
  transition: opacity 0.2s;
}
.banner-preview:hover .banner-actions {
  opacity: 1;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}
.avatar-preview {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--surface-3);
  border: 2px solid var(--border-default);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-secondary);
}
.avatar-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}
.field:last-child {
  margin-bottom: 0;
}
.field label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.input {
  padding: 9px 13px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 14px;
  transition: border-color 0.15s;
}
.input:focus {
  outline: none;
  border-color: var(--accent);
}
.input.error {
  border-color: #ef4444;
}

.textarea {
  padding: 9px 13px;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  background: var(--surface-3);
  color: var(--text-primary);
  font-size: 14px;
  resize: vertical;
  min-height: 148px;
  width: 100%;
  box-sizing: border-box;
  font-family: inherit;
  line-height: 1.55;
}
.textarea:focus {
  outline: none;
  border-color: var(--accent);
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 6px;
}
.error-msg {
  font-size: 12px;
  color: #ef4444;
}
.hint {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
  width: 100%;
}

/* ── Bio header with toggle ── */
.bio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}
.bio-header > h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bio-mode-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  border-radius: 9px;
  border: 1px solid var(--border-default);
  background: var(--surface-4);
  color: var(--text-secondary);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.bio-mode-toggle:hover {
  background: var(--surface-5);
  border-color: var(--accent);
  color: var(--accent);
}
.bio-mode-toggle.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

/* ── Bio preview (in preview mode) ── */
.bio-preview-wrap {
  min-height: 148px;
}

.bio-preview {
  min-height: 148px;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--surface-2);
  border: 1px solid var(--border-subtle);
  border-left: 3px solid var(--accent);
  border-top-left-radius: 4px;
  border-bottom-left-radius: 4px;
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary);
  overflow-wrap: anywhere;
  word-break: break-word;
  box-sizing: border-box;
}

.bio-preview--empty {
  color: var(--text-tertiary);
  font-style: italic;
  background: transparent;
  border: 1px dashed var(--border-subtle);
  border-left: 1px dashed var(--border-subtle);
  border-top-left-radius: 12px;
  border-bottom-left-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 16px;
}

.bio-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.6;
}
.bio-hint code {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 11.5px;
  background: var(--surface-4);
  color: var(--text-secondary);
  padding: 1px 5px;
  border-radius: 4px;
}

/* Markdown inside preview */
.bio-preview.bio--md :deep(p) {
  margin: 0 0 8px;
}
.bio-preview.bio--md :deep(p:last-child) {
  margin-bottom: 0;
}
.bio-preview.bio--md :deep(strong) {
  color: var(--text-primary);
  font-weight: 600;
}
.bio-preview.bio--md :deep(em) {
  color: var(--text-primary);
  font-style: italic;
}
.bio-preview.bio--md :deep(a) {
  color: var(--accent);
  text-decoration: none;
  border-bottom: 1px solid color-mix(in srgb, var(--accent) 40%, transparent);
}
.bio-preview.bio--md :deep(a:hover) {
  color: var(--accent-hover);
  border-bottom-color: var(--accent-hover);
}
.bio-preview.bio--md :deep(code) {
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 0.9em;
  background: var(--surface-4);
  color: var(--text-primary);
  padding: 2px 6px;
  border-radius: 5px;
}
.bio-preview.bio--md :deep(pre) {
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 0.85em;
  line-height: 1.5;
  margin: 8px 0;
}
.bio-preview.bio--md :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: inherit;
}
.bio-preview.bio--md :deep(blockquote) {
  margin: 8px 0;
  padding: 6px 12px;
  border-left: 3px solid var(--accent);
  background: var(--surface-4);
  border-radius: 0 8px 8px 0;
  font-style: italic;
  color: var(--text-secondary);
}
.bio-preview.bio--md :deep(ul),
.bio-preview.bio--md :deep(ol) {
  margin: 6px 0;
  padding-left: 22px;
}
.bio-preview.bio--md :deep(li) {
  margin: 2px 0;
}
.bio-preview.bio--md :deep(h1),
.bio-preview.bio--md :deep(h2),
.bio-preview.bio--md :deep(h3),
.bio-preview.bio--md :deep(h4),
.bio-preview.bio--md :deep(h5),
.bio-preview.bio--md :deep(h6) {
  color: var(--text-primary);
  font-weight: 700;
  line-height: 1.3;
  margin: 10px 0 6px;
}
.bio-preview.bio--md :deep(h1) { font-size: 1.2em; }
.bio-preview.bio--md :deep(h2) { font-size: 1.12em; }
.bio-preview.bio--md :deep(h3) { font-size: 1.04em; }
.bio-preview.bio--md :deep(h4),
.bio-preview.bio--md :deep(h5),
.bio-preview.bio--md :deep(h6) { font-size: 1em; }

.bio-preview.bio--md :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 10px 0;
}

.bio-preview.bio--md :deep(del),
.bio-preview.bio--md :deep(s) {
  opacity: 0.6;
  text-decoration: line-through;
}

.btn-primary,
.btn-danger,
.btn-save,
.btn-reset {
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
  border: none;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-danger {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
  border: 1px solid #ef4444;
}
.btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.18);
}
.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.actions {
  padding: 20px 24px;
  display: flex;
  gap: 12px;
  border-top: 1px solid var(--border-default);
  flex-wrap: wrap;
}
.btn-save {
  background: var(--accent);
  color: #fff;
  padding: 10px 24px;
  font-size: 15px;
}
.btn-save:hover:not(:disabled) {
  background: var(--accent-hover);
}
.btn-save:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.btn-reset {
  background: var(--surface-4);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}
.btn-reset:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}
.btn-reset:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@media (max-width: 700px) {
  .settings-group {
    padding: 18px 16px;
  }
  .actions {
    padding: 16px;
  }
  .banner-preview {
    aspect-ratio: 16 / 9;
  }
  .avatar-row {
    gap: 14px;
  }
  .btn-save,
  .btn-reset {
    width: 100%;
    justify-content: center;
  }
  .bio-header {
    flex-wrap: wrap;
  }
  .bio-mode-toggle {
    margin-left: auto;
  }
}
</style>
