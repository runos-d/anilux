<template>
  <section class="application-view">
    <h1>Приложение AniLux</h1>
    <!-- <p>Каталог, библиотека и общение в отдельном окне на телефоне и компьютере.</p> -->
    <!-- <small class="app-build">Сборка {{ buildTime }}</small> -->
    <!-- <div class="app-card">
      <h2>Скачать приложение</h2>
      <p>Android -APK, Windows -EXE. Для Ubuntu и Debian выберите DEB, для других дистрибутивов Linux -AppImage или Flatpak.</p>
      <p v-if="['loading', 'queued', 'building'].includes(release.status)" role="status">Установочные файлы готовятся. Ссылки появятся здесь автоматически.</p>
      <p v-if="release.status === 'unconfigured'">Установочные файлы пока недоступны. Можно установить приложение через браузер по инструкции ниже.</p>
      <div class="installer-grid">
        <article v-for="file in release.artifacts" :key="file.platform" class="installer">
          <h3>{{ file.label }}</h3>
          <template v-if="file.status === 'ready' && file.url">
            <a class="btn-primary" :href="file.url" download><SakuraIcon name="download" /> Скачать {{ formats[file.platform] }}</a>
            <small>{{ release.version }} · {{ installerSize(file.size) }}</small>
            <p v-if="file.platform === 'appimage'">В свойствах загруженного файла разрешите запуск как программы.</p>
          </template>
          <p v-else-if="file.platform === 'ios' && file.status === 'requires_signing'">IPA пока недоступна. Установите приложение через Safari по инструкции ниже.</p>
          <p v-else-if="file.status === 'failed'">Файл пока недоступен. Можно установить приложение через браузер ниже.</p>
          <p v-else>Подготовка {{ formats[file.platform] }}…</p>
        </article>
      </div>
      <p v-if="releaseError" class="app-error" role="alert">{{ releaseError }}</p>
      <button v-if="releaseError || ['failed', 'pending', 'unconfigured'].includes(release.status)" class="app-button" @click="loadReleases">Проверить доступность файлов</button>
    </div> -->
    <div class="app-card">
      <h2>{{ installed ? 'Приложение установлено' : 'Установка' }}</h2>
      <button v-if="canInstall" class="btn-primary" @click="install"><SakuraIcon name="download" /> Установить приложение</button>
      <template v-else-if="!installed">
        <p v-if="!secure">Откройте сайт по HTTPS, чтобы установить приложение.</p>
        <p v-else>Если кнопка установки не появилась, используйте меню браузера:</p>
        <ul>
          <li><b>iPhone и iPad:</b> Safari → «Поделиться» → «На экран Домой».</li>
          <li><b>Android:</b> меню Chrome → «Установить и создать ярлык»</li>
          <li><b>Компьютер:</b> <br>
            - Chrome: троеточие справа сверху → "Транслировать, сохранить, поделиться" → "Установить страницу, как приложение"<br>
            - Safari: «Файл» → «Добавить в Dock»</li>
        </ul>
      </template>
      <p v-else>Запускайте AniLux с рабочего стола, из Dock или с главного экрана.</p>
    </div>
    <!-- <div class="app-card">
      <h2>Сеть и обновления</h2>
      <p role="status">{{ online ? 'Есть подключение к сети' : 'Вы сейчас без сети' }}. {{ offlineReady ? 'Файлы приложения сохранены.' : error ? 'Файлы приложения не сохранены.' : 'Файлы приложения ещё загружаются.' }}</p>
      <p>Файлы интерфейса и черновики чатов и публикаций сохраняются на устройстве. Для запуска приложения, загрузки каталога, просмотра видео и обмена сообщениями требуется подключение к сети.</p>
      <template v-if="needsRefresh">
        <p>Доступна новая версия. Сохраните изменения перед перезапуском.</p>
        <button class="btn-primary" :disabled="!online || updating" @click="update">Обновить приложение</button>
      </template>
      <button v-else class="app-button" :disabled="!online" @click="checkUpdate">Проверить обновления</button>
      <button v-if="error && !offlineReady" class="app-button" :disabled="!online" @click="retryPreparation">Перезагрузить и повторить</button>
    </div> -->
    <!-- <div class="app-card">
      <h2>Уведомления на устройстве</h2>
      <p v-if="!auth.isAuthenticated">Войдите в аккаунт, чтобы включить уведомления.</p>
      <template v-else>
        <p>{{ pushMessage }}</p>
        <button v-if="pushSupported" class="app-button" :disabled="pushBusy || !online" @click="togglePush">{{ pushEnabled ? 'Выключить на этом устройстве' : 'Включить уведомления' }}</button>
        <RouterLink to="/notifications/settings">Настройки уведомлений аккаунта</RouterLink>
      </template>
    </div> -->
    <p v-if="error || pushError" class="app-error" role="alert">{{ error || pushError }}</p>
  </section>
</template>
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { usePwa } from '@/composables/usePwa'
import { useAuthStore } from '@/stores/auth'
import SakuraIcon from '@/components/icons/SakuraIcon.vue'
import { enableDevicePush, disableDevicePush, devicePushEnabled } from '@/lib/devicePush'
import { useNativeReleases, installerSize } from '@/composables/useNativeReleases'
const { release, error: releaseError, load: loadReleases } = useNativeReleases()
const formats: Record<string, string> = { windows: 'EXE', android: 'APK', deb: 'DEB', appimage: 'AppImage', flatpak: 'Flatpak', ios: 'IPA' }
const auth = useAuthStore()
const { online, installed, canInstall, offlineReady, needsRefresh, updating, error, install, update, checkUpdate, retryPreparation } = usePwa()
const secure = window.isSecureContext
const buildTime = new Date(import.meta.env.VITE_APP_BUILD_TIME).toLocaleString('ru-RU')
const pushEnabled = ref(false), pushBusy = ref(false), pushError = ref('')
const pushSupported = 'PushManager' in window && 'Notification' in window && 'serviceWorker' in navigator
const pushMessage = ref(pushSupported ? 'Уведомления приходят даже при закрытом приложении. На iPhone установите приложение на главный экран.' : 'Эта версия приложения не поддерживает фоновые push-уведомления. Для них откройте сайт в поддерживаемом браузере и установите PWA.')
onMounted(async () => { pushEnabled.value = await devicePushEnabled(); if (pushEnabled.value) pushMessage.value = 'Уведомления на этом устройстве включены.' })
async function togglePush() {
  pushBusy.value = true; pushError.value = ''
  try {
    if (pushEnabled.value) await disableDevicePush()
    else await enableDevicePush()
    pushEnabled.value = await devicePushEnabled()
    pushMessage.value = pushEnabled.value ? 'Уведомления на этом устройстве включены.' : 'Уведомления на этом устройстве выключены.'
  } catch (e) { pushError.value = e instanceof Error ? e.message : 'Не удалось изменить уведомления.' }
  finally { pushBusy.value = false }
}
</script>
<style scoped>
.application-view { max-width: 800px; margin: 0 auto; padding: 24px 16px; color: var(--text-primary); overflow-wrap: anywhere; }
.application-view h1 { font-size: var(--text-2xl); } .application-view h2 { font-size: var(--text-lg); margin-bottom: 12px; }
.application-view p, .application-view li { line-height: 1.65; margin-bottom: 12px; }
.application-view ul { padding-left: 22px; }
.app-card { background: var(--surface-2); border: 1px solid var(--border-subtle); border-radius: 16px; padding: 20px; margin-top: 20px; }
.app-button, .btn-primary { min-height: 44px; padding: 10px 16px; display: inline-flex; align-items: center; gap: 8px; border-radius: 10px; margin: 12px 12px 12px 0; border: 1px solid var(--border-subtle); background: var(--surface-3); color: var(--text-primary); cursor: pointer; white-space: normal; }
.btn-primary { background: var(--accent); color: white; } button:disabled { opacity: .5; cursor: default; }
.app-error { color: var(--error, #e85b70); margin-top: 16px; }
.installer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 240px), 1fr)); gap: 12px; }
.installer { padding: 16px; border: 1px solid var(--border-subtle); border-radius: 12px; min-width: 0; }
.installer h3 { margin: 0 0 12px; font-weight: 600; } .installer small { display: block; }
@media (max-width: 480px) { .app-card { padding: 16px; } }
</style>
