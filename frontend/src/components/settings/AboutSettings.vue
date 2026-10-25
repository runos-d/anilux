<template>
  <div class="settings-section">
    <h2>О программе</h2>

    <div class="settings-group">
      <div class="app-info">
        <div class="app-logo"></div>
        <div class="app-details">
          <div class="app-name">AniLux</div>
          <div class="app-version">
            Версия: {{ appVersion }} (build {{ buildNumber }})
          </div>
          <div class="app-update">Последнее обновление: {{ lastUpdate }}</div>
          <div class="app-size">Размер: {{ appSize }}</div>
        </div>
      </div>

      <div class="update-status" :class="updateStatusClass">
        <span class="status-icon">{{ updateStatusIcon }}</span>
        <span class="status-text">{{ updateStatusText }}</span>
        <button
          v-if="updateAvailable"
          @click="checkForUpdates"
          class="check-update-btn"
        >
          <SakuraIcon name="search" /> Проверить обновления
        </button>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="file-text" /> Лицензия и права</h3>

      <div class="license-info">
        <p class="copyright">© 2024 AniLux. Все права защищены.</p>

        <div class="license-details">
          <div class="license-row">
            <span class="license-label">Лицензия:</span>
            <span>Пользовательское соглашение</span>
          </div>
          <div class="license-row">
            <span class="license-label">Версия соглашения:</span>
            <span>Документ готовится к публикации</span>
          </div>
        </div>

        <div class="legal-links">
          <button @click="showTerms = true" class="legal-link">
            <SakuraIcon name="file-text" /> Пользовательское соглашение
          </button>
          <button @click="showPrivacy = true" class="legal-link">
            <SakuraIcon name="lock" /> Политика конфиденциальности
          </button>
          <button @click="showLicense = true" class="legal-link">
            <SakuraIcon name="scale" /> Лицензионное соглашение
          </button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="users" /> Команда</h3>

      <div class="team-info">
        <div class="team-section">
          <h4>Над проектом работают:</h4>
          <div class="team-members">
            <div class="team-member">
              <span class="member-role">Основатель:</span>
              <span class="member-name">{{ teamInfo.founder }}</span>
            </div>
            <div class="team-member">
              <span class="member-role">Разработчики:</span>
              <span class="member-name">{{ teamInfo.developers }} человек</span>
            </div>
            <div class="team-member">
              <span class="member-role">Дизайнеры:</span>
              <span class="member-name">{{ teamInfo.designers }} человека</span>
            </div>
            <div class="team-member">
              <span class="member-role">Модераторы:</span>
              <span class="member-name">{{ teamInfo.moderators }} человек</span>
            </div>
          </div>
        </div>

        <div class="contact-links">
          <button @click="contactSupport" class="contact-btn">
            <SakuraIcon name="mail" /> Связаться с поддержкой
          </button>
          <button @click="joinDevChat" class="contact-btn">
            <SakuraIcon name="message" /> Чат сообщества разработчиков
          </button>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="pray" /> Благодарности</h3>

      <div class="acknowledgments">
        <div class="ack-section">
          <h4>Использованные технологии:</h4>
          <div class="tech-stack">
            <span class="tech-badge">Django</span>
            <span class="tech-badge">Vue.js</span>
            <span class="tech-badge">PostgreSQL</span>
            <span class="tech-badge">Redis</span>
            <span class="tech-badge">TypeScript</span>
            <span class="tech-badge">Vite</span>
          </div>
        </div>

        <div class="ack-section">
          <h4>Отдельное спасибо:</h4>
          <p class="ack-text">
            Сообществу <a href="#" class="external-link">Shikimori</a> за API и
            вдохновение.
          </p>
          <p class="ack-text">
            Всем пользователям за обратную связь и поддержку проекта.
          </p>
        </div>

        <div class="ack-section">
          <h4>Open Source:</h4>
          <p class="ack-text">
            Проект использует open-source библиотеки. Спасибо всем
            разработчикам, которые вносят вклад в развитие open-source
            сообщества.
          </p>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="chart" /> Статистика проекта</h3>

      <div class="project-stats">
        <div class="stat-card">
          <div class="stat-icon"><SakuraIcon name="users" /></div>
          <div class="stat-value">{{ formatNumber(stats.users) }}</div>
          <div class="stat-label">Пользователей</div>
        </div>

        <div class="stat-card">
          <div class="stat-icon"><SakuraIcon name="tv" /></div>
          <div class="stat-value">{{ formatNumber(stats.anime) }}</div>
          <div class="stat-label">Аниме в базе</div>
        </div>

        <div class="stat-card">
          <div class="stat-icon"><SakuraIcon name="clipboard" /></div>
          <div class="stat-value">{{ formatNumber(stats.playlists) }}</div>
          <div class="stat-label">Плейлистов</div>
        </div>

        <div class="stat-card">
          <div class="stat-icon"><SakuraIcon name="play" /></div>
          <div class="stat-value">{{ formatNumber(stats.shorts) }}</div>
          <div class="stat-label">Shorts</div>
        </div>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="link" /> Ссылки</h3>

      <div class="links-grid">
        <a href="#" class="link-item">
          <span class="link-icon">🌐</span>
          <div class="link-info">
            <span class="link-name">Веб-сайт</span>
            <span class="link-url">Официальный сайт AniLux</span>
          </div>
        </a>

        <a href="#" class="link-item">
          <span class="link-icon"> <SakuraIcon name="phone" /> </span>
          <div class="link-info">
            <span class="link-name">Мобильное приложение</span>
            <span class="link-url">App Store / Google Play</span>
          </div>
        </a>

        <a href="#" class="link-item">
          <span class="link-icon"> <SakuraIcon name="bird" /> </span>
          <div class="link-info">
            <span class="link-name">Twitter</span>
            <span class="link-url">AniLux в Telegram</span>
          </div>
        </a>

        <a href="#" class="link-item">
          <span class="link-icon"> <SakuraIcon name="message" /> </span>
          <div class="link-info">
            <span class="link-name">Discord</span>
            <span class="link-url">AniLux в Discord</span>
          </div>
        </a>

        <a href="#" class="link-item">
          <span class="link-icon"> <SakuraIcon name="tv" /> </span>
          <div class="link-info">
            <span class="link-name">YouTube</span>
            <span class="link-url">AniLux Official</span>
          </div>
        </a>

        <a href="#" class="link-item">
          <span class="link-icon">🐙</span>
          <div class="link-info">
            <span class="link-name">GitHub</span>
            <span class="link-url">AniLux на GitHub</span>
          </div>
        </a>
      </div>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="file-text" /> Журнал изменений</h3>

      <div class="changelog">
        <div
          v-for="version in changelog"
          :key="version.version"
          class="changelog-item"
        >
          <div class="changelog-header">
            <span class="version-badge">{{ version.version }}</span>
            <span class="version-date">{{ formatDate(version.date) }}</span>
          </div>

          <div class="changelog-content">
            <div v-if="version.features.length > 0" class="changelog-section">
              <span class="section-label new"
                ><SakuraIcon name="sparkles" /> Новое:</span
              >
              <ul class="changelog-list">
                <li v-for="feature in version.features" :key="feature">
                  {{ feature }}
                </li>
              </ul>
            </div>

            <div
              v-if="version.improvements.length > 0"
              class="changelog-section"
            >
              <span class="section-label improved"
                ><SakuraIcon name="wrench" /> Улучшения:</span
              >
              <ul class="changelog-list">
                <li
                  v-for="improvement in version.improvements"
                  :key="improvement"
                >
                  {{ improvement }}
                </li>
              </ul>
            </div>

            <div v-if="version.fixes.length > 0" class="changelog-section">
              <span class="section-label fixed">🐛 Исправления:</span>
              <ul class="changelog-list">
                <li v-for="fix in version.fixes" :key="fix">{{ fix }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <button @click="showFullChangelog = true" class="view-changelog-btn">
        Показать весь журнал →
      </button>
    </div>

    <div class="settings-group">
      <h3><SakuraIcon name="lady-beetle" /> Сообщить о проблеме</h3>

      <div class="bug-report">
        <p class="bug-info">
          Нашли ошибку или есть предложение? Помогите нам сделать AniLux
          лучше!
        </p>

        <div class="report-options">
          <button @click="reportBug" class="report-btn">
            <SakuraIcon name="bug" /> Сообщить об ошибке
          </button>
          <button @click="makeSuggestion" class="report-btn">
            <SakuraIcon name="lightbulb" /> Предложить идею
          </button>
          <button @click="makeSuggestion" class="report-btn">
            <SakuraIcon name="lightbulb" /> Сделать предложение
          </button>
          <button @click="requestFeature" class="report-btn">
            <SakuraIcon name="clipboard" /> Запросить функцию
          </button>
        </div>
      </div>
    </div>

    <!-- Модальные окна -->
    <TermsModal :show="showTerms" @close="showTerms = false" />
    <PrivacyModal :show="showPrivacy" @close="showPrivacy = false" />
    <LicenseModal :show="showLicense" @close="showLicense = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import navigation from '../../../public/site-navigation.json';
import TermsModal from "@/components/modal/settings/TermsModal.vue";
import PrivacyModal from "@/components/modal/settings/PrivacyModal.vue";
import LicenseModal from "@/components/modal/settings/LicenseModal.vue";

const appVersion = ref("1.2.3");
const buildNumber = ref("2024.01.15");
const lastUpdate = ref("15.01.2024");
const appSize = ref("45.2 MB");

const updateStatus = ref("up-to-date");
const updateAvailable = ref(false);

const teamInfo = ref({
  founder: "AnimeTeam",
  developers: 5,
  designers: 2,
  moderators: 10,
});

const stats = ref({
  users: 45678,
  anime: 12345,
  playlists: 67890,
  shorts: 23456,
});

const showTerms = ref(false);
const showPrivacy = ref(false);
const showLicense = ref(false);
const showFullChangelog = ref(false);

const changelog = ref([
  {
    version: "1.2.3",
    date: "2024-01-15",
    features: [
      "Добавлен раздел настроек с полной кастомизацией",
      "Новая система уведомлений с расширенными опциями",
      "Импорт и экспорт данных в разных форматах",
    ],
    improvements: [
      "Улучшена производительность загрузки изображений",
      "Оптимизирована работа с большими плейлистами",
      "Улучшен мобильный интерфейс",
    ],
    fixes: [
      "Исправлена ошибка с сохранением настроек темы",
      "Исправлен баг с отображением уведомлений",
      "Исправлена проблема с синхронизацией данных",
    ],
  },
  {
    version: "1.2.2",
    date: "2024-01-01",
    features: ["Добавлена поддержка тёмной темы", "Новые эмодзи для чатов"],
    improvements: [
      "Улучшена скорость поиска",
      "Оптимизировано использование памяти",
    ],
    fixes: ["Исправлены мелкие баги"],
  },
  {
    version: "1.2.0",
    date: "2023-12-15",
    features: [
      "Полностью переработан интерфейс настроек",
      "Добавлена синхронизация между устройствами",
      "Новая система управления плейлистами",
    ],
    improvements: [],
    fixes: [],
  },
]);

const updateStatusClass = computed(() => {
  switch (updateStatus.value) {
    case "up-to-date":
      return "up-to-date";
    case "available":
      return "available";
    case "checking":
      return "checking";
    case "error":
      return "error";
    default:
      return "";
  }
});

const updateStatusIcon = computed(() => {
  switch (updateStatus.value) {
    case "up-to-date":
      return "☑️";
    case "available":
      return "🆕";
    case "checking":
      return "🔄";
    case "error":
      return "✖️";
    default:
      return "ℹ️";
  }
});

const updateStatusText = computed(() => {
  switch (updateStatus.value) {
    case "up-to-date":
      return "У вас актуальная версия";
    case "available":
      return "Доступно обновление!";
    case "checking":
      return "Проверка обновлений...";
    case "error":
      return "Ошибка проверки обновлений";
    default:
      return "";
  }
});

const formatNumber = (num: number) => {
  return num.toLocaleString("ru-RU");
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
};

const checkForUpdates = () => {
  updateStatus.value = "checking";
  setTimeout(() => {
    updateStatus.value = "up-to-date";
  }, 2000);
};

const contactSupport = () => {
  window.open('mailto:' + navigation.email, "_blank");
};

const joinDevChat = () => {
  window.open("https://discord.gg/anisphere", "_blank");
};

const reportBug = () => {
  window.open("https://github.com/anisphere/anisphere/issues", "_blank");
};

const makeSuggestion = () => {
  window.open("https://github.com/anisphere/anisphere/discussions", "_blank");
};

const requestFeature = () => {
  window.open(
    "https://github.com/anisphere/anisphere/issues/new?template=feature_request.md",
    "_blank",
  );
};
</script>

<style scoped>
.settings-group {
  margin-bottom: 30px;
  padding: 20px;
  background: var(--surface-4);
  border-radius: 8px;
}

.settings-group h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
}

.app-info {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.app-logo {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #ff6b6b, #4ecdc4);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
}

.app-details {
  flex: 1;
}

.app-name {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 8px;
}

.app-version {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.app-update,
.app-size {
  font-size: 13px;
  color: var(--text-secondary);
}

.update-status {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  background: var(--surface-3);
  border-radius: 6px;
}

.update-status.up-to-date {
  border-left: 4px solid #4caf50;
}

.update-status.available {
  border-left: 4px solid #ffc107;
  background: rgba(255, 193, 7, 0.1);
}

.update-status.checking {
  border-left: 4px solid var(--accent);
}

.update-status.error {
  border-left: 4px solid #f44336;
}

.status-icon {
  font-size: 24px;
}

.status-text {
  flex: 1;
  font-weight: 500;
}

.check-update-btn {
  padding: 8px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.license-info {
  line-height: 1.6;
}

.copyright {
  font-weight: 500;
  margin-bottom: 15px;
}

.license-details {
  margin-bottom: 20px;
}

.license-row {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 14px;
}

.license-label {
  color: var(--text-secondary);
  min-width: 140px;
}

.legal-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legal-link {
  padding: 12px 16px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  transition: all 0.2s;
}

.legal-link:hover {
  border-color: var(--accent);
  background: var(--surface-4);
}

.team-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.team-section h4 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.team-members {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.team-member {
  display: flex;
  justify-content: space-between;
  padding: 10px 15px;
  background: var(--surface-3);
  border-radius: 4px;
}

.member-role {
  color: var(--text-secondary);
}

.member-name {
  font-weight: 500;
}

.contact-links {
  display: flex;
  gap: 10px;
}

.contact-btn {
  flex: 1;
  padding: 12px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.acknowledgments {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ack-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.ack-text {
  margin: 0;
  line-height: 1.6;
  color: var(--text-primary);
}

.external-link {
  color: var(--accent);
  text-decoration: none;
}

.external-link:hover {
  text-decoration: underline;
}

.tech-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tech-badge {
  padding: 6px 12px;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
}

.project-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: var(--surface-3);
  border-radius: 8px;
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 5px;
}

.stat-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.links-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
}

.link-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: var(--surface-3);
  border-radius: 6px;
  text-decoration: none;
  color: var(--text-primary);
  transition: all 0.2s;
}

.link-item:hover {
  background: var(--surface-4);
  transform: translateY(-2px);
}

.link-icon {
  font-size: 24px;
}

.link-info {
  display: flex;
  flex-direction: column;
}

.link-name {
  font-weight: 500;
  margin-bottom: 2px;
}

.link-url {
  font-size: 12px;
  color: var(--text-secondary);
}

.changelog {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.changelog-item {
  padding: 15px;
  background: var(--surface-3);
  border-radius: 6px;
}

.changelog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-default);
}

.version-badge {
  padding: 4px 10px;
  background: var(--accent);
  color: white;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 600;
}

.version-date {
  font-size: 13px;
  color: var(--text-secondary);
}

.changelog-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.changelog-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-label {
  font-size: 13px;
  font-weight: 600;
}

.section-label.new {
  color: #4caf50;
}

.section-label.improved {
  color: var(--accent);
}

.section-label.fixed {
  color: #ff9800;
}

.changelog-list {
  margin: 0;
  padding-left: 20px;
}

.changelog-list li {
  margin-bottom: 5px;
  font-size: 14px;
  color: var(--text-primary);
}

.view-changelog-btn {
  width: 100%;
  padding: 12px;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: 6px;
  cursor: pointer;
  color: var(--text-primary);
  margin-top: 15px;
}

.bug-report {
  text-align: center;
}

.bug-info {
  margin-bottom: 20px;
  color: var(--text-secondary);
}

.report-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.report-btn {
  flex: 1;
  min-width: 150px;
  padding: 12px 16px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

@media (max-width: 768px) {
  .app-info {
    flex-direction: column;
    text-align: center;
  }

  .project-stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .links-grid {
    grid-template-columns: 1fr;
  }

  .report-options {
    flex-direction: column;
  }
}
</style>
