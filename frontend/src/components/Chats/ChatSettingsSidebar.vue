<template>
  <div class="settings-sidebar">
    <div class="sidebar-header">
      <div class="chat-info-row">
        <img v-if="chatAvatar" :src="chatAvatar" class="chat-avatar-mini" />
        <div v-else class="chat-avatar-mini avatar-placeholder">
          {{ (chatName || "?")[0] }}
        </div>
        <div class="chat-meta">
          <div class="chat-name-mini">{{ chatName }}</div>
          <div class="chat-type-pill">
            {{ chatType === "group" ? "Группа" : "Личный" }}
          </div>
        </div>
      </div>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <nav class="sidebar-nav">
      <button
        v-for="section in sections"
        :key="section.id"
        @click="$emit('update:activeSection', section.id)"
        class="nav-item"
        :class="{ active: activeSection === section.id }"
      >
        <span class="nav-icon">{{ section.icon }}</span>
        <span class="nav-label">{{ section.name }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  chatAvatar?: string
  chatName?: string
  chatType: "group" | "private"
  activeSection: string
  sections: { id: string; name: string; icon: string }[]
}>()

defineEmits<{
  close: []
  "update:activeSection": [value: string]
}>()
</script>

<style scoped>
.settings-sidebar {
  width: 220px;
  min-width: 220px;
  background: var(--surface-1);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
}
.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.chat-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.chat-avatar-mini {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--accent-subtle);
}
.avatar-placeholder {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  color: var(--text-on-accent);
  box-shadow: var(--shadow-sm-petal-sm);
}
.chat-meta {
  min-width: 0;
}
.chat-name-mini {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chat-type-pill {
  font-size: 10px;
  color: var(--text-tertiary);
  background: var(--surface-4);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  margin-top: 2px;
  display: inline-block;
}
.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
  border-radius: var(--radius-md);
  transition: all 0.2s var(--ease-petal);
  flex-shrink: 0;
}
.close-btn:hover {
  color: var(--accent);
  background: var(--surface-4);
}
.sidebar-nav {
  padding: 8px;
  overflow-y: auto;
  flex: 1;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 12px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  transition: all 0.15s var(--ease-petal);
  text-align: left;
  font-size: 13px;
}
.nav-item:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--accent-subtle);
  color: var(--accent);
  font-weight: 500;
}
.nav-icon {
  font-size: 16px;
  flex-shrink: 0;
  color: inherit;
}
.nav-label {
  flex: 1;
}
</style>
