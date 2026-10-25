<template>
  <div
    class="chat-folders-bar"
  >
    <div class="chat-folders-bar__list">
      <button
        v-for="folder in sortedFolders"
        :key="folder.id"
        @click="handleFolderSelect(folder.id)"
        @contextmenu="handleFolderContextMenu($event, folder)"
        @mouseenter="showFolderTooltip($event, folder)"
        @mouseleave="hideFolderTooltip"
        :class="[
          'folder-icon',
          { 'folder-icon--active': activeFolderId === folder.id },
        ]"
        :style="getIconStyle(folder)"
        type="button"
      >
        <span class="folder-icon__emoji">
          <SakuraIcon
            v-if="isIconName(folder.icon)"
            :name="folder.icon"
            :size="22"
          />
          <span v-else>{{ folder.icon }}</span>
        </span>
        <span v-if="getUnreadCount(folder.id) > 0" class="folder-icon__badge">
          {{
            getUnreadCount(folder.id) > 99 ? "99+" : getUnreadCount(folder.id)
          }}
        </span>
      </button>
    </div>

    <div
      v-if="tooltipVisible"
      class="folder-tooltip"
      :style="{ left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      {{ tooltipText }}
    </div>

    <div class="chat-folders-bar__actions">
      <button
        @click="showCreateModal = true"
        class="action-button action-button--create"
        title="Создать папку"
        type="button"
      >
        <SakuraIcon name="folder" :size="18" />
      </button>

      <button
        @click="showShortcutsModal = true"
        class="action-button"
        title="Горячие клавиши"
        type="button"
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </button>
    </div>

    <FolderCreateModal
      :show="showCreateModal"
      @close="showCreateModal = false"
      @created="handleFolderCreated"
    />

    <FolderEditModal
      v-if="editingFolder"
      :show="showEditModal"
      :folder="editingFolder"
      @close="showEditModal = false"
      @updated="handleFolderUpdated"
      @deleted="handleFolderDeleted"
    />

    <FolderContextMenu
      v-if="contextMenu.folder"
      :visible="contextMenu.visible"
      :x="contextMenu.x"
      :y="contextMenu.y"
      :folder="contextMenu.folder"
      @close="contextMenu.visible = false"
      @edit="handleContextMenuEdit"
      @delete="handleContextMenuDelete"
    />

    <KeyboardShortcutsModal
      :show="showShortcutsModal"
      @close="showShortcutsModal = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useChatFoldersStore } from "@/stores/chatFolders";
import FolderCreateModal from "./FolderCreateModal.vue";
import FolderEditModal from "./FolderEditModal.vue";
import FolderContextMenu from "./FolderContextMenu.vue";
import KeyboardShortcutsModal from "./KeyboardShortcutsModal.vue";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import type { ChatFolder } from "@/types/chat";

const isIconName = (icon: string | undefined): boolean => {
  if (!icon) return false;
  return /^[a-zA-Z][a-zA-Z0-9-]*$/.test(icon);
};

const emit = defineEmits<{
  folderChange: [folder: ChatFolder | null];
}>();

const chatFoldersStore = useChatFoldersStore();

const showCreateModal = ref(false);
const showEditModal = ref(false);
const showShortcutsModal = ref(false);
const editingFolder = ref<ChatFolder | null>(null);
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  folder: null as ChatFolder | null,
});

const tooltipVisible = ref(false);
const tooltipText = ref("");
const tooltipX = ref(0);
const tooltipY = ref(0);
let tooltipTimeout: number | null = null;

const activeFolderId = computed(() => chatFoldersStore.activeFolderId);
const allFolders = computed(() => chatFoldersStore.allFolders);

const sortedFolders = computed(() => {
  return allFolders.value;
});


const getUnreadCount = (folderId: number): number => {
  return chatFoldersStore.getFolderUnreadCount(
    allFolders.value.find((f) => f.id === folderId)!,
    [],
  );
};

const getIconStyle = (folder: ChatFolder) => {
  if (activeFolderId.value === folder.id) {
    return {};
  }
  if (folder.color) {
    return {
      "--folder-color": folder.color,
    };
  }
  return {};
};

const handleFolderSelect = (folderId: number) => {
  chatFoldersStore.setActiveFolder(folderId);
  const folder = allFolders.value.find((f) => f.id === folderId) || null;
  emit("folderChange", folder);
};

const showFolderTooltip = (event: MouseEvent, folder: ChatFolder) => {
  tooltipText.value = folder.name;
  tooltipX.value = event.clientX;
  tooltipY.value = event.clientY - 10;

  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout);
  }

  tooltipTimeout = window.setTimeout(() => {
    tooltipVisible.value = true;
  }, 100);
};

const hideFolderTooltip = () => {
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout);
    tooltipTimeout = null;
  }
  tooltipVisible.value = false;
};

const handleFolderContextMenu = (event: MouseEvent, folder: ChatFolder) => {
  if (folder.is_system) return;

  contextMenu.value = {
    visible: true,
    x: event.clientX,
    y: event.clientY,
    folder,
  };
};

const handleFolderCreated = (folder: { id: number; name: string }) => {
  showCreateModal.value = false;
  chatFoldersStore.setActiveFolder(folder.id);
};

const handleFolderUpdated = () => {
  showEditModal.value = false;
  editingFolder.value = null;
};

const handleFolderDeleted = () => {
  showEditModal.value = false;
  editingFolder.value = null;
};

const handleContextMenuEdit = (folder: ChatFolder) => {
  editingFolder.value = folder;
  showEditModal.value = true;
};

const handleContextMenuDelete = () => {
  handleFolderDeleted();
};

const handleKeyboardShortcut = (event: KeyboardEvent) => {
  if (event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {
    const folderIndex = parseInt(event.key);

    if (event.key === "0") {
      chatFoldersStore.setActiveFolder(0);
      const folder = allFolders.value.find((f) => f.id === 0) || null;
      emit("folderChange", folder);
    } else if (!isNaN(folderIndex) && folderIndex >= 1 && folderIndex <= 9) {
      const folder = sortedFolders.value[folderIndex - 1];
      if (folder) {
        chatFoldersStore.setActiveFolder(folder.id);
        emit("folderChange", folder);
      }
    }
  } else if (
    event.key === "?" &&
    !event.ctrlKey &&
    !event.altKey &&
    !event.metaKey &&
    !event.shiftKey
  ) {
    showShortcutsModal.value = true;
  }
};

onMounted(() => {
  chatFoldersStore.loadFolders();
  document.addEventListener("keydown", handleKeyboardShortcut);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeyboardShortcut);
  if (tooltipTimeout) {
    clearTimeout(tooltipTimeout);
  }
});
</script>

<style scoped>
.chat-folders-bar {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 68px;
  height: calc(100% - 1.25rem);
  margin: 0.625rem 0 0.625rem 0.625rem;
  background: linear-gradient(
    180deg,
    rgba(255, 255, 255, 0.06) 0%,
    rgba(255, 255, 255, 0.02) 100%
  );
  background-color: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-2xl);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 0.75rem 0;
  gap: 0;
  z-index: 1000;
  box-shadow: var(--shadow-sm-modal);
  overflow: visible;
  flex-shrink: 0;
  animation: dock-in 0.35s var(--ease-petal);
}

@keyframes dock-in {
  from {
    opacity: 0;
    transform: translateX(-14px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.chat-folders-bar__list {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-height: 0;
  gap: 10px;
  padding: 0.25rem 0.5rem 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: none;
}

.chat-folders-bar__list::-webkit-scrollbar {
  width: 0;
}

.folder-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border: none;
  border-radius: var(--radius-xl);
  background-color: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.25s var(--ease-petal);
  flex-shrink: 0;
}

.folder-icon:hover {
  background-color: var(--surface-4);
  color: var(--text-primary);
  transform: translateY(-2px) scale(1.05);
  box-shadow: var(--shadow-sm-glow-sm);
}

.folder-icon--active {
  background: linear-gradient(135deg, var(--accent), var(--accent-4)) !important;
  color: var(--text-on-accent) !important;
  box-shadow:
    0 6px 18px -4px rgba(255, 126, 152, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
}

.folder-icon--active :deep(.sakura-icon),
.folder-icon--active .sakura-icon {
  color: white !important;
}

.folder-icon--active:hover {
  transform: translateY(-2px) scale(1.06);
}

.folder-icon--active::before {
  content: "";
  position: absolute;
  left: -12px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 26px;
  background: linear-gradient(180deg, var(--accent), var(--accent-4));
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  box-shadow: var(--shadow-sm-glow-sm);
}

.folder-icon__emoji {
  font-size: 1.35rem;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.folder-icon__badge {
  position: absolute;
  top: 2px;
  right: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  background: var(--danger);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  border-radius: var(--radius-full);
  border: 2px solid var(--surface-2);
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(255, 77, 109, 0.4);
}

.folder-icon--active .folder-icon__badge {
  background-color: white;
  color: var(--accent);
  border-color: var(--accent);
}

.chat-folders-bar__actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  padding: 0.6rem 0.5rem 0;
  border-top: 1px solid var(--border-subtle);
  margin-top: 0.4rem;
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border: none;
  border-radius: var(--radius-xl);
  background-color: var(--surface-3);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all 0.25s var(--ease-petal);
  flex-shrink: 0;
}

.action-button:hover {
  background-color: var(--accent-subtle);
  color: var(--accent);
  transform: translateY(-2px) scale(1.05);
  box-shadow: var(--shadow-sm-glow-sm);
}

.action-button--create {
  background: linear-gradient(135deg, var(--accent), var(--accent-4));
  color: var(--text-on-accent);
  box-shadow: var(--shadow-sm-glow-sm);
}

.action-button--create:hover {
  color: white;
  background: linear-gradient(135deg, var(--accent-press), var(--accent-4));
}

.action-button svg {
  width: 17px;
  height: 17px;
}

.folder-tooltip {
  position: fixed;
  padding: 0.5rem 0.75rem;
  background-color: var(--surface-3);
  color: var(--text-primary);
  font-size: 0.8125rem;
  font-weight: 500;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm-modal);
  z-index: 10000;
  pointer-events: none;
  white-space: nowrap;
  border: 1px solid var(--border-default);
}

@media (max-width: 768px) {
  .chat-folders-bar {
    width: 54px;
    height: calc(100% - 1rem);
    margin: 0.5rem;
    padding: 0.5rem 0;
  }

  .folder-icon,
  .action-button {
    width: 40px;
    height: 40px;
  }

  .folder-icon__emoji {
    font-size: 1.1rem;
  }

  .folder-icon--active::before {
    left: -9px;
  }

  .action-button svg {
    width: 15px;
    height: 15px;
  }
}
</style>
