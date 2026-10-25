<template>
  <section class="settings-section">
    <div class="section-header">
      <h2><SakuraIcon name="user" /> Группа</h2>
    </div>

    <div class="field-group">
      <label for="chat-group-name">Название</label>
      <input id="chat-group-name" :value="name" @input="$emit('update:name', ($event.target as HTMLInputElement).value)" maxlength="255" class="text-field" />
      <label for="chat-group-description">Описание</label>
      <textarea id="chat-group-description" :value="description" @input="$emit('update:description', ($event.target as HTMLTextAreaElement).value)" rows="3" class="text-field" />
      <button @click="$emit('save-info')" class="btn-primary" :disabled="saving || !name.trim()">Сохранить название и описание</button>
    </div>
    <div class="avatar-preview-section">
      <div class="avatar-preview-large" @click="fileInput?.click()">
        <img v-if="avatarPreview || chatAvatar" :src="avatarPreview || chatAvatar" alt="Avatar" />
        <div v-else class="avatar-placeholder-large">
          {{ (chatName || "?")[0] }}
        </div>
        <div class="avatar-overlay">
          <span> <SakuraIcon name="camera" /> </span>
        </div>
      </div>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        @change="onFileChange"
        style="display: none"
      />
    </div>

    <div class="field-group">
      <p class="field-hint">Нажмите на аватар, чтобы загрузить новое изображение</p>
      <p class="field-hint">JPG, PNG, WEBP -максимум 5MB</p>
    </div>

    <div v-if="avatarPreview" class="section-actions">
      <button @click="$emit('clear')" class="btn-secondary" type="button">
        Отменить
      </button>
      <button @click="$emit('save')" class="btn-primary" :disabled="saving">
        <span v-if="saving" class="btn-spinner"></span>
        <template v-if="saving">Сохранение...</template>
        <template v-else>
          <SakuraIcon name="save" />
          Сохранить аватар
        </template>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";

defineProps<{
  chatName?: string
  chatAvatar?: string
  avatarPreview: string | null
  saving: boolean
  name: string
  description: string
}>()

const emit = defineEmits<{
  save: []
  clear: []
  "file-change": [file: File]
  'update:name': [value: string]
  'update:description': [value: string]
  'save-info': []
}>()

const fileInput = ref<HTMLInputElement | null>(null)

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) emit("file-change", file)
}
</script>

<style scoped>
.field-group { display: grid; gap: 12px; }
.text-field { width: 100%; padding: 10px 12px; color: var(--text-primary); background: var(--surface-2); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); }
.settings-section {
  padding: var(--space-6);
  animation: slideUp var(--duration-slow) var(--ease-out) both;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}
.section-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.avatar-preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-6) var(--space-4);
  margin-bottom: var(--space-4);
}
.avatar-preview-large {
  position: relative;
  width: 128px;
  height: 128px;
  border-radius: var(--radius-full);
  overflow: hidden;
  cursor: pointer;
  border: 3px solid var(--border-strong);
  box-shadow: var(--shadow-petal);
  transition: all var(--duration-base) var(--ease-petal);
}
.avatar-preview-large:hover {
  border-color: var(--accent);
  transform: scale(1.03);
  box-shadow: var(--shadow-glow);
}
.avatar-preview-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-placeholder-large {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--text-on-accent);
}
.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-petal);
}
.avatar-preview-large:hover .avatar-overlay {
  opacity: 1;
}
.avatar-overlay span {
  font-size: var(--text-3xl);
}
.field-group {
  margin-bottom: var(--space-4);
}
.field-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-2);
  text-align: center;
  line-height: 1.5;
}
.section-actions {
  margin-top: var(--space-5);
  display: flex;
  gap: var(--space-3);
  justify-content: center;
}
.btn-primary {
  padding: var(--space-2) var(--space-6);
  background: var(--accent);
  border: none;
  color: var(--text-on-accent);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-petal-sm);
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-petal);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn-secondary {
  padding: var(--space-2) var(--space-5);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-out);
}
.btn-secondary:hover {
  border-color: var(--accent);
  background: var(--surface-5);
  transform: translateY(-1px);
}
.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: var(--radius-full);
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .settings-section {
    padding: var(--space-4);
  }
  .avatar-preview-large {
    width: 100px;
    height: 100px;
  }
  .avatar-placeholder-large {
    font-size: var(--text-3xl);
  }
}
</style>
