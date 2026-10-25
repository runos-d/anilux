<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
</script>

<template>
  <div class="donate-page">
    <header class="page-header">
      <h1><SakuraIcon name="heart" :size="16" /> Поддержать проект</h1>
      <p class="subtitle">
        Помогите нам развиваться и радовать вас новым контентом!
      </p>
    </header>

    <div class="donate-content">
      <section class="donate-reason">
        <h2>Почему это важно?</h2>
        <p>
          Animesphere -это бесплатная платформа для любителей аниме. Мы не
          показываем рекламу и не требуем подписки. Однако для поддержания
          серверов, покупки доменов, хранения баз данных и развития проекта
          нужны средства.
        </p>
        <p>Каждый ваш донат помогает нам:</p>
        <ul class="reason-list">
          <li><SakuraIcon name="rocket" /> Оплачивать серверы и хостинг</li>
          <li>
            <SakuraIcon name="save" /> Обеспечивать резервное копирование данных
          </li>
          <li><SakuraIcon name="sparkles" /> Добавлять новые функции</li>
          <li><SakuraIcon name="bug" /> Улучшать производительность</li>
        </ul>
      </section>

      <section class="donate-methods">
        <h2>Способы доната</h2>

        <div class="methods-grid">
          <div class="donate-card main">
            <div class="card-icon"><SakuraIcon name="gift" /></div>
            <h3>Donation Alerts</h3>
            <p>
              Официальная платформа для приёма донатов с поддержкой
              автоматических пожертвований и отображения ваших имён в
              донатерском списке.
            </p>
            <a
              href="https://www.donationalerts.com/r/anisphere"
              target="_blank"
              rel="noopener noreferrer"
              class="donate-btn primary"
            >
              Перейти на Donation Alerts
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"
                />
                <polyline points="15 3 21 3 21 9" />
                <line x1="10" y1="14" x2="21" y2="3" />
              </svg>
            </a>
            <div class="donation-link">
              <span class="link-label">Ссылка для доната:</span>
              <code class="link-value"
                >https://www.donationalerts.com/r/anisphere</code
              >
            </div>
          </div>

        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.donate-page {
  padding: 2rem 1rem;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 3rem;
}

.page-header h1 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
}

.subtitle {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Причина */
.donate-reason {
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
}

.donate-reason h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
}

.donate-reason p {
  font-size: 1rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 1rem 0;
}

.reason-list {
  list-style: none;
  padding: 0;
  margin: 1rem 0 0 0;
}

.reason-list li {
  font-size: 1rem;
  color: var(--text-primary);
  padding: 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

/* Методы доната */
.donate-methods {
  margin-bottom: 3rem;
}

.donate-methods h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.methods-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.donate-card {
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 1rem;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
}

.donate-card.main {
  grid-column: span 2;
  background: linear-gradient(
    135deg,
    rgba(58, 134, 255, 0.1) 0%,
    rgba(255, 107, 107, 0.1) 100%
  );
  border-color: var(--accent);
}

.card-icon {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
}

.donate-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
}

.donate-card p {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 1.25rem 0;
  flex: 1;
}

.donate-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.875rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s;
  cursor: pointer;
  border: none;
}

.donate-btn.primary {
  background: var(--accent);
  color: white;
}

.donate-btn.primary:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.donate-btn.secondary {
  background: var(--surface-3);
  color: var(--text-primary);
  border: 1px solid var(--border-strong);
}

.donate-btn.secondary:hover {
  background: var(--surface-1-hover);
}

.donation-link {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-strong);
}

.link-label {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 0.25rem;
}

.link-value {
  font-family: monospace;
  font-size: 0.9375rem;
  color: var(--accent);
  background: var(--surface-1);
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}

.wallet-info {
  margin-top: auto;
}

.wallet-label {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 0.5rem;
}

.wallet-number {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.wallet-number code {
  font-family: monospace;
  font-size: 1.125rem;
  color: var(--text-primary);
  background: var(--surface-1);
  padding: 0.5rem 0.75rem;
  border-radius: 0.375rem;
}

.copy-btn {
  padding: 0.5rem;
  background: var(--surface-1);
  border: 1px solid var(--border-strong);
  border-radius: 0.375rem;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.copy-btn:hover {
  background: var(--surface-1-hover);
  color: var(--text-primary);
}

.crypto-info {
  margin-bottom: 1rem;
}

.crypto-item {
  margin-bottom: 0.75rem;
}

.crypto-name {
  font-size: 0.8125rem;
  color: var(--text-tertiary);
  display: block;
  margin-bottom: 0.25rem;
}

.crypto-address {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--text-primary);
  background: var(--surface-1);
  padding: 0.375rem 0.5rem;
  border-radius: 0.25rem;
  word-break: break-all;
  display: block;
}

.copy-btn-full {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--surface-1);
  border: 1px solid var(--border-strong);
  border-radius: 0.5rem;
  color: var(--text-primary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto;
}

.copy-btn-full:hover {
  background: var(--surface-1-hover);
}

/* FAQ */
.donate-faq {
  margin-bottom: 3rem;
}

.donate-faq h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1.5rem 0;
  text-align: center;
}

.faq-item {
  background: var(--surface-3);
  border: 1px solid var(--border-strong);
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.faq-item h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
}

.faq-item p {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Благодарность */
.donate-thanks {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(
    135deg,
    rgba(58, 134, 255, 0.08) 0%,
    rgba(255, 107, 107, 0.08) 100%
  );
  border-radius: 1rem;
  border: 1px solid var(--border-strong);
}

.donate-thanks h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 0.75rem 0;
}

.donate-thanks p {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Адаптивность */
@media (max-width: 768px) {
  .methods-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .donate-card.main {
    grid-column: span 1;
  }

  .page-header h1 {
    font-size: 1.75rem;
  }

  .donate-reason,
  .donate-card,
  .faq-item {
    padding: 1.25rem;
  }

  .crypto-address {
    word-break: break-all;
    font-size: 0.9rem;
  }

  .copy-btn {
    width: 100%;
    margin-top: 8px;
  }

  .copy-btn-full {
    width: 100%;
  }

  .donate-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 480px) {
  .donate-page {
    padding: 1rem 0.5rem;
  }

  .donate-content {
    padding: 0;
  }

  .donate-reason,
  .donate-card,
  .faq-item {
    padding: 1rem;
    border-radius: 0.75rem;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .subtitle {
    font-size: 1rem;
  }

  .donate-reason h2,
  .donate-methods h2,
  .donate-faq h2 {
    font-size: 1.25rem;
  }

  .crypto-address {
    font-size: 0.75rem;
    padding: 0.25rem 0.375rem;
  }
}

/* ============================================================
   ДОПОЛНИТЕЛЬНЫЕ АДАПТИВНЫЕ СТИЛИ ДЛЯ МОБИЛЬНЫХ И ПЛАНШЕТОВ
   (десктопные стили выше остаются без изменений)
   ============================================================ */

/* Планшеты: 769px – 1024px */
@media (max-width: 1024px) and (min-width: 769px) {
  .donate-page {
    padding: 1.75rem 1rem;
  }

  .methods-grid {
    gap: 1.25rem;
  }
}

/* Большие телефоны / маленькие планшеты: 481px – 768px */
@media (max-width: 768px) {
  .donate-page {
    padding: 1.5rem 0.875rem;
  }

  .page-header {
    margin-bottom: 2rem;
  }

  .donate-content {
    padding: 0;
  }

  .reason-list li {
    padding-left: 1.25rem;
    font-size: 0.9375rem;
  }

  .link-value {
    display: block;
    font-size: 0.8125rem;
    word-break: break-all;
  }

  .wallet-number {
    flex-wrap: wrap;
  }

  .wallet-number code {
    font-size: 1rem;
    flex: 1;
    min-width: 0;
    word-break: break-all;
  }
}

/* Телефоны: до 480px */
@media (max-width: 480px) {
  .page-header h1 {
    font-size: 1.375rem;
    line-height: 1.25;
  }

  .subtitle {
    font-size: 0.875rem;
    line-height: 1.4;
  }

  .donate-reason p {
    font-size: 0.9rem;
    line-height: 1.55;
  }

  .reason-list li {
    font-size: 0.875rem;
    padding-left: 1.15rem;
    padding-top: 0.4rem;
    padding-bottom: 0.4rem;
  }

  .card-icon {
    font-size: 2rem;
  }

  .donate-card h3 {
    font-size: 1.1rem;
  }

  .donate-card p {
    font-size: 0.875rem;
  }

  .donate-btn {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }

  .link-label,
  .wallet-label,
  .crypto-name {
    font-size: 0.75rem;
  }

  .link-value,
  .wallet-number code {
    font-size: 0.8125rem;
    padding: 0.4rem 0.6rem;
  }

  .crypto-address {
    font-size: 0.7rem;
    padding: 0.3rem 0.4rem;
    line-height: 1.4;
  }

  .copy-btn-full {
    font-size: 0.8125rem;
    padding: 0.65rem 0.85rem;
  }
}

/* Ландшафтная ориентация на телефонах */
@media (max-width: 768px) and (orientation: landscape) {
  .donate-page {
    padding: 1rem 1.25rem;
  }

  .page-header {
    margin-bottom: 1.5rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .donate-reason {
    padding: 1rem 1.25rem;
    margin-bottom: 1.25rem;
  }
}

/* Очень узкие экраны: до 360px */
@media (max-width: 360px) {
  .donate-page {
    padding: 0.875rem 0.4rem;
  }

  .page-header h1 {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8125rem;
  }

  .donate-reason,
  .donate-card,
  .faq-item {
    padding: 0.875rem;
  }

  .reason-list li {
    font-size: 0.8125rem;
  }

  .donate-btn {
    font-size: 0.85rem;
    padding: 0.65rem 0.85rem;
  }

  .crypto-address {
    font-size: 0.65rem;
  }
}

/* Устройства с вырезом (notch) и safe-area */
@supports (padding: max(0px)) {
  @media (max-width: 768px) {
    .donate-page {
      padding-left: max(0.875rem, env(safe-area-inset-left));
      padding-right: max(0.875rem, env(safe-area-inset-right));
      padding-bottom: max(1rem, env(safe-area-inset-bottom));
    }
  }
}
</style>
