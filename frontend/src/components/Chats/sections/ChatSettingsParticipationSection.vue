<template>
  <section class="settings-section">
    <div class="section-header">
      <h2><SakuraIcon name="users" /> Участие в группе</h2>
    </div>

    <div class="settings-group-card danger-card">
      <div class="sgc-title" style="color: #ef4444">
        <SakuraIcon name="warning" />️ Действия
      </div>
      <div class="danger-list">
        <div class="danger-row">
          <div class="dr-info">
            <span class="dr-title">Выйти из группы</span>
            <span class="dr-desc">Покинуть эту групповую беседу</span>
          </div>
          <button
            @click="$emit('leave-group')"
            class="danger-btn danger-btn--critical"
          >
            Выйти
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  chatId: number
}>()

defineEmits<{
  "leave-group": []
}>()
</script>

<style scoped>
.settings-section {
  padding: 24px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.section-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
.settings-group-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  margin-bottom: 16px;
}
.danger-card {
  border-color: var(--danger-subtle);
}
.sgc-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-tertiary);
  margin-bottom: 12px;
}
.danger-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-subtle);
}
.danger-row:last-child {
  border-bottom: none;
}
.dr-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dr-title {
  font-size: 13px;
  color: var(--text-primary);
}
.dr-desc {
  font-size: 11px;
  color: var(--text-tertiary);
}
.danger-btn {
  padding: 6px 14px;
  background: var(--danger);
  border: 1px solid var(--danger-press);
  color: white;
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.15s var(--ease-petal);
  white-space: nowrap;
}
.danger-btn:hover {
  background: var(--danger-press);
}
.danger-btn--critical {
  background: var(--danger);
  border-color: var(--danger-press);
  color: white;
  font-weight: 600;
}
.danger-btn--critical:hover {
  background: var(--danger-press);
}
</style>
