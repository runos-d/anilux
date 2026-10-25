<template>
  <Teleport to="body">
    <div class="gs-backdrop" @click="$emit('close')">
      <div class="gs-modal" @click.stop>
        <div class="gs-header">
          <span class="gs-title"
            ><SakuraIcon name="settings" /> Настройки стиля чатов</span
          >
          <button class="gs-close" @click="$emit('close')">✕</button>
        </div>

        <div class="gs-body">

          <section class="gs-section">
            <h3 class="gs-section-title">Фон чата</h3>

            <div class="gs-row">
              <label class="gs-label">Акцентный цвет</label>
              <input
                type="color"
                v-model="form.accent_color"
                class="gs-color"
              />
            </div>
          </section>
        </div>

        <div class="gs-footer">
          <button class="gs-btn-reset" @click="resetDefaults">Сбросить</button>
          <button class="gs-btn-save" @click="save" :disabled="saving">
            {{ saving ? "Сохранение…" : "Сохранить" }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import apiClient from "@/api/client";

const emit = defineEmits<{ close: [] }>();

const saving = ref(false);

const DEFAULTS = {
  wallpaper_type: "solid",
  wallpaper_color: "#0f0f0f",
  wallpaper_color2: "#1a1a2e",
  bubble_style: "modern",
  accent_color: "#6C5CE7",
  font_size: "medium",
  message_animation: "slide",
  emoji_set: "default",
  time_format: "24h",
};

const form = ref({ ...DEFAULTS });



const load = async () => {
  try {
    const { data } = await apiClient.get("/social/chat-settings/global/");
    if (data) form.value = { ...DEFAULTS, ...data };
  } catch {
  }
};

const save = async () => {
  saving.value = true;
  try {
    await apiClient.put("/social/chat-settings/global/", form.value);
    localStorage.setItem("globalChatStyle", JSON.stringify(form.value));
    emit("close");
  } catch (e) {
    console.error("Ошибка сохранения глобального стиля:", e);
    localStorage.setItem("globalChatStyle", JSON.stringify(form.value));
    emit("close");
  } finally {
    saving.value = false;
  }
};

const resetDefaults = () => {
  form.value = { ...DEFAULTS };
};

onMounted(load);
</script>

<style scoped>
.gs-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(5, 4, 8, 0.88);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.gs-modal {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-sm-modal);
}
.gs-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.gs-title {
  color: var(--text-primary);
  font-weight: 700;
  font-size: 1rem;
}
.gs-close {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1.1rem;
  transition: color 0.15s var(--ease-petal);
}
.gs-close:hover {
  color: var(--accent);
}
.gs-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.gs-hint {
  color: var(--text-tertiary);
  font-size: 0.8rem;
  line-height: 1.5;
  margin: 0;
}

.gs-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.gs-section-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0;
}
.gs-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.gs-label {
  color: var(--text-secondary);
  font-size: 0.875rem;
  flex-shrink: 0;
}
.gs-select {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-primary);
  padding: 5px 8px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: border-color 0.15s var(--ease-petal);
}
.gs-select:focus {
  outline: none;
  border-color: var(--accent);
}
.gs-color {
  width: 40px;
  height: 30px;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  padding: 2px;
  background: transparent;
}
.gs-radio-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.gs-radio {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  cursor: pointer;
}
.gs-radio input {
  accent-color: var(--accent);
}

.gs-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.gs-btn-reset {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-tertiary);
  border-radius: var(--radius-lg);
  padding: 8px 16px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.15s var(--ease-petal);
}
.gs-btn-reset:hover {
  background: var(--surface-5);
  color: var(--text-secondary);
}
.gs-btn-save {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  border: none;
  color: var(--text-on-accent);
  border-radius: var(--radius-lg);
  padding: 8px 20px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.875rem;
  box-shadow: var(--shadow-sm-petal-sm);
  transition: all 0.15s var(--ease-petal);
}
.gs-btn-save:hover:not(:disabled) {
  box-shadow: var(--shadow-sm-glow-sm);
  transform: translateY(-1px);
}
.gs-btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
