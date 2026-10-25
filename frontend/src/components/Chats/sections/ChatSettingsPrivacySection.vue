<template>
  <section class="settings-section">
    <div class="section-header">
      <h2><SakuraIcon name="lock" /> Приватность</h2>
    </div>

    <div class="settings-group-card">
      <div class="danger-row">
        <div class="dr-info">
          <span class="dr-title">
            <template v-if="form.is_blocked"
              ><SakuraIcon name="check" /> Разблокировать</template
            >
            <template v-else
              ><SakuraIcon name="ban" /> Заблокировать
              пользователя</template
            >
          </span>
          <span class="dr-desc">{{
            form.is_blocked
              ? "Снять блокировку"
              : "Пользователь не сможет писать вам"
          }}</span>
        </div>
        <button
          v-if="!form.is_blocked"
          @click="$emit('block')"
          class="danger-btn"
        >
          Заблокировать
        </button>
        <button v-else @click="$emit('unblock')" class="btn-secondary">
          Разблокировать
        </button>
      </div>
    </div>

    <div class="settings-group-card danger-card">
      <div class="sgc-title" style="color: #ef4444">
        <SakuraIcon name="warning" />️ Опасная зона
      </div>
      <div class="danger-list">
        <div class="danger-row">
          <div class="dr-info">
            <span class="dr-title">Очистить историю</span>
            <span class="dr-desc"
              >Удалить все сообщения только для вас</span
            >
          </div>
          <button @click="$emit('clear-history')" class="danger-btn">
            Очистить
          </button>
        </div>
        <div class="danger-row">
          <div class="dr-info">
            <span class="dr-title">Удалить чат</span>
            <span class="dr-desc"
              >Безвозвратное удаление переписки</span
            >
          </div>
          <button
            @click="$emit('delete-chat')"
            class="danger-btn danger-btn--critical"
          >
            Удалить
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  form: Record<string, unknown>
  chatId: number
  chatType: "group" | "private"
}>()

defineEmits<{
  block: []
  unblock: []
  "clear-history": []
  "delete-chat": []
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
.btn-secondary {
  padding: 8px 16px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.15s var(--ease-petal);
}
.btn-secondary:hover {
  border-color: var(--accent);
}
</style>
