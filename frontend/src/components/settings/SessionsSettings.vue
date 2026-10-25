<template>
  <div class="settings-section">
    <h2>Активные сессии</h2>

    <div class="current-session" v-if="currentSession">
      <h3><SakuraIcon name="phone" /> Это устройство (текущее)</h3>
      <div class="session-info">
        <div class="session-details">
          <div class="device-name">
            {{ currentSession.device_name || "Неизвестное устройство" }}
          </div>
          <div class="device-location">
            {{ currentSession.location || "Неизвестно" }}
          </div>
          <div class="last-activity">Активно сейчас</div>
        </div>
        <div class="device-icon"><SakuraIcon name="phone" /></div>
      </div>
    </div>

    <div class="other-sessions" v-if="otherSessions.length > 0">
      <h3>● Другие устройства ({{ otherSessions.length }})</h3>

      <div class="session-list">
        <div
          v-for="session in otherSessions"
          :key="session.id"
          class="session-item"
        >
          <div class="session-info">
            <div class="device-name">{{ session.device_name }}</div>
            <div class="device-location">{{ session.location }}</div>
            <div class="last-activity">
              Активно {{ formatLastActivity(session.last_activity) }}
            </div>
          </div>
          <div class="device-icon">
            {{ getDeviceIcon(session.device_info) }}
          </div>
          <button
            @click="terminateSession(session)"
            class="terminate-btn"
            title="Завершить сессию"
          >
            ✕
          </button>
        </div>
      </div>
    </div>

    <div class="inactive-sessions" v-if="inactiveSessions.length > 0">
      <h3>● Неактивные сессии ({{ inactiveSessions.length }})</h3>
      <button class="view-inactive-btn">Показать неактивные сессии →</button>
    </div>

    <div class="security-settings">
      <h3><SakuraIcon name="settings" /> Настройки безопасности</h3>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="loginNotifications" />
          <span>Уведомлять о новых входах</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="rememberDevices" />
          <span>Запоминать устройства на {{ rememberDays }} дней</span>
        </label>
      </div>

      <div class="setting-item">
        <label class="setting-label">
          <input type="checkbox" v-model="autoTerminateOld" />
          <span>Автоматически завершать старые сессии</span>
        </label>
      </div>
    </div>

    <div class="danger-actions">
      <button @click="showTerminateAll = true" class="terminate-all-btn">
        🚪 Завершить все другие сессии
      </button>
    </div>

    <!-- Terminate All Confirmation Modal -->
    <div
      v-if="showTerminateAll"
      class="modal-overlay"
      @click="showTerminateAll = false"
    >
      <div class="modal" @click.stop>
        <h3>Завершить все другие сессии?</h3>
        <p>
          Вы действительно хотите завершить все сессии на других устройствах?
          Вам придется войти заново на всех этих устройствах.
        </p>

        <div class="session-list-preview">
          <div
            v-for="session in otherSessions.slice(0, 3)"
            :key="session.id"
            class="session-preview"
          >
            {{ session.device_name }} • {{ session.location }}
          </div>
          <div v-if="otherSessions.length > 3" class="more-sessions">
            ... и еще {{ otherSessions.length - 3 }} устройств
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showTerminateAll = false" class="cancel-btn">
            Отмена
          </button>
          <button @click="terminateAllOtherSessions" class="confirm-btn">
            Завершить все
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import * as settingsApi from "@/api/settings";

interface DeviceInfo {
  device?: string;
}

interface Session {
  id: number;
  session_key: string;
  device_info: DeviceInfo;
  device_name: string;
  location: string;
  last_activity: string;
  ip_address: string;
}

const sessions = ref<Session[]>([]);
const showTerminateAll = ref(false);
const loginNotifications = ref(true);
const rememberDevices = ref(true);
const rememberDays = ref(30);
const autoTerminateOld = ref(false);

const currentSession = computed(() => {
  return (
    sessions.value.find((session) =>
      session.device_name?.includes("Current"),
    ) ||
    sessions.value[0] ||
    ({} as Session)
  );
});

const otherSessions = computed(() => {
  return sessions.value.filter(
    (session) => session !== currentSession.value && isActive(session),
  );
});

const inactiveSessions = computed(() => {
  return sessions.value.filter((session) => !isActive(session));
});

const fetchSessions = async () => {
  try {
    const data = await settingsApi.getActiveSessions();
    sessions.value = data || [];
  } catch (error) {
    console.error("Error fetching sessions:", error);
  }
};

const isActive = (session: Session) => {
  const lastActivity = new Date(session.last_activity);
  const now = new Date();
  const diffHours = (now.getTime() - lastActivity.getTime()) / (1000 * 60 * 60);
  return diffHours < 24;
};

const formatLastActivity = (lastActivity: string) => {
  const date = new Date(lastActivity);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 60) {
    return `${diffMins} минут назад`;
  } else if (diffHours < 24) {
    return `${diffHours} часов назад`;
  } else {
    return `${diffDays} дней назад`;
  }
};

const getDeviceIcon = (deviceInfo: DeviceInfo) => {
  if (
    deviceInfo?.device?.toLowerCase().includes("mobile") ||
    deviceInfo?.device?.toLowerCase().includes("phone")
  ) {
    return "☎";
  } else if (deviceInfo?.device?.toLowerCase().includes("tablet")) {
    return "☎";
  } else {
    return "💻";
  }
};

const terminateSession = async (session: Session) => {
  try {
    await settingsApi.terminateSession(session.session_key);
    sessions.value = sessions.value.filter(
      (s) => s.session_key !== session.session_key,
    );
  } catch (error) {
    console.error("Error terminating session:", error);
  }
};

const terminateAllOtherSessions = async () => {
  try {
    await settingsApi.terminateAllOtherSessions();
    sessions.value = sessions.value.filter(
      (session) => session === currentSession.value,
    );
    showTerminateAll.value = false;
  } catch (error) {
    console.error("Error terminating all sessions:", error);
  }
};

onMounted(() => {
  fetchSessions();
});
</script>

<style scoped>
.settings-section h2 {
  margin-bottom: 30px;
}

.current-session,
.other-sessions,
.inactive-sessions,
.security-settings {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--surface-4);
  border-radius: 8px;
}

.current-session h3,
.other-sessions h3,
.inactive-sessions h3,
.security-settings h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: var(--accent);
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.session-details {
  flex: 1;
}

.device-name {
  font-weight: 600;
  margin-bottom: 4px;
}

.device-location {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 4px;
}

.last-activity {
  color: var(--text-secondary);
  font-size: 13px;
}

.device-icon {
  font-size: 24px;
  margin-left: 15px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 15px;
  background: var(--surface-3);
  border-radius: 8px;
  border: 1px solid var(--border-default);
}

.session-item .session-info {
  flex: 1;
}

.terminate-btn {
  background: none;
  border: none;
  color: #f44336;
  font-size: 18px;
  cursor: pointer;
  padding: 5px;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.terminate-btn:hover {
  background: rgba(244, 67, 54, 0.1);
}

.view-inactive-btn {
  background: var(--accent);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.setting-item {
  margin-bottom: 12px;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: 500;
}

.setting-label input[type="checkbox"] {
  margin: 0;
}

.danger-actions {
  margin-top: 30px;
  text-align: center;
}

.terminate-all-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  font-size: 16px;
}

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
  margin-bottom: 15px;
}

.modal p {
  margin-bottom: 20px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.session-list-preview {
  background: var(--surface-4);
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
  max-height: 150px;
  overflow-y: auto;
}

.session-preview {
  padding: 8px 0;
  border-bottom: 1px solid var(--border-default);
  font-size: 14px;
  color: var(--text-secondary);
}

.session-preview:last-child {
  border-bottom: none;
}

.more-sessions {
  padding: 8px 0;
  font-style: italic;
  color: var(--text-secondary);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid var(--border-default);
  background: var(--surface-3);
  border-radius: 6px;
  cursor: pointer;
}

.confirm-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
}

/* ═══ АДАПТИВНЫЕ СТИЛИ (мобильные / планшеты) ═══════════════ */

/* xs: 320px – 374px */
@media (max-width: 374px) {
  .settings-section h2 {
    margin-bottom: 20px;
    font-size: 18px;
  }

  .current-session,
  .other-sessions,
  .inactive-sessions,
  .security-settings {
    margin-bottom: 20px;
    padding: 14px;
    border-radius: 6px;
  }

  .current-session h3,
  .other-sessions h3,
  .inactive-sessions h3,
  .security-settings h3 {
    font-size: 14px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .session-info {
    gap: 10px;
  }

  .device-name {
    font-size: 13px;
  }

  .device-location {
    font-size: 12px;
    word-break: break-word;
  }

  .last-activity {
    font-size: 11px;
  }

  .device-icon {
    font-size: 20px;
    margin-left: 8px;
    flex-shrink: 0;
  }

  .session-list {
    gap: 10px;
  }

  .session-item {
    padding: 12px;
    gap: 8px;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .session-item .session-info {
    flex: 1 1 100%;
    order: 1;
  }

  .session-item .device-icon {
    order: 2;
    margin-left: 0;
  }

  .terminate-btn {
    order: 3;
    width: 28px;
    height: 28px;
    font-size: 16px;
    margin-left: auto;
  }

  .view-inactive-btn {
    width: 100%;
    padding: 10px 14px;
    font-size: 13px;
  }

  .setting-item {
    margin-bottom: 10px;
  }

  .setting-label {
    font-size: 13px;
    gap: 8px;
    align-items: flex-start;
  }

  .setting-label input[type="checkbox"] {
    margin-top: 2px;
    flex-shrink: 0;
  }

  .danger-actions {
    margin-top: 20px;
  }

  .terminate-all-btn {
    width: 100%;
    padding: 12px 16px;
    font-size: 14px;
  }

  .modal-overlay {
    padding: 8px;
    align-items: flex-end;
  }

  .modal {
    padding: 20px;
    max-width: 100%;
    width: 100%;
    border-radius: 12px 12px 0 0;
    max-height: 92vh;
    overflow-y: auto;
  }

  .modal h3 {
    font-size: 16px;
    margin-bottom: 12px;
  }

  .modal p {
    font-size: 13px;
    margin-bottom: 16px;
  }

  .session-list-preview {
    padding: 12px;
    margin-bottom: 16px;
    max-height: 120px;
  }

  .session-preview {
    font-size: 12px;
    padding: 6px 0;
  }

  .more-sessions {
    font-size: 12px;
  }

  .modal-actions {
    flex-direction: column-reverse;
    gap: 8px;
    justify-content: stretch;
  }

  .cancel-btn,
  .confirm-btn {
    width: 100%;
    padding: 11px 16px;
    font-size: 14px;
  }
}

/* sm: 375px – 767px */
@media (min-width: 375px) and (max-width: 767px) {
  .settings-section h2 {
    margin-bottom: 22px;
  }

  .current-session,
  .other-sessions,
  .inactive-sessions,
  .security-settings {
    margin-bottom: 22px;
    padding: 16px;
  }

  .session-item {
    padding: 14px;
    gap: 10px;
  }

  .device-icon {
    margin-left: 10px;
  }

  .setting-label {
    font-size: 14px;
  }

  .terminate-all-btn {
    width: 100%;
    padding: 13px 20px;
  }

  .modal-overlay {
    padding: 12px;
    align-items: flex-end;
  }

  .modal {
    padding: 24px;
    max-width: 100%;
    width: 100%;
    border-radius: 12px 12px 0 0;
  }

  .modal-actions {
    gap: 10px;
  }

  .cancel-btn,
  .confirm-btn {
    flex: 1;
    padding: 11px 16px;
  }
}

/* md: 768px – 1023px */
@media (min-width: 768px) and (max-width: 1023px) {
  .current-session,
  .other-sessions,
  .inactive-sessions,
  .security-settings {
    padding: 18px;
  }

  .session-item {
    padding: 14px;
  }

  .modal {
    max-width: 440px;
  }
}

/* Ландшафтная ориентация на мобильных -центрируем модалку */
@media (max-width: 767px) and (orientation: landscape) {
  .modal-overlay {
    align-items: center;
    padding: 8px;
  }

  .modal {
    max-height: 96vh;
    border-radius: 12px;
    max-width: 92vw;
    width: auto;
  }
}

/* Улучшение тач-взаимодействия */
@media (hover: none) and (pointer: coarse) {
  .terminate-btn:hover {
    background: none;
  }

  .terminate-btn:active {
    background: rgba(244, 67, 54, 0.15);
  }

  .terminate-all-btn:active,
  .view-inactive-btn:active,
  .cancel-btn:active,
  .confirm-btn:active {
    transform: scale(0.98);
  }

  .session-list-preview {
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
  }
}
</style>