<template>
  <div v-if="show" class="modal-overlay" @click="$emit('close')">
    <div class="modal" @click.stop>
      <h3>Поделиться плейлистом</h3>

      <div class="modal-share-options">
        <button class="share-option" @click="shareTo('telegram')">
          <span class="icon"> <SakuraIcon name='phone' /> </span>
          <span>Telegram</span>
        </button>
        <button class="share-option" @click="shareTo('vk')">
          <span class="icon"> <SakuraIcon name='circle' /> </span>
          <span>VK</span>
        </button>
        <button class="share-option" @click="shareTo('whatsapp')">
          <span class="icon"> <SakuraIcon name='message' /> </span>
          <span>WhatsApp</span>
        </button>
        <button class="share-option" @click="copyLink">
          <span class="icon"> <SakuraIcon name='link' /> </span>
          <span>Скопировать ссылку</span>
        </button>
      </div>

      <div class="modal-link">
        <label>Прямая ссылка:</label>
        <div class="link-input">
          <input :value="playlistLink" readonly />
          <button @click="copyLink" class="copy-btn">Копировать</button>
        </div>
      </div>

      <div class="modal-actions">
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue"
defineProps<{
  show: boolean;
  playlistLink?: string;
}>();

const emit = defineEmits<{
  close: [];
  share: [platform: string];
  copyLink: [];
}>();

const shareTo = (platform: string) => {
  emit("share", platform);
};

const copyLink = () => {
  emit("copyLink");
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
  z-index: 1000;
}

.modal {
  background: var(--surface-3);
  padding: 30px;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  border: 1px solid var(--border-default);
}

.modal h3 {
  margin-top: 0;
  margin-bottom: 20px;
  text-align: center;
}

.modal-share-options {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 20px;
}

.share-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 15px;
  border: 1px solid var(--border-default);
  background: var(--surface-1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.share-option:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.share-option .icon {
  font-size: 24px;
}

.share-option span {
  font-size: 14px;
}

.modal-link {
  margin-bottom: 20px;
}

.modal-link label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
}

.link-input {
  display: flex;
  gap: 10px;
}

.link-input input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid var(--border-default);
  border-radius: 6px;
  background: var(--surface-1);
  color: var(--text-secondary);
}

.copy-btn {
  padding: 10px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  width: 100%;
  padding: 12px 20px;
  border: 1px solid var(--border-default);
  background: var(--surface-3);
  border-radius: 6px;
  cursor: pointer;
}
</style>