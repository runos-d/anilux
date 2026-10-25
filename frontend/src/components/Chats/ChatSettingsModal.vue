<template>
  <Teleport to="body">
    <div class="modal-overlay" @click.self="$emit('close')">
      <div class="chat-settings-modal">
        <div class="settings-sidebar">
          <div class="sidebar-header">
            <div class="chat-info-row">
              <UserAvatar :src="chatAvatar" :alt="chatName" size="sm" class="chat-avatar-mini" />
              <div class="chat-meta">
                <span class="sidebar-overline">Настройки</span>
                <div class="chat-name-mini">{{ chatName }}</div>
                <div class="chat-type-pill">
                  {{ chatType === "group" ? "Группа" : "Личный чат" }}
                </div>
              </div>
            </div>
            <button @click="$emit('close')" class="close-btn" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
          </div>

          <nav class="sidebar-nav" @keydown="onNavKeydown">
            <template v-for="group in navGroups" :key="group.title">
              <div class="nav-group-title">{{ group.title }}</div>
              <button
                v-for="section in group.items"
                :key="section.id"
                type="button"
                :ref="setNavItemRef(section.id)"
                @click="setSection(section.id)"
                class="nav-item"
                :class="{ active: activeSection === section.id }"
              >
                <span class="nav-icon-chip">
                  <SakuraIcon :name="section.icon" />
                </span>
                <span class="nav-label">
                  <span class="nav-name">{{ section.name }}</span>
                  <span class="nav-hint">{{ section.desc }}</span>
                </span>
              </button>
            </template>
          </nav>

          <div class="sidebar-footer">
            <SakuraIcon name="sparkles" />
            <span>AniLux</span>
          </div>
        </div>

        <div ref="contentEl" class="settings-content">
          <div v-if="loading" class="loading-state">
            <p>Загрузка настроек...</p>
          </div>

          <Transition v-else name="section-swap" mode="out-in">
            <div :key="activeSection" class="settings-pane">
            <!-- Temporarily disabled: advanced chat settings.
<ChatSettingsBackupSection v-if="activeSection === 'backups' && chatType === 'group'"
              :chat-id="chatId" :can-restore="!!isOwner || isSiteAdmin" @restored="showToast('История восстановлена')" />
-->
            <!-- Temporarily disabled: advanced chat settings.
<section v-if="activeSection === 'transfer'" class="settings-section">
              <div class="section-header"><h2>Перенос настроек</h2></div>
              <p>Экспортирует ваши настройки чатов, папки, темы и изображения оформления.</p>
              <button :disabled="saving" @click="exportPersonalSettings">Скачать настройки</button>
              <label>Импорт настроек <input type="file" accept="application/json,.json" :disabled="saving" @change="importPersonalSettings" /></label>
            </section>
-->
            <ChatSettingsWallpaperSection
              v-if="activeSection === 'wallpaper'"
              :form="wallpaperForm"
              :chat-name="chatName || ''"
              :image-preview="wallpaperImagePreview"
              :has-custom="hasCustomWallpaper"
              :saving="saving"
              :solid-color-presets="solidColorPresets"
              :type-options="wallpaperTypeOptions"
              :mine-bubble-style="mineBubbleStyle"
              :other-bubble-style="otherBubbleStyle"
              :anime-card-border-radius="themeForm.anime_card_border_radius"
              :playlist-card-border-radius="themeForm.playlist_card_border_radius"
              @save="saveWallpaper"
              @reset="resetWallpaper"
              @file-change="handleWallpaperFile"
              @file-clear="clearWallpaperImage"
              @update:wallpaper-blur="wallpaperForm.wallpaper_blur = $event"
              @update:wallpaper-intensity="wallpaperForm.wallpaper_intensity = $event"
              @update:wallpaper-type="wallpaperForm.wallpaper_type = $event"
              @update:wallpaper-color="wallpaperForm.wallpaper_color = $event"
            />

    <ChatSettingsAvatarSection
               v-else-if="showAvatarSection"
               :chat-name="chatName || ''"
               :chat-avatar="chatAvatar"
               :avatar-preview="avatarPreview"
               :saving="saving"
               v-model:name="groupInfo.name"
               v-model:description="groupInfo.description"
               @save-info="saveGroupInfo"
               @save="saveAvatar"
               @clear="clearAvatar"
               @file-change="handleAvatarFile"
             />

            <ChatSettingsThemeSection
              v-if="activeSection === 'theme'"
              v-model:form="themeForm"
              :theme-presets="themePresets"
              :preset-id="currentPresetId"
              :saving="saving"
              :bubble-styles="bubbleStyles"
              :font-families="fontFamilies"
              :font-sizes="fontSizes"
              :interface-colors="interfaceColors"
              :theme-toggles="themeToggles"
              :chat-name="chatName || ''"
              :wallpaper-type="wallpaperForm.wallpaper_type"
              :wallpaper-color="wallpaperForm.wallpaper_color"
              :wallpaper-color2="wallpaperForm.wallpaper_color2"
              :wallpaper-intensity="wallpaperForm.wallpaper_intensity"
              :wallpaper-blur="wallpaperForm.wallpaper_blur"
              :pattern-type="wallpaperForm.pattern_type"
              :pattern-color="wallpaperForm.pattern_color"
              :pattern-opacity="wallpaperForm.pattern_opacity"
               :wallpaper-image-url="wallpaperForm.wallpaper_image_url"
               :wallpaper-image-preview="wallpaperImagePreview"
               :anime-card-border-radius="themeForm.anime_card_border_radius"
               :playlist-card-border-radius="themeForm.playlist_card_border_radius"
               @update:wallpaper-blur="wallpaperForm.wallpaper_blur = $event"
              @update:wallpaper-intensity="wallpaperForm.wallpaper_intensity = $event"
              @save="saveTheme"
              @reset="resetTheme"
              @preset-apply="applyThemePreset"
            />

            <section
              v-if="activeSection === 'notifications'"
              class="settings-section"
            >
              <div class="section-header">
                <h2><SakuraIcon name="bell" /> Уведомления</h2>
              </div>

              <div class="settings-group-card">
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Уведомления</span>
                      <span class="tr-desc"
                        >Получать уведомления из этого чата</span
                      >
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="notifForm.notifications_enabled"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <!-- Temporarily disabled: advanced chat settings.
<template v-if="notifForm.notifications_enabled">
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Только упоминания</span>
                        <span class="tr-desc"
                          >Уведомлять только при @упоминании</span
                        >
                      </div>
                      <label class="switch">
                        <input
                          type="checkbox"
                          v-model="notifForm.mentions_only"
                        />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Звук уведомлений</span>
                      </div>
                      <label class="switch">
                        <input
                          type="checkbox"
                          v-model="notifForm.sound_enabled"
                        />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Звук уведомления</span>
                        <span class="tr-desc"
                          >Выберите звук для уведомлений</span
                        >
                      </div>
                      <select v-model="notifForm.notification_sound" class="select-field" style="width: auto; min-width: 160px;">
                        <option value="default">По умолчанию</option>
                        <option value="soft">Мягкий</option>
                        <option value="loud">Громкий</option>
                        <option value="gentle">Нежный</option>
                        <option value="alert">Сигнал</option>
                        <option value="none">Без звука</option>
                      </select>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Вибрация</span>
                        <span class="tr-desc"
                          >Вибрация при получении сообщения</span
                        >
                      </div>
                      <label class="switch">
                        <input
                          type="checkbox"
                          v-model="notifForm.vibration_enabled"
                        />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Тип вибрации</span>
                        <span class="tr-desc"
                          >Выберите паттерн вибрации</span
                        >
                      </div>
                      <select v-model="notifForm.vibration_type" class="select-field" style="width: auto; min-width: 160px;">
                        <option value="default">По умолчанию</option>
                        <option value="short">Короткая</option>
                        <option value="long">Длинная</option>
                        <option value="double">Двойная</option>
                        <option value="heartbeat">Ритмичная</option>
                        <option value="none">Без вибрации</option>
                      </select>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Превью сообщения</span>
                        <span class="tr-desc"
                          >Показывать текст сообщения в уведомлении</span
                        >
                      </div>
                      <label class="switch">
                        <input
                          type="checkbox"
                          v-model="notifForm.show_preview"
                        />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                    <div class="toggle-row">
                      <div class="tr-info">
                        <span class="tr-label">Всплывающее уведомление</span>
                        <span class="tr-desc"
                          >Показывать плавающие уведомления поверх других окон</span
                        >
                      </div>
                      <label class="switch">
                        <input
                          type="checkbox"
                          v-model="notifForm.show_popup"
                        />
                        <span class="switch-slider"></span>
                      </label>
                    </div>
                  </template>
-->
                </div>
              </div>

              <!-- <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="volume-x" /> Заглушить
                </div>
                <div class="mute-grid">
                  <button
                    v-for="opt in muteOptions"
                    :key="opt.value"
                    @click="muteChat(opt.value)"
                    class="mute-btn"
                    :class="{ active: currentMuteDuration === opt.value }"
                  >
                    {{ opt.label }}
                  </button>
                </div>
                <div
                  v-if="
                    notifForm.muted_until ||
                    notifForm.notifications_enabled === false
                  "
                  class="mute-status"
                >
                  <span
                    ><SakuraIcon name="volume-x" />
                    {{
                      notifForm.muted_until
                        ? `Заглушено до ${formatMuteDate(notifForm.muted_until)}`
                        : "Навсегда заглушено"
                    }}</span
                  >
                  <button @click="unmuteChat" class="btn-link">
                    Включить звук
                  </button>
                </div>
              </div> -->

              <div class="section-actions">
                <button
                  @click="saveNotifSettings"
                  class="btn-primary"
                  :disabled="saving"
                >
                  <template v-if="saving">Сохранение...</template>
                  <template v-else>
                    <SakuraIcon name="save" />
                    Сохранить
                  </template>
                </button>
              </div>
            </section>

            <section
              v-if="activeSection === 'organize'"
              class="settings-section"
            >
              <div class="section-header">
                <h2><SakuraIcon name="folder-open" /> Организация</h2>
              </div>

              <div class="settings-group-card">
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label"
                        ><SakuraIcon name="pin" /> Закрепить чат</span
                      >
                      <span class="tr-desc">Показывать вверху списка</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="organizeForm.is_pinned"
                        @change="saveOrganizeSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label"
                        ><SakuraIcon name="package" /> Архивировать</span
                      >
                      <span class="tr-desc">Скрыть из основного списка</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="organizeForm.is_archived"
                        @change="saveOrganizeSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
<!-- Temporarily disabled: hide chat.
                  <div v-if="chatType === 'private'" class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label"
                        ><SakuraIcon name="eye-off" /> Скрыть чат</span
                      >
                      <span class="tr-desc">Не показывать в списке</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="organizeForm.is_hidden"
                        @change="saveOrganizeSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
-->
                </div>
              </div>

              <!-- Temporarily disabled: advanced chat organization.
<div class="settings-group-card">
                <div class="sgc-title"><SakuraIcon name="folder" /> Папка</div>
                <select
                  v-model="organizeForm.folder_id"
                  class="select-field"
                  @change="saveOrganizeSettings"
                >
                  <option :value="null">Без папки</option>
                  <option
                    v-for="folder in chatFolders"
                    :key="String(folder.id)"
                    :value="folder.id"
                  >
                    <span v-if="folder.icon">{{ folder.icon }}</span
                    ><SakuraIcon v-else name="folder" /> {{ folder.name }}
                  </option>
                </select>
              </div>
-->

              <div v-if="chatType === 'private'" class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="edit" /> Кастомное название
                </div>
                <div class="field-group">
                  <input
                    v-model="organizeForm.custom_name"
                    class="text-field"
                    placeholder="Персональное название..."
                    maxlength="255"
                  />
                  <p class="field-hint">Видно только вам</p>
                </div>
                <button @click="saveOrganizeSettings" class="btn-secondary">
                  Сохранить
                </button>
              </div>

              <!-- Temporarily disabled: advanced chat organization.
<div v-if="chatType === 'private'" class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="trash" /> Автоудаление
                </div>
                <div class="toggle-row">
                  <div class="tr-info">
                    <span class="tr-label">Автоудаление сообщений</span>
                    <span class="tr-desc"
                      >Удалять старые сообщения автоматически</span
                    >
                  </div>
                  <label class="switch">
                    <input
                      type="checkbox"
                      v-model="organizeForm.auto_delete_enabled"
                      @change="saveOrganizeSettings"
                    />
                    <span class="switch-slider"></span>
                  </label>
                </div>
                <div
                  v-if="organizeForm.auto_delete_enabled"
                  class="field-group mt-3"
                >
                  <label class="field-label"
                    >Через {{ organizeForm.auto_delete_after }} дней</label
                  >
                  <UiRangeSlider
                    v-model.number="organizeForm.auto_delete_after"
                    min="1"
                    max="365"
                    class="range-slider"
                    @change="saveOrganizeSettings"
                  />
                </div>
              </div>
-->
            </section>

            <section
              v-if="activeSection === 'security' && chatType === 'private'"
              class="settings-section"
            >
              <div class="section-header">
                <h2><SakuraIcon name="lock" /> Безопасность</h2>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="user-x" /> Блокировка
                </div>
                <div class="danger-row">
                  <div class="dr-info">
                    <span class="dr-title">
                      <template v-if="privacyForm.is_blocked"
                        ><SakuraIcon name="check" /> Разблокировать</template
                      >
                      <template v-else
                        ><SakuraIcon name="ban" /> Заблокировать
                        пользователя</template
                      >
                    </span>
                    <span class="dr-desc">{{
                      privacyForm.is_blocked
                        ? "Снять блокировку"
                        : "Пользователь не сможет писать вам"
                    }}</span>
                  </div>
                  <button
                    v-if="!privacyForm.is_blocked"
                    @click="blockUser"
                    class="danger-btn"
                  >
                    Заблокировать
                  </button>
                  <button v-else @click="unblockUser" class="btn-secondary">
                    Разблокировать
                  </button>
                </div>
              </div>

              <div class="settings-group-card danger-card">
                <div class="sgc-title danger-title">
                  <SakuraIcon name="trash" /> Очистка и удаление
                </div>
                <div class="danger-list">
                  <div class="danger-row">
                    <div class="dr-info">
                      <span class="dr-title">Очистить историю</span>
                      <span class="dr-desc"
                        >Удалить все сообщения только для вас</span
                      >
                    </div>
                    <button @click="clearHistory" class="danger-btn">
                      Очистить
                    </button>
                  </div>
                  <div class="danger-row">
                    <div class="dr-info">
                      <span class="dr-title">Удалить чат</span>
                      <span class="dr-desc"
                        >Скрыть чат из вашего списка до нового сообщения</span
                      >
                    </div>
                    <button
                      @click="deleteChat"
                      class="danger-btn danger-btn--critical"
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            </section>

            <!-- Temporarily disabled: advanced chat settings.
<section
              v-if="activeSection === 'moderation' && chatType === 'group'"
              class="settings-section"
            >
              <div class="section-header"><h2>🛡️ Модерация</h2></div>

              <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="timer" /> Медленный режим
                </div>
                <div class="toggle-row">
                  <div class="tr-info">
                    <span class="tr-label">Медленный режим</span>
                    <span class="tr-desc">Ограничение частоты сообщений</span>
                  </div>
                  <label class="switch">
                    <input
                      type="checkbox"
                      v-model="groupSettings.slow_mode_enabled"
                      @change="saveGroupSettings"
                    />
                    <span class="switch-slider"></span>
                  </label>
                </div>
                <div
                  v-if="groupSettings.slow_mode_enabled"
                  class="field-group mt-3"
                >
                  <label class="field-label"
                    >Задержка: {{ groupSettings.slow_mode_delay }}с</label
                  >
                  <UiRangeSlider
                    v-model.number="groupSettings.slow_mode_delay"
                    min="5"
                    max="3600"
                    class="range-slider"
                    @change="saveGroupSettings"
                  />
                  <div class="slow-presets">
                    <button
                      v-for="d in [5, 10, 30, 60, 300, 3600]"
                      :key="d"
                      @click="
                        groupSettings.slow_mode_delay = d;
                        saveGroupSettings();
                      "
                      class="slow-preset-btn"
                      :class="{ active: groupSettings.slow_mode_delay === d }"
                    >
                      {{ formatDelay(d) }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="mail" /> Разрешённый контент
                </div>
                <div class="toggle-list">
                  <div
                    v-for="perm in contentPermissions"
                    :key="perm.key"
                    class="toggle-row"
                  >
                    <div class="tr-info">
                      <span class="tr-label">{{ perm.label }}</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="
                          groupSettings[perm.key as keyof typeof groupSettings]
                        "
                        @change="saveGroupSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>

              <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="lock" /> Приватность группы
                </div>
                <div class="toggle-list">
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Скрыть список участников</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="groupSettings.has_hidden_members"
                        @change="saveGroupSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div class="toggle-row">
                    <div class="tr-info">
                      <span class="tr-label">Запретить сохранение медиа</span>
                    </div>
                    <label class="switch">
                      <input
                        type="checkbox"
                        v-model="groupSettings.restrict_saving_content"
                        @change="saveGroupSettings"
                      />
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                </div>
              </div>
            </section>
-->

            <section
              v-if="activeSection === 'participation' && chatType === 'group'"
              class="settings-section"
            >
              <div class="section-header">
                <h2><SakuraIcon name="users" /> Участие в группе</h2>
              </div>


              <div class="settings-group-card">
                <div class="sgc-title">
                  <SakuraIcon name="users" /> Участники ({{ members.length }})
                </div>
                <div v-if="loadingMembers" class="loading-state" style="height: 120px;">

                  <p>Загрузка участников...</p>
                </div>
                <div v-else class="members-list">
                  <div v-for="member in members" :key="member.user.id" class="member-card">
                    <img
                      :src="member.user.avatar_url || member.user.avatar || ''"
                      class="member-avatar"
                      :alt="member.user.display_name"
                    />
                    <div class="member-info">
                      <div class="member-name">{{ member.user.display_name }}</div>
                      <div class="member-role">
                        <span
                          :class="[
                            'role-badge',
                            member.is_owner ? 'owner' : member.is_admin ? 'admin' : 'participant',
                          ]"
                        >
                          {{ member.is_owner ? 'Владелец' : member.is_admin ? 'Админ' : 'Участник' }}
                        </span>
                        <span v-if="member.custom_title" class="member-custom-title">{{ member.custom_title }}</span>
                      </div>
                    </div>
                    <div v-if="canManageMember(member)" class="member-actions">
                      <!-- Temporarily disabled: group moderation.
<select
                        :value="memberStatusValue(member)"
                        @change="onMemberStatusChange(member, ($event.target as HTMLSelectElement).value)"
                        class="role-select"
                      >
                        <option value="participant">Участник</option>
                        <option value="admin">Админ</option>
                        <option v-if="isOwner" value="owner">Владелец</option>
                      </select>
-->
                      <button
                        @click="removeMember(member.user.id)"
                        class="btn-icon btn-icon--danger"
                        title="Удалить"
                      >
                        <SakuraIcon name="x" :size="16" />
                      </button>
                      <!-- Temporarily disabled: group moderation.
<button
                        @click="banMember(member.user.id)"
                        class="btn-icon btn-icon--danger"
                        title="Забанить"
                      >
                        🚫
                      </button>
-->
                    </div>
                  </div>
                </div>
              </div>

            <div class="settings-group-card actions-card">
              <div class="sgc-title actions-title">
                <SakuraIcon name="warning" /> Действия
              </div>
              <div class="danger-list">
                <div class="danger-row">
                  <div class="dr-info">
                    <span class="dr-title">Выйти из группы</span>
                    <span class="dr-desc">Покинуть эту групповую беседу</span>
                  </div>
                  <button
                    @click="leaveGroup"
                    class="action-btn action-btn--leave"
                  >
                    Выйти
                  </button>
                </div>
                <div v-if="isOwner" class="danger-row">
                  <div class="dr-info">
                    <span class="dr-title">Удалить группу</span>
                    <span class="dr-desc">Удалить группу навсегда (необратимо)</span>
                  </div>
                  <button
                    @click="deleteChat"
                    class="action-btn action-btn--delete"
                  >
                    Удалить группу
                  </button>
                </div>
              </div>
            </div>
            </section>
            </div>
          </Transition>
        </div>
      </div>
    </div>

    <Transition name="toast-anim">
      <div
        v-if="toast.show"
        class="global-toast"
        :class="`toast-${toast.type}`"
      >
        {{ toast.message }}
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import UiRangeSlider from "@/components/common/UiRangeSlider.vue";
import UserAvatar from '@/components/ui/UserAvatar.vue';
import { ref, computed, nextTick, onMounted, onUnmounted } from "vue";
import apiClient from "@/api/client";
import ChatSettingsAvatarSection from "./sections/ChatSettingsAvatarSection.vue";
import ChatSettingsWallpaperSection from "./sections/ChatSettingsWallpaperSection.vue";
import ChatSettingsThemeSection from "./sections/ChatSettingsThemeSection.vue";
import ChatSettingsBackupSection from "./sections/ChatSettingsBackupSection.vue";
import { useAuthStore } from '@/stores/auth';
import { rolesApi } from "@/api/chats";
import { useGroupChatStore } from "@/stores/groupChat";

interface ThemeForm {
  theme: string;
  message_color_mine: string;
  message_color_other: string;
  message_text_color_mine: string;
  message_text_color_other: string;
  bubble_style: string;
  bubble_border_radius: number;
  bubble_shadow: boolean;
  font_family: string;
  font_size: string;
  font_size_px: number;
  font_weight: number;
  line_height: number;
  time_format: string;
  time_color: string;
  background_color: string;
  header_color: string;
  input_color: string;
  input_text_color: string;
  accent_color: string;
  link_color: string;
  message_animation: string;
  reaction_animation: string;
  typing_animation: string;
  emoji_set: string;
  emoji_size: string;
  show_avatars: boolean;
  show_usernames: boolean;
  compact_mode: boolean;
  show_read_status: boolean;
  show_typing_indicator: boolean;
  message_grouping: boolean;
  custom_css: string;
  anime_card_border_radius: number;
  playlist_card_border_radius: number;
  [key: string]: unknown;
}

interface GroupSettingsForm {
  slow_mode_enabled: boolean;
  slow_mode_delay: number;
  has_hidden_members: boolean;
  restrict_saving_content: boolean;
  can_send_media: boolean;
  can_send_stickers: boolean;
  can_send_polls: boolean;
  can_invite_users: boolean;
  can_pin_messages: boolean;
  [key: string]: unknown;
}

const props = defineProps<{
  chatId: number;
  chatType: "group" | "private";
  chatName?: string;
  chatAvatar?: string;
  isAdmin?: boolean;
  isOwner?: boolean;
}>();
const isSiteAdmin = computed(() => !!useAuthStore().user?.is_staff);

const emit = defineEmits<{
  close: [];
  "settings-saved": [payload: Record<string, unknown>];
}>();

const loading = ref(true);
const saving = ref(false);
const activeSection = ref("wallpaper");
const toast = ref({ show: false, message: "", type: "success" });
const hasCustomWallpaper = ref(false);
const currentPresetId = ref<string | null>(null);
const currentMuteDuration = ref<number | null>(null);
const transferLoading = ref(false);
const groupChatStore = useGroupChatStore();
const members = ref<Array<{
  user: { id: number; username: string; display_name?: string; avatar?: string | null; avatar_url?: string | null; is_online?: boolean };
  role: { id: number; name: string; level: number; color: string } | null;
  is_admin: boolean;
  is_owner: boolean;
  custom_title: string;
}>>([]);
const chatRoles = ref<Array<{ id: number; name: string; level: number; color: string }>>([]);
const loadingMembers = ref(false);

const chat = computed(() => groupChatStore.allGroupChats.find(c => c.id === props.chatId));
const discussionType = computed(() => chat.value?.discussion_type || '');
const showAvatarSection = computed(() => activeSection.value === 'avatar' && discussionType.value !== 'anime' && discussionType.value !== 'franchise');

async function transferOwnership(userId: number) {
  transferLoading.value = true;
  try {
    await rolesApi.transferOwnership(props.chatId, userId);
    showToast("Права владения переданы", "success");
    await loadMembers();
    emit("settings-saved", { type: "transfer-ownership" });
  } catch (error) {
    console.error("Error transferring ownership:", error);
    showToast("Ошибка при передаче прав", "error");
  } finally {
    transferLoading.value = false;
  }
}

const wallpaperFileRef = ref<HTMLInputElement | null>(null);
const wallpaperImagePreview = ref<string | null>(null);
const wallpaperImageFile = ref<File | null>(null);

const avatarPreview = ref<string | null>(null);
const avatarFile = ref<File | null>(null);
const groupInfo = ref({ name: props.chatName || '', description: '' });

async function saveGroupInfo() {
  if (!groupInfo.value.name.trim()) { showToast('Введите название группы', 'error'); return; }
  saving.value = true;
  try {
    await groupChatStore.updateGroupChat(props.chatId, { name: groupInfo.value.name.trim(), description: groupInfo.value.description });
    await groupChatStore.loadGroupChats();
    emit('settings-saved', { type: 'group-info' });
    showToast('Название и описание сохранены');
  } catch (err) { showToast(errorText(err, 'Не удалось сохранить группу'), 'error'); }
  finally { saving.value = false; }
}

const themePresets = ref<Record<string, unknown>[]>([]);
const chatFolders = ref<Record<string, unknown>[]>([]);

const wallpaperForm = ref({
  wallpaper_type: "solid",
  wallpaper_color: "#0f0f1a",
  wallpaper_color2: "#1a1a2e",
  wallpaper_intensity: 100,
  wallpaper_blur: 0,
  wallpaper_motion: "none",
  wallpaper_image_url: undefined,
  gradient_angle: 135,
  pattern_type: "dots",
  pattern_color: "#3b82f6",
  pattern_opacity: 15,
});

const themeForm = ref<ThemeForm>({
  theme: "default",
  message_color_mine: "#3b82f6",
  message_color_other: "#1e1e32",
  message_text_color_mine: "#ffffff",
  message_text_color_other: "#e2e8f0",
  bubble_style: "modern",
  bubble_border_radius: 18,
  bubble_shadow: false,
  font_family: "system",
  font_size: "medium",
  font_size_px: 14,
  font_weight: 400,
  line_height: 1.5,
  time_format: "24h",
  time_color: "rgba(255,255,255,0.5)",
  background_color: "#0f0f1a",
  header_color: "#1a1a2e",
  input_color: "#1e1e32",
  input_text_color: "#e2e8f0",
  accent_color: "#3b82f6",
  link_color: "#60a5fa",
  message_animation: "slide",
  reaction_animation: "bounce",
  typing_animation: "dots",
  emoji_set: "default",
  emoji_size: "medium",
  show_avatars: true,
  show_usernames: true,
  compact_mode: false,
  show_read_status: true,
  show_typing_indicator: true,
  message_grouping: true,
  custom_css: "",
  anime_card_border_radius: 12,
  playlist_card_border_radius: 12,
});

const notifForm = ref({
  notifications_enabled: true,
  mentions_only: false,
  sound_enabled: true,
  notification_sound: "default",
  vibration_enabled: true,
  vibration_type: "default",
  show_preview: true,
  show_popup: true,
  muted_until: null as string | null,
});

const organizeForm = ref({
  is_pinned: false,
  is_archived: false,
  is_hidden: false,
  custom_name: "",
  folder_id: null as number | null,
  auto_delete_enabled: false,
  auto_delete_after: 30,
});

const privacyForm = ref({ is_blocked: false });

const groupSettings = ref<GroupSettingsForm>({
  slow_mode_enabled: false,
  slow_mode_delay: 30,
  has_hidden_members: false,
  restrict_saving_content: false,
  can_send_media: true,
  can_send_stickers: true,
  can_send_polls: true,
  can_invite_users: true,
  can_pin_messages: true,
});

interface NavSection {
  id: string;
  name: string;
  icon: string;
  desc: string;
}

const navGroups = computed(() => {
  const appearance: NavSection[] = [
    { id: "wallpaper", name: "Обои", icon: "image", desc: "Фон чата" },
    { id: "theme", name: "Тема и стиль", icon: "palette", desc: "Цвета, сообщения, текст" },
  ];

if (props.chatType === "group" && (props.isAdmin || props.isOwner) && discussionType.value !== 'anime' && discussionType.value !== 'franchise') {
     appearance.push({ id: "avatar", name: "Группа", icon: "camera", desc: "Название, описание и фото" });
   }

  const manage: NavSection[] = [];
  manage.push({ id: 'notifications', name: 'Уведомления', icon: 'bell', desc: 'Включение и отключение' },
    { id: 'organize', name: 'Организация', icon: 'folder', desc: 'Закрепление и архив' });

  if (props.chatType === "group") {
    manage.push({ id: "participation", name: "Участие", icon: "users", desc: "Действия с группой" });
    /* Temporarily disabled: advanced group settings.
    if (props.isAdmin || props.isOwner || isSiteAdmin.value) manage.push(
      { id: 'moderation', name: 'Модерация', icon: 'lock', desc: 'Права и медленный режим' },
      { id: 'backups', name: 'Резервные копии', icon: 'folder', desc: 'Архив и восстановление' });
    */
  }
  if (props.chatType === "private") {
    manage.push({ id: "security", name: "Безопасность", icon: "lock", desc: "Блокировка, очистка, удаление" });
  }

  const groups: Array<{ title: string; items: NavSection[] }> = [
    { title: "Оформление", items: appearance },
  ];
  if (manage.length > 0) groups.push({ title: "Управление", items: manage });
  return groups;
});

const flatSections = computed(() => navGroups.value.flatMap((g) => g.items));

const contentEl = ref<HTMLElement | null>(null);
const navItemEls = ref<Record<string, HTMLElement | null>>({});
const setNavItemRef = (id: string) => (el: unknown) => {
  navItemEls.value[id] = (el as HTMLElement | null) ?? null;
};

function setSection(id: string) {
  if (activeSection.value === id) return;
  activeSection.value = id;
  nextTick(() => {
    if (contentEl.value) contentEl.value.scrollTo({ top: 0, behavior: "auto" });
  });
}

function onNavKeydown(e: KeyboardEvent) {
  if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
  e.preventDefault();
  const ids = flatSections.value.map((s) => s.id);
  const idx = ids.indexOf(activeSection.value);
  const next =
    e.key === "ArrowDown"
      ? Math.min(idx + 1, ids.length - 1)
      : Math.max(idx - 1, 0);
  if (!ids[next]) return;
  const nextId = ids[next]!;
  setSection(nextId);
  nextTick(() => navItemEls.value[nextId]?.focus());
}

const apiBase = computed(
  () => `/social/chat-settings/${props.chatType}/${props.chatId}`,
);

const bubbleRadiusVal = computed(() => themeForm.value.bubble_border_radius);

const fontFamilyCSS = computed(() => {
  const map: Record<string, string> = {
    system: "system-ui,-apple-system,sans-serif",
    inter: "Inter,sans-serif",
    roboto: "Roboto,sans-serif",
    nunito: "Nunito,sans-serif",
    montserrat: "Montserrat,sans-serif",
    opensans: '"Open Sans",sans-serif',
  };
  return map[themeForm.value.font_family] || "system-ui";
});

const mineBubbleStyle = computed(() => ({
  background: themeForm.value.message_color_mine,
  color: themeForm.value.message_text_color_mine,
  borderRadius: bubbleRadiusVal.value + "px",
  fontFamily: fontFamilyCSS.value,
  fontSize: themeForm.value.font_size_px + "px",
  padding: "6px 12px",
  display: "inline-block",
  maxWidth: "80%",
}));

const otherBubbleStyle = computed(() => ({
  background: themeForm.value.message_color_other,
  color: themeForm.value.message_text_color_other,
  borderRadius: bubbleRadiusVal.value + "px",
  fontFamily: fontFamilyCSS.value,
  fontSize: themeForm.value.font_size_px + "px",
  padding: "6px 12px",
  display: "inline-block",
  maxWidth: "80%",
}));

const wallpaperTypeOptions = [
  { value: "solid", label: "Цвет" },
  { value: "image", label: "Картинка" },
];

const solidColorPresets = [
  "#0f0f1a",
  "#1a1a2e",
  "#1c1c1c",
  "#0f172a",
  "#1e1b4b",
  "#14532d",
  "#7f1d1d",
  "#1e3a5f",
  "#2d1b69",
  "#000000",
];

const bubbleStyles = [
  { value: "modern", label: "Модерн", defaultRadius: 18 },
  { value: "classic", label: "Классика", defaultRadius: 4 },
  { value: "rounded", label: "Округлый", defaultRadius: 24 },
  { value: "flat", label: "Плоский", defaultRadius: 8 },
  { value: "minimal", label: "Минимал", defaultRadius: 2 },
];

const fontFamilies = [
  { value: "system", label: "Системный" },
  { value: "inter", label: "Inter" },
  { value: "roboto", label: "Roboto" },
  { value: "nunito", label: "Nunito" },
  { value: "montserrat", label: "Montserrat" },
];

const fontSizes = [
  { value: "small", label: "Маленький", px: 12 },
  { value: "medium", label: "Средний", px: 14 },
  { value: "large", label: "Большой", px: 16 },
];

const interfaceColors = [
  { key: "background_color", label: "Фон чата" },
  { key: "header_color", label: "Шапка" },
  { key: "input_color", label: "Поле ввода" },
];

const themeToggles = [
  { key: "show_avatars", label: "Аватарки", desc: "" },
  { key: "show_usernames", label: "Имена участников", desc: "" },
];

const muteOptions = [
  { label: "15 мин", value: 15 },
  { label: "1 час", value: 60 },
  { label: "8 часов", value: 480 },
  { label: "2 дня", value: 2880 },
  { label: "1 неделя", value: 10080 },
  { label: "Навсегда", value: 0 },
];

const contentPermissions = [
  { key: "can_send_media", label: "Медиафайлы" },
  { key: "can_send_stickers", label: "Стикеры и GIF" },
  { key: "can_send_polls", label: "Опросы" },
  { key: "can_invite_users", label: "Приглашения" },
  { key: "can_pin_messages", label: "Закрепление сообщений" },
];

async function loadSettings() {
  loading.value = true;
  try {
    const [allRes, themePresetsRes, foldersRes] = await Promise.allSettled([
      apiClient.get(`${apiBase.value}/all/`),
      apiClient.get("/social/chat-settings/themes/presets/"),
      apiClient.get("/social/chat-folders/"),
    ]);

    if (allRes.status === "fulfilled") {
      const d = allRes.value.data;
      if (d.wallpaper) {
        hasCustomWallpaper.value = true;
        Object.assign(wallpaperForm.value, d.wallpaper);
      }
      if (d.theme) Object.assign(themeForm.value, d.theme);
    }
    if (themePresetsRes.status === "fulfilled")
      themePresets.value = themePresetsRes.value.data.presets || [];
    if (foldersRes.status === "fulfilled") {
      chatFolders.value =
        foldersRes.value.data.results || foldersRes.value.data || [];
    }

    await loadNotifSettings();
    if (props.chatType === "group") {
      const info = await apiClient.get(`/social/group-chats/${props.chatId}/`);
      groupInfo.value = { name: info.data.name || '', description: info.data.description || '' };
      const response = await apiClient.get(`/social/group-chats/${props.chatId}/settings/`);
      Object.assign(groupSettings.value, response.data);
      await loadMembers();
    }
  } catch {
    showToast('Не удалось загрузить все настройки', 'error');
  } finally {
    loading.value = false;
  }
}

async function exportPersonalSettings() {
  saving.value = true;
  try {
    const { data } = await apiClient.get('/social/settings/export/');
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'chat-settings.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  } catch { showToast('Не удалось экспортировать настройки', 'error'); }
  finally { saving.value = false; }
}
async function importPersonalSettings(event: Event) {
  const input = event.target as HTMLInputElement, file = input.files?.[0];
  if (!file) return;
  saving.value = true;
  try {
    if (file.size > 30 * 1024 * 1024) throw new Error('Слишком большой файл');
    await apiClient.post('/social/settings/import/', JSON.parse(await file.text()));
    await loadSettings();
    showToast('Настройки импортированы');
    emit('settings-saved', { type: 'import' });
  } catch { showToast('Не удалось импортировать настройки. Проверьте файл и доступ к чатам.', 'error'); }
  finally { saving.value = false; input.value = ''; }
}

async function loadNotifSettings() {
  try {
    const url =
      props.chatType === "private"
        ? `/social/private-chats/${props.chatId}/settings/`
        : `/social/group-chats/${props.chatId}/notification-settings/`;
    const { data } = await apiClient.get(url);
    Object.assign(notifForm.value, {
      notifications_enabled: data.notifications_enabled ?? true,
      mentions_only: data.mentions_only ?? false,
      sound_enabled: data.sound_enabled ?? true,
      notification_sound: data.notification_sound ?? "default",
      vibration_enabled: data.vibration_enabled ?? true,
      vibration_type: data.vibration_type ?? "default",
      show_preview: data.show_preview ?? true,
      show_popup: data.show_popup ?? true,
      muted_until: data.muted_until || null,
    });
    Object.assign(organizeForm.value, {
      is_pinned: data.is_pinned ?? false,
      is_archived: data.is_archived ?? false,
      is_hidden: data.is_hidden ?? false,
      custom_name: data.custom_name || "",
      folder_id: data.folder_id || null,
      auto_delete_enabled: data.auto_delete_enabled ?? false,
      auto_delete_after: data.auto_delete_after || 30,
    });
    privacyForm.value.is_blocked = data.is_blocked ?? false;
  } catch (err) {
    console.warn("loadNotifSettings failed:", err);
    showToast(
      errorText(err, "Не удалось загрузить настройки уведомлений"),
      "error",
    );
  }
}

/** Перечитать обои с сервера (после сброса/сохранения -не доверяем форме). */
async function reloadWallpaperFromServer() {
  try {
    const { data } = await apiClient.get(`${apiBase.value}/wallpaper/`);
    if (data?.wallpaper) {
      Object.assign(wallpaperForm.value, data.wallpaper);
    } else {
      Object.assign(wallpaperForm.value, {
        wallpaper_type: "solid",
        wallpaper_color: "#0f0f1a",
        wallpaper_color2: "#1a1a2e",
      });
    }
  } catch (err) {
    console.warn("reloadWallpaperFromServer failed:", err);
  }
}

async function saveWallpaper() {
  saving.value = true;
  try {
    let saved: Record<string, unknown> | null = null;
    if (
      wallpaperForm.value.wallpaper_type === "image" &&
      wallpaperImageFile.value
    ) {
      const fd = new FormData();
      fd.append("wallpaper_image", wallpaperImageFile.value);
      fd.append("wallpaper_blur", String(wallpaperForm.value.wallpaper_blur));
      fd.append(
        "wallpaper_intensity",
        String(wallpaperForm.value.wallpaper_intensity),
      );
      fd.append("wallpaper_type", "image");
      const res = await apiClient.post(`${apiBase.value}/wallpaper/set/`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      saved = res.data?.wallpaper || null;
    } else {
      const res = await apiClient.post(
        `${apiBase.value}/wallpaper/set/`,
        wallpaperForm.value,
      );
      saved = res.data?.wallpaper || null;
    }
    hasCustomWallpaper.value = true;
    wallpaperImageFile.value = null;
    if (saved) Object.assign(wallpaperForm.value, saved);
    showToast("Обои сохранены");
    emit("settings-saved", {
      type: "wallpaper",
      wallpaper: saved || { ...wallpaperForm.value },
    });
  } catch (err) {
    showToast(
      (err as { response?: { data?: { error?: string } } })?.response?.data
        ?.error || "Ошибка сохранения",
      "error",
    );
  } finally {
    saving.value = false;
  }
}

async function resetWallpaper() {
  try {
    await apiClient.delete(`${apiBase.value}/wallpaper/reset/`);
    hasCustomWallpaper.value = false;
    wallpaperImagePreview.value = null;
    Object.assign(wallpaperForm.value, {
      wallpaper_type: "solid",
      wallpaper_color: "#0f0f1a",
      wallpaper_color2: "#1a1a2e",
    });
    showToast("Обои сброшены");
    emit("settings-saved", { type: "wallpaper", reset: true });
    await reloadWallpaperFromServer();
  } catch (err) {
    showToast(errorText(err, "Не удалось сбросить обои"), "error");
  }
}

async function saveTheme() {
  saving.value = true;
  try {
    await apiClient.post(`${apiBase.value}/theme/set/`, themeForm.value);
    showToast("Тема сохранена");
    emit("settings-saved", { type: "theme", theme: { ...themeForm.value } });
    applyThemeToDom();
  } catch (err) {
    showToast(
      (err as { response?: { data?: { error?: string } } })?.response?.data
        ?.error || "Ошибка",
      "error",
    );
  } finally {
    saving.value = false;
  }
}

async function resetTheme() {
  try {
    await apiClient.delete(`${apiBase.value}/theme/reset/`);
    Object.assign(themeForm.value, {
      theme: "default",
      message_color_mine: "#3b82f6",
      message_color_other: "#1e1e32",
      message_text_color_mine: "#ffffff",
      message_text_color_other: "#e2e8f0",
      bubble_style: "modern",
      bubble_border_radius: 18,
      bubble_shadow: false,
      font_family: "system",
      font_size: "medium",
      font_size_px: 14,
      font_weight: 400,
      line_height: 1.5,
      time_format: "24h",
      time_color: "rgba(255,255,255,0.5)",
      background_color: "#0f0f1a",
      header_color: "#1a1a2e",
      input_color: "#1e1e32",
      input_text_color: "#e2e8f0",
      accent_color: "#3b82f6",
      link_color: "#60a5fa",
      message_animation: "slide",
      reaction_animation: "bounce",
      typing_animation: "dots",
      emoji_set: "default",
      emoji_size: "medium",
      show_avatars: true,
      show_usernames: true,
      compact_mode: false,
      show_read_status: true,
      show_typing_indicator: true,
      message_grouping: true,
      custom_css: "",
      anime_card_border_radius: 12,
      playlist_card_border_radius: 12,
    });
    currentPresetId.value = null;
    showToast("Тема сброшена");
    emit("settings-saved", { type: "theme", reset: true });
  } catch (err) {
    showToast(errorText(err, "Не удалось сбросить тему"), "error");
  }
}

function applyThemePreset(preset: Record<string, unknown>) {
  currentPresetId.value = preset.id as string | null;
  const fields = Object.keys(themeForm.value);
  fields.forEach((f) => {
    if (f in preset) themeForm.value[f] = preset[f];
  });
  saveTheme();
}

function applyThemeToDom() {
  const root = document.documentElement;
  const t = themeForm.value;
  root.style.setProperty("--chat-msg-mine-bg", t.message_color_mine);
  root.style.setProperty("--chat-msg-other-bg", t.message_color_other);
  root.style.setProperty("--chat-msg-mine-text", t.message_text_color_mine);
  root.style.setProperty("--chat-msg-other-text", t.message_text_color_other);
  root.style.setProperty("--chat-bg", t.background_color);
  root.style.setProperty("--chat-header-bg", t.header_color);
  root.style.setProperty("--chat-input-bg", t.input_color);
  root.style.setProperty("--chat-accent", t.accent_color);
  root.style.setProperty("--chat-font-size", t.font_size_px + "px");
  root.style.setProperty("--chat-font-family", fontFamilyCSS.value);
  root.style.setProperty("--chat-font-weight", String(t.font_weight));
  root.style.setProperty("--chat-bubble-radius", bubbleRadiusVal.value + "px");
  root.style.setProperty(
    "--chat-bubble-shadow",
    t.bubble_shadow ? "0 2px 8px rgba(0,0,0,0.3)" : "none",
  );
  root.style.setProperty("--chat-anime-card-radius", t.anime_card_border_radius + "px");
  root.style.setProperty("--chat-playlist-card-radius", t.playlist_card_border_radius + "px");
}

async function saveNotifSettings() {
  saving.value = true;
  try {
    const url =
      props.chatType === "private"
        ? `/social/private-chats/${props.chatId}/user-settings/`
        : `/social/group-chats/${props.chatId}/member-settings/`;
    await apiClient.put(url, { notifications_enabled: notifForm.value.notifications_enabled, muted_until: null });
    showToast("Уведомления сохранены");
    await loadNotifSettings();
  } catch (err) {
    showToast(errorText(err, "Не удалось сохранить уведомления"), "error");
  } finally {
    saving.value = false;
  }
}

async function muteChat(minutes: number) {
  try {
    const url =
      props.chatType === "private"
        ? `/social/private-chats/${props.chatId}/mute/`
        : `/social/group-chats/${props.chatId}/mute/`;
    await apiClient.post(url, { duration: minutes || null });
    currentMuteDuration.value = minutes;
    if (minutes === 0) {
      notifForm.value.notifications_enabled = false;
      notifForm.value.muted_until = null;
    } else {
      notifForm.value.muted_until = new Date(
        Date.now() + minutes * 60000,
      ).toISOString();
    }
    showToast("Чат заглушен");
    await loadNotifSettings();
  } catch (err) {
    showToast(errorText(err, "Не удалось заглушить чат"), "error");
  }
}

async function unmuteChat() {
  try {
    if (props.chatType === "private") {
      await apiClient.post(`/social/private-chats/${props.chatId}/unmute/`);
    } else {
      await apiClient.post(`/social/group-chats/${props.chatId}/unmute/`);
    }
    notifForm.value.muted_until = null;
    notifForm.value.notifications_enabled = true;
    currentMuteDuration.value = null;
    showToast("Уведомления включены");
    await loadNotifSettings();
  } catch (err) {
    showToast(errorText(err, "Не удалось включить уведомления"), "error");
  }
}

async function saveOrganizeSettings() {
  try {
    if (props.chatType === "private") {
      await apiClient.put(
        `/social/private-chats/${props.chatId}/settings/`,
        organizeForm.value,
      );
    } else {
      const tasks: Promise<unknown>[] = [];

      if ("is_archived" in organizeForm.value) {
        tasks.push(
          apiClient.post(`/social/group-chats/${props.chatId}/archive/`, {
            is_archived: organizeForm.value.is_archived,
          }),
        );
      }

      const memberSettings: Record<string, unknown> = {};
      if ("is_pinned" in organizeForm.value)
        memberSettings.is_pinned = organizeForm.value.is_pinned;
      if ("tags" in organizeForm.value)
        memberSettings.tags = organizeForm.value.tags;
      if (Object.keys(memberSettings).length > 0) {
        tasks.push(
          apiClient.put(
            `/social/group-chats/${props.chatId}/member-settings/`,
            memberSettings,
          ),
        );
      }

      await Promise.all(tasks);
    }

    showToast("Сохранено");
    emit("settings-saved", { type: "organize", ...organizeForm.value });
    await loadNotifSettings();
    window.dispatchEvent(new CustomEvent("chat-settings-updated"));
  } catch (err) {
    showToast(errorText(err, "Не удалось сохранить"), "error");
  }
}

async function blockUser() {
  if (!confirm("Заблокировать пользователя?")) return;
  try {
    await apiClient.post(`/social/private-chats/${props.chatId}/block/`);
    privacyForm.value.is_blocked = true;
    emit("settings-saved", { type: "block" });
    showToast("Пользователь заблокирован");
    await loadNotifSettings();
  } catch (err) {
    showToast(errorText(err, "Не удалось заблокировать"), "error");
  }
}

async function unblockUser() {
  try {
    await apiClient.post(`/social/private-chats/${props.chatId}/unblock/`);
    privacyForm.value.is_blocked = false;
    emit("settings-saved", { type: "unblock" });
    showToast("Пользователь разблокирован");
    await loadNotifSettings();
  } catch (err) {
    showToast(errorText(err, "Не удалось разблокировать"), "error");
  }
}

async function clearHistory() {
  if (!confirm("Очистить историю? Это действие необратимо.")) return;
  try {
    await apiClient.post(
      `/social/chats/${props.chatId}/clear-history/?type=${props.chatType}`,
    );
    showToast("История очищена");
  } catch (err) {
    showToast(errorText(err, "Не удалось очистить историю"), "error");
  }
}

async function deleteChat() {
  if (!confirm("Удалить чат? Это действие необратимо!")) return;
  try {
    if (props.chatType === "private") {
      await apiClient.delete(`/social/private-chats/${props.chatId}/`);
    } else {
      await apiClient.delete(`/social/group-chats/${props.chatId}/`);
      groupChatStore.removeGroupChatFromList(props.chatId);
    }
    showToast("Чат удалён");
    emit("close");
    emit("settings-saved", { type: "delete" });
  } catch (err) {
    showToast(errorText(err, "Не удалось удалить чат"), "error");
  }
}

async function leaveGroup() {
  if (!confirm("Выйти из этой группы? Вы больше не сможете видеть сообщения."))
    return;

  const removeMissingGroupLocally = () => {
    groupChatStore.removeGroupChatFromList(props.chatId);
    emit("close");
    emit("settings-saved", { type: "leave" });
  };

  try {
    await apiClient.post(
      `/social/group-chats/${props.chatId}/leave_group_chat/`,
    );
    removeMissingGroupLocally();
    showToast("Вы покинули группу", "success");
  } catch (err) {
    const status = (err as { response?: { status?: number } })?.response?.status;
    if (status === 404 || status === 410) {
      removeMissingGroupLocally();
      showToast("Группа удалена из списка чатов", "success");
      return;
    }
    showToast(errorText(err, "Не удалось выйти из группы"), "error");
  }
}

async function saveGroupSettings() {
  try {
    const response = await apiClient.put(
      `/social/group-chats/${props.chatId}/settings/`,
      groupSettings.value,
    );
    Object.assign(groupSettings.value, response.data);
    emit("settings-saved", { type: "group" });
    showToast("Настройки сохранены");
  } catch (err) {
    showToast(errorText(err, "Не удалось сохранить настройки группы"), "error");
  }
}

async function loadMembers() {
  if (props.chatType !== "group") return;
  loadingMembers.value = true;
  try {
    await Promise.all([
      groupChatStore.loadChatMembers(props.chatId),
      groupChatStore.loadChatRoles(props.chatId),
    ]);
    members.value = groupChatStore.chatMembers.map((m) => ({
      user: {
        id: m.user.id,
        username: m.user.username,
        display_name:
          [m.user.first_name, m.user.last_name].filter(Boolean).join(" ") ||
          m.user.username,
        avatar: m.user.avatar,
        avatar_url: m.user.avatar_url,
        is_online: m.user.status?.status === "online",
      },
      role: m.role
        ? {
            id: m.role.id,
            name: m.role.name,
            level: m.role.level,
            color: m.role.color,
          }
        : null,
      is_admin: m.is_admin,
      is_owner: m.is_owner,
      custom_title: m.custom_title,
    }));
    chatRoles.value = groupChatStore.chatRoles.map((r) => ({
      id: r.id,
      name: r.name,
      level: r.level,
      color: r.color,
    }));
  } catch (err) {
    console.warn("Error loading members:", err);
    showToast(errorText(err, "Не удалось загрузить участников"), "error");
  } finally {
    loadingMembers.value = false;
  }
}

function canManageMember(member: (typeof members.value)[0]): boolean {
  if (member.is_owner) return false;
  if (props.isOwner || props.isAdmin) return true;
  return false;
}

function memberStatusValue(member: (typeof members.value)[0]): string {
  if (member.is_owner) return "owner";
  if (member.is_admin) return "admin";
  return "participant";
}

async function onMemberStatusChange(member: (typeof members.value)[0], status: string) {
  if (status === "owner") {
    if (!confirm(`Передать права владения ${member.user.display_name}?`)) {
      await loadMembers();
      return;
    }
    await transferOwnership(member.user.id);
  } else {
    const isAdmin = status === "admin";
    await updateMemberRole(member.user.id, null, isAdmin);
  }
}

async function updateMemberRole(userId: number, roleId: number | null, isAdmin?: boolean) {
  try {
    await rolesApi.setMemberRole(props.chatId, userId, roleId, isAdmin);
    showToast("Роль обновлена", "success");
    await loadMembers();
  } catch (err) {
    showToast(errorText(err, "Не удалось изменить роль"), "error");
  }
}

async function removeMember(userId: number) {
  if (!confirm("Удалить участника из чата?")) return;
  try {
    await rolesApi.removeMember(props.chatId, userId);
    showToast("Участник удалён", "success");
    await loadMembers();
  } catch (err) {
    showToast(errorText(err, "Не удалось удалить участника"), "error");
  }
}

async function banMember(userId: number) {
  if (!confirm("Забанить пользователя?")) return;
  try {
    await rolesApi.banUser(props.chatId, userId);
    showToast("Пользователь забанен", "success");
    await loadMembers();
  } catch (err) {
    showToast(errorText(err, "Не удалось забанить"), "error");
  }
}

const addUserQuery = ref("");
const userSearchResults = ref<
  Array<{ id: number; username: string; display_name?: string; avatar?: string; avatar_url?: string }>
>([]);
const searchingUsers = ref(false);
const userSearchIndex = ref(0);
let userSearchTimeout: ReturnType<typeof setTimeout> | null = null;

const addedUserIds = computed(() => new Set(members.value.map((m) => m.user.id)));

const userSearchPlaceholder = computed(() => (addUserQuery.value ? "" : "Поиск пользователей..."));

async function onSearchUsers() {
  if (userSearchTimeout) clearTimeout(userSearchTimeout);
  const query = addUserQuery.value.trim();
  if (!query) {
    userSearchResults.value = [];
    searchingUsers.value = false;
    userSearchIndex.value = 0;
    return;
  }
  searchingUsers.value = true;
  userSearchIndex.value = 0;
  userSearchTimeout = setTimeout(async () => {
    try {
      const response = await apiClient.get("/users/search/", {
        params: { q: query },
      });
      const results = (response.data.results || response.data || []) as Array<{
        id: number;
        username: string;
        display_name?: string;
        avatar?: string;
        avatar_url?: string;
      }>;
      userSearchResults.value = results.filter((u) => !addedUserIds.value.has(u.id));
    } catch (err) {
      console.warn("user search failed:", err);
      userSearchResults.value = [];
    } finally {
      searchingUsers.value = false;
    }
  }, 250);
}

function onSearchKeydown(e: KeyboardEvent) {
  if (!userSearchResults.value.length) return;
  if (e.key === "ArrowDown") {
    e.preventDefault();
    userSearchIndex.value = (userSearchIndex.value + 1) % userSearchResults.value.length;
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    userSearchIndex.value =
      (userSearchIndex.value - 1 + userSearchResults.value.length) % userSearchResults.value.length;
  } else if (e.key === "Enter") {
    e.preventDefault();
    const user = userSearchResults.value[userSearchIndex.value];
    if (user) addUser(user);
  }
}

function onSearchFocus() {
  if (addUserQuery.value.trim() && userSearchResults.value.length) {
    userSearchIndex.value = 0;
  }
}

function onSearchBlur() {
  userSearchIndex.value = 0;
}

async function addUser(
  user: { id: number; username: string; display_name?: string; avatar?: string; avatar_url?: string },
) {
  try {
    await rolesApi.addMembers(props.chatId, [user.id]);
    showToast(`Пользователь ${user.display_name || user.username} добавлен`, "success");
    addUserQuery.value = "";
    userSearchResults.value = [];
    userSearchIndex.value = 0;
    await loadMembers();
  } catch (err) {
    showToast(errorText(err, "Не удалось добавить участников"), "error");
  }
}

function handleWallpaperFile(file: File) {
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    showToast("Файл слишком большой (максимум 5MB)", "error");
    return;
  }
  wallpaperImageFile.value = file;
  wallpaperImagePreview.value = URL.createObjectURL(file);
}

function clearWallpaperImage() {
  wallpaperImageFile.value = null;
  wallpaperImagePreview.value = null;
  if (wallpaperFileRef.value) wallpaperFileRef.value.value = "";
}

function handleAvatarFile(file: File) {
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    showToast("Файл слишком большой (максимум 5MB)", "error");
    return;
  }
  avatarFile.value = file;
  const reader = new FileReader();
  reader.onload = () => {
    avatarPreview.value = reader.result as string;
  };
  reader.readAsDataURL(file);
}

function clearAvatar() {
  avatarFile.value = null;
  avatarPreview.value = null;
}

async function saveAvatar() {
  if (!avatarFile.value) return;

  saving.value = true;
  try {
    const fd = new FormData();
    fd.append("avatar", avatarFile.value);

    await apiClient.patch(`/social/group-chats/${props.chatId}/`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    showToast("Аватар обновлён", "success");
    emit("settings-saved", { type: "avatar" });

    clearAvatar();
  } catch (error) {
    console.error("Error saving avatar:", error);
    showToast("Ошибка при сохранении", "error");
  } finally {
    saving.value = false;
  }
}

function formatMuteDate(iso: string): string {
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDelay(seconds: number): string {
  if (seconds < 60) return `${seconds}с`;
  if (seconds < 3600) return `${seconds / 60}м`;
  return `${seconds / 3600}ч`;
}

let toastTimer: ReturnType<typeof setTimeout> | null = null;
/** Человекочитаемый текст ошибки DRF: error/detail/поля, иначе статус. */
function errorText(err: unknown, fallback: string): string {
  const resp = (err as { response?: { status?: number; data?: unknown } })?.response;
  const data = resp?.data;
  if (typeof data === "string" && data.trim()) return data;
  if (data && typeof data === "object") {
    const obj = data as Record<string, unknown>;
    for (const key of ["error", "detail", "message"]) {
      const value = obj[key];
      if (typeof value === "string" && value.trim()) return value;
    }
    const fieldErrors: string[] = [];
    for (const [field, value] of Object.entries(obj)) {
      if (Array.isArray(value) && value.length) {
        fieldErrors.push(`${field}: ${value.join(", ")}`);
      } else if (typeof value === "string" && value.trim()) {
        fieldErrors.push(`${field}: ${value}`);
      }
    }
    if (fieldErrors.length) return fieldErrors.join("; ");
  }
  if (resp?.status) return `${fallback} (HTTP ${resp.status})`;
  return (err as { message?: string })?.message || fallback;
}

function showToast(message: string, type: "success" | "error" = "success") {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { show: true, message, type };
  toastTimer = setTimeout(() => {
    toast.value.show = false;
  }, 3000);
}

onMounted(loadSettings);

onUnmounted(() => {
  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }
  if (userSearchTimeout) {
    clearTimeout(userSearchTimeout);
    userSearchTimeout = null;
  }
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: var(--viewport-top, 0px) 0 auto;
  height: var(--viewport-height, 100dvh);
  background: color-mix(in srgb, var(--surface-1) 88%, transparent);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: var(--space-4);
  animation: fadeIn var(--duration-base) var(--ease-out);
}

.chat-settings-modal {
  display: flex;
  width: min(960px, 95vw);
  height: min(720px, calc(var(--viewport-height, 100dvh) * .92));
  background: var(--surface-3);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--border-default);
  animation: scaleIn var(--duration-slow) var(--ease-spring);
}

.settings-sidebar {
  width: 240px;
  min-width: 240px;
  background: var(--surface-1);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
}

.sidebar-header {
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.chat-info-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
  flex: 1;
}

.chat-avatar-mini {
  width: 38px;
  height: 38px;
  border-radius: var(--radius-full);
  object-fit: cover;
  flex-shrink: 0;
  border: 2px solid var(--border-strong);
  transition: border-color var(--duration-base) var(--ease-out);
}

.chat-avatar-mini:hover {
  border-color: var(--accent);
}

.avatar-placeholder {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--text-lg);
  color: var(--text-on-accent);
  box-shadow: var(--shadow-petal-sm);
}

.chat-meta {
  min-width: 0;
  flex: 1;
}

.sidebar-overline {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--accent);
  opacity: 0.85;
  margin-bottom: 2px;
}

.chat-name-mini {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.3;
}
.chat-type-pill {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  background: var(--surface-4);
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  margin-top: var(--space-1);
  display: inline-block;
  font-weight: 500;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--text-xl);
  width: 32px;
  min-width: 32px;
  max-width: 32px;
  height: 32px;
  min-height: 32px;
  max-height: 32px;
  padding: 0;
  border-radius: 50%;
  transition: all var(--duration-base) var(--ease-out);
  flex-shrink: 0;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1 / 1;
  overflow: hidden;
}
.close-btn:hover {
  color: var(--accent);
  background: var(--surface-4);
}
.close-btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.sidebar-nav {
  padding: var(--space-3);
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sidebar-nav::-webkit-scrollbar {
  width: 4px;
}
.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--border-default);
  border-radius: var(--radius-full);
}

.nav-group-title {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--text-tertiary);
  padding: var(--space-3) var(--space-2) var(--space-1);
  user-select: none;
}
.nav-group-title:not(:first-child) {
  margin-top: var(--space-2);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-2) var(--space-2);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  transition:
    background var(--duration-base) var(--ease-out),
    color var(--duration-base) var(--ease-out);
  text-align: left;
  font-size: var(--text-base);
  font-weight: 500;
  position: relative;
  outline: none;
}

.nav-icon-chip {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 17px;
  flex-shrink: 0;
  transition:
    background var(--duration-base) var(--ease-petal),
    color var(--duration-base) var(--ease-petal),
    border-color var(--duration-base) var(--ease-petal),
    box-shadow var(--duration-base) var(--ease-petal),
    transform var(--duration-base) var(--ease-petal);
}

.nav-label {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.nav-name {
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color var(--duration-base) var(--ease-out);
}

.nav-item::after {
  content: "";
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%) scaleY(0);
  width: 3px;
  height: 55%;
  border-radius: var(--radius-full);
  background: linear-gradient(180deg, var(--accent), var(--accent-bright));
  box-shadow: var(--shadow-sm-glow-sm);
  transition: transform var(--duration-base) var(--ease-spring);
}

.nav-item:hover {
  color: var(--text-primary);
  background: var(--surface-4);
}
.nav-item:hover .nav-icon-chip {
  border-color: var(--border-default);
  color: var(--accent);
  transform: translateY(-1px);
}

.nav-item:focus-visible {
  box-shadow: 0 0 0 2px var(--accent-subtle);
}

.nav-item.active {
  color: var(--text-primary);
  font-weight: 600;
  background: var(--accent-subtle);
}
.nav-item.active .nav-icon-chip {
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  border-color: transparent;
  color: var(--text-on-accent);
  box-shadow: var(--shadow-sm-glow-sm);
  transform: scale(1.04);
}
.nav-item.active .nav-hint {
  color: var(--accent);
  opacity: 0.75;
}
.nav-item.active::after {
  transform: translateY(-50%) scaleY(1);
}

.sidebar-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  font-weight: 600;
  user-select: none;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  min-width: 0;
  scroll-behavior: smooth;
}

.settings-pane {
  max-width: 680px;
  margin: 0 auto;
  min-height: 100%;
}

.section-swap-enter-active {
  transition:
    opacity var(--duration-base) var(--ease-out),
    transform var(--duration-slow) var(--ease-out);
}
.section-swap-leave-active {
  transition:
    opacity 0.12s var(--ease-in, ease),
    transform 0.12s var(--ease-in, ease);
}
.section-swap-enter-from {
  opacity: 0;
  transform: translateY(14px) scale(0.995);
}
.section-swap-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: var(--space-4);
  color: var(--text-tertiary);
  font-size: var(--text-base);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--surface-4);
  border-top-color: var(--accent);
  border-radius: var(--radius-full);
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.settings-section {
  padding: var(--space-6);
  animation: slideUp var(--duration-slow) var(--ease-out) both;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-subtle);
}
.section-header h2 {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  letter-spacing: -0.01em;
}

.settings-group-card {
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  transition: border-color var(--duration-base) var(--ease-out);
}
.settings-group-card:hover {
  border-color: var(--border-default);
}
.sgc-title {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
  margin-bottom: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.danger-title {
  color: var(--danger);
}

.field-group {
  margin-bottom: var(--space-4);
}
.field-group:last-child {
  margin-bottom: 0;
}
.field-label {
  display: block;
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  font-weight: 500;
}
.field-hint {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-2);
  line-height: 1.5;
}
.mt-3 {
  margin-top: var(--space-3);
}

.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}

.color-row {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.color-picker-wide {
  width: 44px;
  height: 36px;
  padding: 3px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-4);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  flex-shrink: 0;
}
.color-picker-wide:hover {
  border-color: var(--accent);
  transform: scale(1.05);
}
.color-hex-input {
  flex: 1;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  transition: all var(--duration-base) var(--ease-out);
}
.color-hex-input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.color-swathes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-3);
}
.swatch {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  position: relative;
}
.swatch:hover {
  transform: scale(1.15);
  z-index: 1;
}
.swatch--active {
  border-color: var(--accent);
  transform: scale(1.15);
  box-shadow: var(--shadow-sm-glow-sm);
}

.range-slider {
  width: 100%;
  accent-color: var(--accent);
  cursor: pointer;
  height: 6px;
  border-radius: var(--radius-full);
  transition: accent-color var(--duration-base) var(--ease-out);
}

.type-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.type-tab {
  padding: var(--space-2) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.type-tab:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: var(--surface-5);
}
.type-tab.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
  box-shadow: var(--shadow-sm-glow-sm);
}

.wallpaper-preview {
  position: relative;
  min-height: 120px;
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  margin-bottom: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  overflow: hidden;
  transition: all var(--duration-slow) var(--ease-petal);
  border: 1px solid var(--border-subtle);
}
.wp-msg {
  display: flex;
}
.wp-msg--mine {
  justify-content: flex-end;
}
.wp-msg--other {
  justify-content: flex-start;
}
.wp-bubble {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  line-height: 1.4;
  border-radius: var(--radius-lg);
  max-width: 75%;
}

.avatar-preview-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-6) var(--space-4);
  margin-bottom: var(--space-4);
}

.avatar-preview-large {
  position: relative;
  width: 128px;
  height: 128px;
  border-radius: var(--radius-full);
  overflow: hidden;
  cursor: pointer;
  border: 3px solid var(--border-strong);
  box-shadow: var(--shadow-petal);
  transition: all var(--duration-base) var(--ease-petal);
}

.avatar-preview-large:hover {
  border-color: var(--accent);
  transform: scale(1.03);
  box-shadow: var(--shadow-glow);
}

.avatar-preview-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder-large {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, var(--accent), var(--accent-press));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-4xl);
  font-weight: 700;
  color: var(--text-on-accent);
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity var(--duration-base) var(--ease-petal);
}

.avatar-preview-large:hover .avatar-overlay {
  opacity: 1;
}

.avatar-overlay span {
  font-size: var(--text-3xl);
}

.angle-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-top: var(--space-3);
}
.angle-btn {
  padding: var(--space-1) var(--space-2);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.angle-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.angle-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.gradient-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.gradient-swatch {
  width: 52px;
  height: 36px;
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
}
.gradient-swatch:hover {
  transform: scale(1.1);
  border-color: rgba(255, 255, 255, 0.35);
  box-shadow: var(--shadow-sm-glow-sm);
}

.pattern-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.pattern-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.pattern-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.pattern-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.upload-zone {
  border: 2px dashed var(--border-default);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  overflow: hidden;
  min-height: 120px;
  position: relative;
}
.upload-zone:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
}
.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
  gap: var(--space-2);
  color: var(--text-tertiary);
}
.upload-icon-big {
  font-size: var(--text-3xl);
  opacity: 0.8;
}
.upload-hint {
  font-size: var(--text-xs);
}
.upload-preview {
  position: relative;
}
.upload-preview-img {
  width: 100%;
  max-height: 200px;
  object-fit: cover;
  display: block;
  border-radius: var(--radius-lg);
}
.clear-btn {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: white;
  border-radius: var(--radius-full);
  width: 28px;
  height: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-out);
}
.clear-btn:hover {
  background: var(--danger);
  border-color: var(--danger);
  transform: scale(1.1);
}

.wallpaper-presets-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-3);
}
.wp-preset {
  aspect-ratio: 16/9;
  border-radius: var(--radius-lg);
  border: 2px solid transparent;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all var(--duration-base) var(--ease-petal);
}
.wp-preset:hover {
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: var(--shadow-petal-sm);
}
.wp-preset-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.75));
  color: white;
  font-size: var(--text-xs);
  padding: var(--space-2) var(--space-2) var(--space-1);
  text-align: center;
  font-weight: 500;
  letter-spacing: 0.01em;
}

.theme-preview-wrap {
  margin-bottom: var(--space-5);
}
.theme-preview-chat {
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
  transition: all var(--duration-slow) var(--ease-petal);
  background: var(--preview-bg, var(--surface-2));
  --bubble-radius: 10px;
  --bubble-font-family: system-ui;
  --bubble-font-size: 13px;
  --bubble-shadow: none;
}
.theme-preview-chat .tp-header {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-primary);
  transition: background var(--duration-slow) var(--ease-petal);
  background: var(--preview-header, var(--surface-4));
}
.theme-preview-chat .tp-input {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  border-top: 1px solid var(--border-subtle);
  transition: background var(--duration-slow) var(--ease-petal);
  background: var(--preview-input, var(--surface-4));
}
.tp-input-placeholder {
  color: var(--preview-input-text, var(--text-secondary));
  opacity: 0.5;
  font-size: var(--text-sm);
}
.tp-messages {
  padding: var(--space-2);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.tp-row {
  display: flex;
}
.tp-row--mine {
  justify-content: flex-end;
}
.tp-row--other {
  justify-content: flex-start;
}
.tp-bubble {
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  line-height: 1.4;
  max-width: 70%;
  border-radius: var(--bubble-radius);
  font-family: var(--bubble-font-family);
  font-size: var(--bubble-font-size);
  box-shadow: var(--bubble-shadow);
  display: inline-block;
}
.tp-bubble-mine {
  background: var(--bubble-mine-bg, var(--accent-subtle));
  color: var(--bubble-mine-text, var(--text-primary));
}
.tp-bubble-other {
  background: var(--bubble-other-bg, var(--surface-4));
  color: var(--bubble-other-text, var(--text-secondary));
}

.theme-presets-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-3);
}
.theme-preset-btn {
  background: var(--surface-4);
  border: 2px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-3) var(--space-2);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
}
.theme-preset-btn:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-petal-sm);
}
.theme-preset-btn.active {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow-sm);
}
.tpb-preview {
  width: 100%;
  height: 36px;
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  gap: 2px;
}
.tpb-mine,
.tpb-other {
  flex: 1;
  height: 100%;
}
.tpb-mine {
  background: var(--preset-mine, var(--accent-subtle));
}
.tpb-other {
  background: var(--preset-other, var(--surface-4));
}
.tpb-bg {
  width: 24px;
  flex-shrink: 0;
  background: var(--preset-bg, #0f0f1a);
}
.tpb-name {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  text-align: center;
  font-weight: 500;
}

.bubble-style-picker {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}
.bsp-item {
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  min-width: 80px;
  transition: all var(--duration-base) var(--ease-petal);
}
.bsp-item:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}
.bsp-item.active {
  border-color: var(--accent);
  background: var(--accent-subtle);
  box-shadow: var(--shadow-sm-glow-sm);
}
.bsp-demo {
  width: 52px;
  height: 24px;
  background: var(--accent);
  border-radius: var(--bubble-radius, 10px);
  transition: border-radius var(--duration-base) var(--ease-petal);
}
.bsp-item span {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  font-weight: 500;
}
.bsp-modern {
  --bubble-radius: 18px;
}
.bsp-classic {
  --bubble-radius: 4px;
}
.bsp-rounded {
  --bubble-radius: 24px;
}
.bsp-flat {
  --bubble-radius: 8px;
}
.bsp-minimal {
  --bubble-radius: 2px;
}

.ff-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-size: var(--text-sm);
  font-weight: 500;
}
.ff-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  background: var(--surface-5);
}
.ff-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.font-size-picker {
  display: flex;
  gap: var(--space-2);
}
.fs-btn {
  padding: var(--space-2) var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.fs-small {
  font-size: var(--text-sm);
}
.fs-medium {
  font-size: var(--text-base);
}
.fs-large {
  font-size: var(--text-lg);
}
.fs-xlarge {
  font-size: var(--text-xl);
}
.fs-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.fs-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.interface-colors-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-4);
}
.ic-field .field-label {
  font-size: var(--text-xs);
}

.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-subtle);
  transition: background var(--duration-base) var(--ease-out);
}
.toggle-row:hover {
  background: var(--surface-4);
  margin: 0 calc(-1 * var(--space-4));
  padding-left: var(--space-4);
  padding-right: var(--space-4);
  border-radius: var(--radius-md);
}
.toggle-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.toggle-row:first-child {
  padding-top: 0;
}
.tr-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  min-width: 0;
}
.tr-label {
  font-size: var(--text-base);
  color: var(--text-primary);
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.tr-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.5;
}

.switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  cursor: pointer;
}
.switch input {
  position: absolute;
  opacity: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
  cursor: pointer;
  margin: 0;
}
.switch-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--surface-5);
  border-radius: 24px;
  transition: all var(--duration-base) var(--ease-petal);
  pointer-events: none;
  border: 1px solid var(--border-default);
}
.switch-slider::before {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: all var(--duration-base) var(--ease-petal);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
}
.switch input:checked + .switch-slider {
  background: var(--accent);
  border-color: var(--accent);
}
.switch input:checked + .switch-slider::before {
  transform: translateX(20px);
}
.switch:hover .switch-slider {
  background: var(--surface-4);
}
.switch input:checked:hover + .switch-slider {
  background: var(--accent-press);
  border-color: var(--accent-press);
}

.css-textarea {
  width: 100%;
  background: var(--surface-1);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  resize: vertical;
  min-height: 100px;
  box-sizing: border-box;
  transition: all var(--duration-base) var(--ease-out);
  line-height: 1.6;
}
.css-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.select-field {
  width: 100%;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--text-base);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-out);
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236d607a' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-3) center;
  padding-right: var(--space-8);
}
.select-field:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}
.select-field option {
  background: var(--surface-4);
  color: var(--text-primary);
}

.text-field {
  width: 100%;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-3);
  color: var(--text-primary);
  font-size: var(--text-base);
  box-sizing: border-box;
  transition: all var(--duration-base) var(--ease-out);
}
.text-field:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}

.mute-grid {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
.mute-btn {
  padding: var(--space-2) var(--space-4);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.mute-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
  transform: translateY(-1px);
}
.mute-btn.active {
  background: var(--accent-subtle);
  border-color: var(--accent);
  color: var(--accent);
  font-weight: 600;
  box-shadow: var(--shadow-sm-glow-sm);
}
.mute-status {
  margin-top: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  padding: var(--space-3);
  background: var(--surface-4);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
}
.btn-link {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: var(--text-sm);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
  transition: all var(--duration-base) var(--ease-out);
  font-weight: 500;
}
.btn-link:hover {
  color: var(--accent-press);
  background: var(--accent-subtle);
}

.slow-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-1);
  margin-top: var(--space-3);
}
.slow-preset-btn {
  padding: var(--space-1) var(--space-2);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.slow-preset-btn:hover {
  border-color: var(--accent);
  color: var(--text-primary);
}
.slow-preset-btn.active {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.danger-card {
  border-color: color-mix(in srgb, var(--danger) 30%, transparent);
  background: linear-gradient(135deg, var(--surface-3), color-mix(in srgb, var(--danger) 5%, var(--surface-3)));
}
.danger-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.danger-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-subtle);
  gap: var(--space-4);
}
.danger-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.dr-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
  min-width: 0;
}
.dr-title {
  font-size: var(--text-base);
  color: var(--text-primary);
  font-weight: 500;
}
.dr-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  line-height: 1.5;
}
.danger-btn {
  padding: var(--space-2) var(--space-4);
  background: color-mix(in srgb, var(--danger) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--danger) 35%, transparent);
  color: var(--danger);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-petal);
  white-space: nowrap;
  font-weight: 500;
}
.danger-btn:hover {
  background: color-mix(in srgb, var(--danger) 22%, transparent);
  border-color: var(--danger);
  transform: translateY(-1px);
}
.danger-btn--critical {
  background: var(--danger);
  border-color: var(--danger);
  color: white;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(215, 39, 39, 0.35);
}
.danger-btn--critical:hover {
  background: var(--danger-hover);
  border-color: var(--danger-hover);
  box-shadow: 0 4px 16px rgba(215, 39, 39, 0.45);
}

.section-actions {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--border-subtle);
}
.btn-primary {
  padding: var(--space-2) var(--space-6);
  background: var(--accent);
  border: none;
  color: var(--text-on-accent);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  transition: all var(--duration-base) var(--ease-out);
  box-shadow: var(--shadow-petal-sm);
  letter-spacing: 0.01em;
}
.btn-primary:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
  box-shadow: var(--shadow-petal);
}
.btn-primary:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
  background: var(--accent-press);
}
.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  box-shadow: none;
}
.btn-primary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.btn-secondary {
  padding: var(--space-2) var(--space-5);
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  color: var(--text-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-base);
  font-weight: 500;
  transition: all var(--duration-base) var(--ease-out);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}
.btn-secondary:hover {
  border-color: var(--accent);
  background: var(--surface-5);
  transform: translateY(-1px);
}
.btn-secondary:active {
  transform: translateY(0) scale(0.98);
}

.btn-ghost-sm {
  padding: var(--space-1) var(--space-3);
  background: none;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--duration-base) var(--ease-petal);
  font-weight: 500;
}
.btn-ghost-sm:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-subtle);
}

.btn-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: var(--radius-full);
  animation: spin 0.7s linear infinite;
}

.global-toast {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  border: 1px solid var(--border-default);
  background: color-mix(in srgb, var(--surface-3) 94%, transparent);
  color: var(--text-primary);
  backdrop-filter: blur(16px);
}
.toast-success {
  background: color-mix(in srgb, var(--accent) 12%, var(--surface-3));
  color: var(--text-primary);
  border-color: color-mix(in srgb, var(--accent) 48%, var(--border-default));
  box-shadow: var(--shadow-lg), inset 3px 0 0 var(--accent);
}
.toast-error {
  background: color-mix(in srgb, var(--danger) 12%, var(--surface-3));
  color: var(--text-primary);
  border-color: color-mix(in srgb, var(--danger) 48%, var(--border-default));
  box-shadow: var(--shadow-lg), inset 3px 0 0 var(--danger);
}

.toast-anim-enter-active,
.toast-anim-leave-active {
  transition: all var(--duration-slow) var(--ease-bloom);
}
.toast-anim-enter-from,
.toast-anim-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

.settings-content::-webkit-scrollbar {
  width: 5px;
}
.settings-content::-webkit-scrollbar-thumb {
  background: var(--surface-5);
  border-radius: var(--radius-full);
}
.settings-content::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
}
.settings-content::-webkit-scrollbar-track {
  background: transparent;
}
.sidebar-nav::-webkit-scrollbar {
  width: 3px;
}
.sidebar-nav::-webkit-scrollbar-thumb {
  background: var(--surface-5);
  border-radius: var(--radius-full);
}
.sidebar-nav::-webkit-scrollbar-track {
  background: transparent;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.member-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--surface-4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition: all var(--duration-base) var(--ease-out);
}
.member-card:hover {
  border-color: var(--border-default);
  background: var(--surface-5);
}
.member-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  object-fit: cover;
  flex-shrink: 0;
  background: var(--surface-5);
}
.member-info {
  flex: 1;
  min-width: 0;
}
.member-name {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.member-role {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-1);
}
.role-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
  line-height: 1.4;
}
.role-badge.owner {
  background: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--accent);
  border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent);
}
.role-badge.admin {
  background: color-mix(in srgb, #f59e0b 18%, transparent);
  color: #f59e0b;
  border: 1px solid color-mix(in srgb, #f59e0b 35%, transparent);
}
.role-badge.participant {
  background: var(--surface-5);
  color: var(--text-tertiary);
  border: 1px solid var(--border-subtle);
}
.member-custom-title {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-style: italic;
}
.member-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.role-select {
  background: var(--surface-5);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: 4px var(--space-2);
  color: var(--text-primary);
  font-size: var(--text-xs);
  cursor: pointer;
  outline: none;
  transition: all var(--duration-base) var(--ease-out);
}
.role-select:focus {
  border-color: var(--accent);
  box-shadow: var(--border-glow);
}
.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-width: 28px;
  min-height: 28px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-subtle);
  background: var(--surface-5);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: var(--text-sm);
  transition: all var(--duration-fast) var(--ease-out);
}
.btn-icon:hover {
  background: var(--surface-4);
  border-color: var(--border-default);
}
.btn-icon--danger:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #ef4444;
}
.add-user-row {
  position: relative;
}
.user-search-field {
  position: relative;
  display: flex;
  align-items: center;
}
.user-search-field .text-field {
  padding-right: var(--space-8);
}
.search-spinner {
  position: absolute;
  right: var(--space-3);
  width: 16px;
  height: 16px;
  border: 2px solid var(--border-default);
  border-top-color: var(--accent);
  border-radius: var(--radius-full);
  animation: spin 0.7s linear infinite;
  pointer-events: none;
}
.user-search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: var(--space-1);
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-modal);
  z-index: 10;
  max-height: 220px;
  overflow-y: auto;
}
.user-search-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out);
}
.user-search-item.active,
.user-search-item:hover {
  background: var(--surface-4);
}
.user-search-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  object-fit: cover;
  flex-shrink: 0;
}
.user-search-meta {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.user-search-name {
  font-size: var(--text-sm);
  color: var(--text-primary);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-search-username {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-search-empty {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  text-align: center;
}

.actions-card {
  border-color: color-mix(in srgb, var(--accent) 35%, var(--border-subtle));
  background: linear-gradient(
    135deg,
    var(--surface-3),
    color-mix(in srgb, var(--accent) 6%, var(--surface-3))
  );
}

.actions-title {
  color: var(--accent);
}

.action-btn {
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  border: 1px solid transparent;
  transition:
    background-color 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease,
    opacity 0.2s ease;
}

.action-btn:active {
  opacity: 0.85;
}

.action-btn--leave {
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
  color: var(--accent);
}

.action-btn--leave:hover {
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  border-color: var(--accent);
}

.action-btn--delete {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--text-on-accent);
}

.action-btn--delete:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

@media (max-width: 640px) {
  .chat-settings-modal {
    flex-direction: column;
    width: 100vw;
    height: var(--viewport-height, 100dvh);
    border-radius: 0;
    border: none;
  }
  .settings-sidebar {
    width: 100%;
    min-width: 0;
    flex-direction: column;
    border-right: none;
    border-bottom: 1px solid var(--border-subtle);
  }
  .sidebar-header {
    padding: var(--space-3) var(--space-4);
  }
  .chat-avatar-mini {
    width: 32px;
    height: 32px;
  }
  .sidebar-footer {
    display: none;
  }
  .nav-group-title {
    display: none;
  }
  .sidebar-nav {
    display: flex;
    padding: var(--space-2);
    gap: var(--space-1);
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-width: none;
  }
  .sidebar-nav::-webkit-scrollbar {
    display: none;
  }
  .nav-item {
    flex: 0 0 96px;
    width: auto;
    flex-direction: column;
    align-items: center;
    min-width: 68px;
    padding: var(--space-2) var(--space-2);
    font-size: var(--text-xs);
    gap: var(--space-1);
    text-align: center;
  }
  .nav-item::after {
    left: 50%;
    top: auto;
    bottom: -6px;
    transform: translateX(-50%) scaleX(0);
    width: 55%;
    height: 3px;
  }
  .nav-item.active::after {
    transform: translateX(-50%) scaleX(1);
  }
  .nav-label {
    align-items: center;
  }
  .nav-name {
    white-space: normal;
    line-height: 1.25;
    min-height: 2.5em;
    overflow-wrap: anywhere;
  }
  .nav-hint {
    display: none;
  }
  .settings-pane {
    max-width: none;
  }
  .settings-section {
    padding: var(--space-4);
  }
  .two-col {
    grid-template-columns: 1fr;
  }
  .interface-colors-grid {
    grid-template-columns: 1fr;
  }
  .section-header {
    margin-bottom: var(--space-4);
  }
  .settings-group-card {
    padding: var(--space-3);
  }
  .global-toast {
    left: var(--space-4);
    right: var(--space-4);
    bottom: var(--space-4);
  }
}

@media (max-width: 480px) {
  .theme-presets-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .wallpaper-presets-grid {
    grid-template-columns: repeat(3, 1fr);
  }
  .bubble-style-picker {
    gap: var(--space-2);
  }
  .bsp-item {
    min-width: 64px;
    padding: var(--space-2);
  }
}

@media (prefers-reduced-motion: reduce) {
  .chat-settings-modal,
  .modal-overlay,
  .settings-section,
  .section-swap-enter-active,
  .section-swap-leave-active,
  .nav-item,
  .nav-icon-chip,
  .btn-primary,
  .btn-secondary,
  .type-tab,
  .switch-slider,
  .swatch,
  .wp-preset,
  .theme-preset-btn,
  .avatar-preview-large,
  .clear-btn {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
