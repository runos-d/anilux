<template>
  <section v-if="record.state === 'unknown'" class="consent-banner" role="dialog" aria-labelledby="analytics-consent-title" aria-describedby="analytics-consent-description">
    <div class="consent-copy">
      <h2 id="analytics-consent-title">Помочь улучшать AniLux?</h2>
      <p id="analytics-consent-description">
        Мы можем собирать только обезличенные просмотры разделов, технические ошибки и показатели скорости.
        Сообщения, поисковые запросы, email, телефон и содержимое форм не отправляются.
      </p>
      <RouterLink to="/privacy">Подробнее в политике приватности</RouterLink>
    </div>
    <div class="consent-actions">
      <button type="button" class="consent-button" @click="choose('denied')">Не разрешать</button>
      <button type="button" class="consent-button" @click="choose('granted')">Разрешить</button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onBeforeUnmount, ref } from "vue";
import { getConsent, onConsentChange, setConsent } from "@/analytics/consent";
import type { ConsentState } from "@/analytics/types";

const record = ref(getConsent());
const stop = onConsentChange((next) => { record.value = next; });
onBeforeUnmount(stop);

const choose = (state: Exclude<ConsentState, "unknown">) => {
  setConsent(state, "banner");
};
</script>

<style scoped>
.consent-banner {
  position: fixed;
  z-index: 2500;
  right: max(16px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
  left: max(16px, calc(var(--app-sidebar-offset, 0px) + 16px));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  max-width: 900px;
  margin: 0 auto;
  padding: 18px;
  color: var(--text-color);
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  box-shadow: 0 14px 40px rgb(0 0 0 / 28%);
}
.consent-copy h2 { margin: 0 0 6px; font-size: 18px; }
.consent-copy p { margin: 0 0 6px; max-width: 650px; line-height: 1.45; }
.consent-copy a { color: var(--primary-color); }
.consent-actions { display: flex; gap: 10px; flex: 0 0 auto; }
.consent-button {
  min-height: 42px;
  padding: 9px 16px;
  color: var(--text-color);
  background: var(--hover-bg);
  border: 1px solid var(--primary-color);
  border-radius: 8px;
  font: inherit;
  cursor: pointer;
}
.consent-button:focus-visible { outline: 3px solid var(--primary-color); outline-offset: 2px; }
@media (max-width: 720px) {
  .consent-banner { left: 12px; right: 12px; bottom: calc(var(--mobile-nav-height, 64px) + 12px); flex-direction: column; align-items: stretch; }
  .consent-actions { display: grid; grid-template-columns: 1fr 1fr; }
}
@media (max-width: 380px) { .consent-actions { grid-template-columns: 1fr; } }
</style>
