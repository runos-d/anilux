<template>
  <div class="chat-detail">
    <FranchiseDiscussionChat
      v-if="isFranchiseDiscussion"
      :franchise-id="chat?.franchise_id ?? 0"
      :franchise-name="chat?.name || ''"
      :franchise-poster="chat?.avatar_url || ''"
      :franchise-slug="chat?.franchise_slug"
      :highlight-anime-id="highlightAnimeId"
    />

    <div v-else-if="chatNotFound" class="chat-not-found-state">
      <div class="chat-not-found-icon"><SakuraIcon name="users" :size="30" /></div>
      <h2>Чат не найден</h2>
      <p>Группа больше не существует или недоступна. Её можно убрать из вашего списка чатов.</p>
      <button
        v-if="props.chatType === 'group'"
        type="button"
        class="chat-not-found-remove"
        @click="removeUnavailableGroup"
      >
        Выйти и удалить из списка
      </button>
      <button v-else type="button" class="chat-not-found-back" @click="router.push('/chats')">
        Вернуться к чатам
      </button>
    </div>

    <template v-else>
      <div class="chat-wallpaper" :style="wallpaperVars" :data-own="currentWallpaper ? 'true' : undefined" aria-hidden="true"></div>
      <header class="chat-header">
        <div class="header-left">
          <div class="avatar-wrap" @click="!loadingMessages && (showSettings = true)" role="button" aria-label="Профиль чата">
            <img :src="chatAvatar" :alt="chatName" class="avatar" />
            <span
              v-if="chat?.type === 'private' && isOnline"
              class="online-dot"
            />
          </div>
          <div class="header-info">
            <h1
              class="chat-name"
              :class="{ 'is-link': topicPageTarget }"
              :role="topicPageTarget ? 'link' : undefined"
              :tabindex="topicPageTarget ? 0 : undefined"
              @click="openTopicPage"
              @keydown.enter.prevent="openTopicPage"
              @keydown.space.prevent="openTopicPage"
            >{{ topicName || chatName }}</h1>
            <p v-if="chat?.type === 'private'" class="chat-status">
              <span v-if="isOtherTyping" class="typing">печатает...</span>
              <span v-else-if="isOnline" class="online">онлайн</span>
              <span v-else class="offline">был(а) недавно</span>
            </p>
            <p v-else-if="chat?.type === 'group'" class="chat-status">
              {{ chat.members_count ?? chat.participants_usernames?.length ?? 0 }} участников
            </p>
          </div>
        </div>
        <div class="header-actions">
          <button class="action-btn" title="Поиск по сообщениям" @click="showSearch = true">
            <SakuraIcon name="search" :size="18" />
          </button>
          <button
            v-if="isGroup && chat?.user_permissions?.can_invite_users"
            class="action-btn"
            title="Пригласить"
            @click="handleInvite"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M19 8v6M22 11h-6" />
            </svg>
          </button>
          <button
            class="action-btn"
            title="Настройки"
            :disabled="loadingMessages"
            @click="showSettings = true"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H2a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V2a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
            </svg>
          </button>
        </div>
      </header>

      <div class="messages-wrap">
        <div class="messages" ref="messagesContainer" @scroll="handleScroll">
        <div v-if="loadingMessages" class="loading-state">
          <span>Загрузка...</span>
        </div>
        <div v-else-if="messages.length === 0" class="empty-messages">
          <p>Нет сообщений. Напишите первым!</p>
        </div>
        <div v-if="isSelectionMode" class="message-select-bar">
          <span class="message-select-count">{{ selectedMessages.size }} выбрано</span>
          <div class="message-select-actions">
            <button class="message-select-btn danger" @click="deleteSelectedMessages" title="Удалить">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
            </button>
            <button class="message-select-btn" @click="clearSelection" title="Отменить">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12" /></svg>
            </button>
          </div>
        </div>
        <div class="messages-list">
          <VirtualChatTimeline ref="timeline" :messages="messages" :scroll-element="messagesContainer" @rendered="setupMessageObserver" v-slot="{ message }">
            <div v-if="messageMeta.get(message.id)?.showDivider" class="day-divider">
              <span class="day-label">
                {{ messageMeta.get(message.id)?.day }}
              </span>
            </div>
            <ChatSystemMessage v-if="message.message_type === 'system'" :message="message" :user-id="user?.id" :data-message-id="message.id" />
            <div v-else
              :class="[
                'message',
                {
                  'message--own': message.sender_id === user?.id,
                  'message--other': message.sender_id !== user?.id,
                  'message--grouped': messageMeta.get(message.id)?.grouped,
                  'message--has-next-grouped': messageMeta.get(message.id)?.groupedWithNext,
                  'message--has-reactions': getMessageReactions(message.id).length > 0,
                },
              ]"
              :data-message-id="message.id"
              @contextmenu.prevent="showMessageMenu(message, $event)"
              @click="handleMessageClick(message, $event)"
              @pointerdown="handleMessagePointerDown(message, $event)"
              @pointerup="handleMessagePointerUp"
              @pointercancel="handleMessagePointerUp"
            >
              <div
                v-if="isGroup && messageMeta.get(message.id)?.showSenderHeader"
                class="message-sender-avatar"
                :style="{ background: getMessageAuthorColor(message.sender_id) }"
              >
                {{ getSenderInitial(message.sender_username || "") }}
              </div>
              <div v-else-if="isGroup && message.sender_id !== user?.id" class="message-sender-avatar-placeholder" aria-hidden="true" />
              <div class="message-body" :class="{ 'message-body--selected': selectedMessages.has(message.id) }">
                <div v-if="selectedMessages.has(message.id)" class="message-select-check">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5" /></svg>
                </div>
                <div
                  v-if="
                    isGroup && messageMeta.get(message.id)?.showSenderHeader
                  "
                  class="message-sender-name"
                >
                  {{ message.sender_username || "Unknown" }}
                </div>
                <div v-if="message.reply_to_message" class="reply-quote" :style="{ borderLeftColor: getMessageAuthorColor(message.reply_to_message.sender_id) }" @click="handleInnerClick($event, () => scrollToReply(message.reply_to_message!))">
                  <div class="reply-author" :style="{ color: getMessageAuthorColor(message.reply_to_message.sender_id) }">
                    {{ message.reply_to_message.sender_username || "Пользователь" }}
                  </div>
                  <div v-if="message.reply_to_message.text" class="reply-text">
                    {{ truncateText(message.reply_to_message.text, 100) }}
                  </div>
                </div>
                <div v-if="message.text && !hasSharedCards(message)" class="message-text"><span class="meta-float"><MessageMeta
                    variant="plain"
                    :tone="message.sender_id === user?.id ? 'accent' : 'neutral'"
                    :time="formatMessageTime(message.created_at)"
                    :pinned="message.is_pinned"
                    :edited="message.is_edited"
                    v-bind="getMessageStatus(message)"
                  /></span><span class="msg-text">{{ message.text }}</span></div>
                  <button v-if="message.send_status === 'failed'" class="retry-message" @click.stop="retryMessage(message.id)">Не отправлено · Повторить</button>
                <div v-if="getMediaItems(message).length" class="message-media-grid">
                  <template v-for="(mItem, mIdx) in getMediaItems(message)" :key="'media-' + mIdx">
                    <img
                      v-if="mItem.type === 'image'"
                      :src="mItem.url"
                      class="message-image"
                      loading="eager"
                      @load="handleMessageImageLoad"
                      @error="renewMessageMedia($event, message.id)"
                    />
                    <video
                      v-else-if="mItem.type === 'video'"
                      :src="mItem.url"
                      controls
                      preload="none"
                      class="message-video"
                      @error="renewMessageMedia($event, message.id)"
                    />
                  </template>
                <MessageMeta
                    v-if="!message.text && !hasSharedCards(message)"
                    variant="media"
                    tone="accent"
                    :time="formatMessageTime(message.created_at)"
                    :pinned="message.is_pinned"
                    :edited="message.is_edited"
                    v-bind="getMessageStatus(message)"
                  />
                </div>
                <div v-if="message.id < 0 && uploadProgress > 0" class="upload-progress">
                  <div class="upload-progress-bar">
                    <div class="upload-progress-fill" :style="{ width: uploadProgress + '%' }" />
                  </div>
                  <span class="upload-progress-label">{{ uploadProgress }}%</span>
                </div>
                <a
                  v-for="(fCard, fIdx) in getFileCards(message)"
                  :key="'file-' + fIdx"
                  class="file-card"
                  :href="fCard.url"
                  target="_blank"
                  rel="noopener"
                  @click="downloadChatFile($event, fCard.url, fCard.name)"
                >
                  <span class="file-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                  </span>
                  <span class="file-card-info">
                    <span class="file-card-name">{{ fCard.name }}</span>
                    <span class="file-card-size">{{ fCard.sizeLabel }}</span>
                  </span>
                  <svg class="file-card-dl" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" /></svg>
                </a>
                <ChatContentCard
                  v-for="cCard in getContentCards(message)"
                  :key="`${cCard.type}:${cCard.id}`"
                  :type="cCard.type"
                  :data="cCard.data"
                  :own="message.sender_id === user?.id"
                  :time="formatMessageTime(message.created_at)"
                  @open="handleInnerClick($event, () => openContentCard(cCard))"
                />
                <div v-if="getMessageReactions(message.id).length > 0" class="reactions">
                  <button
                    v-for="(reaction, idx) in getGroupedReactions(message.id)"
                    :key="idx"
                    class="reaction"
                    :class="{ 'reaction--collapsed': idx >= 4 }"
                    @click.stop="handleReaction(message.id, reaction.emoji)"
                  >
                    {{ reaction.emoji }} {{ reaction.count }}
                  </button>
                </div>
                <MessageMeta
                  v-if="!message.text && !getMediaItems(message).length && !getContentCards(message).length"
                  variant="plain"
                  :tone="message.sender_id === user?.id ? 'accent' : 'neutral'"
                  :time="formatMessageTime(message.created_at)"
                  :pinned="message.is_pinned"
                  :edited="message.is_edited"
                  v-bind="getMessageStatus(message)"
                />
              </div>
            </div>
          </VirtualChatTimeline>
        </div>
      </div>
      <button v-if="showScrollDownBtn" class="scroll-down" @click="scrollToBottom(true)" title="Вниз">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 5v14M19 12l-7 7-7-7" />
        </svg>
      </button>
      </div>

      <div class="input-area">
        <div v-if="editingMessage" class="edit-preview" role="status">
          <strong>Редактирование сообщения</strong>
          <span>{{ editingMessage.text }}</span>
          <button type="button" aria-label="Отменить редактирование" @click="cancelEdit"><SakuraIcon name="x" :size="16" /></button>
        </div>
        <MessageReplyPreview
          v-if="replyToMessage && !editingMessage"
          :message="replyToMessage"
          :author="replyToMessage.sender_username || replyToMessage.sender?.username || 'Пользователь'"
          :author-color="getMessageAuthorColor(replyToMessage.sender_id)"
          @close="cancelReply"
          @click="scrollToMessage(replyToMessage.id)"
        />
        <div v-if="pendingAttachments.length && !editingMessage" class="pending-attachments">
          <div v-for="(att, idx) in pendingAttachments" :key="idx" class="pending-attachment">
            <template v-if="att.kind === 'excerpt'"><span class="pending-info">Отрывок: {{ att.excerpt.title || att.excerpt.anime_title }}</span></template>
            <template v-else-if="att.kind === 'anime'">
              <img :src="resolvePosterUrl(att.poster_url)" class="pending-poster" @error="handleImageError" />
              <span class="pending-info">Аниме: {{ att.title_ru || att.title_en || `#${att.id}` }}</span>
            </template>
            <template v-else-if="att.kind === 'playlist'">
              <img :src="resolvePosterUrl(att.cover_image)" class="pending-poster" @error="handleImageError" />
              <span class="pending-info">Плейлист: {{ att.title || `#${att.id}` }} ({{ att.items_count ?? 0 }})</span>
            </template>
            <template v-else-if="att.kind === 'file'">
              <span class="pending-icon"><SakuraIcon name="paperclip" :size="16" /></span>
              <span class="pending-info">{{ att.file.name }} ({{ (att.file.size / 1024).toFixed(1) }} KB)</span>
            </template>
            <button type="button" class="pending-remove" @click="removePendingAttachment(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
          </div>
        </div>
        <form @submit.prevent="sendMessage" class="input-form">
          <div class="input-row">
            <button type="button" class="input-action" aria-label="Прикрепить" @click.stop="toggleAttachMenu" :disabled="!wsConnected || persistingSend || !!editingMessage">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
            <textarea
              v-model="composerText"
              ref="messageInputEl"
              rows="1"
              placeholder="Сообщение..."
              class="message-textarea"
              :disabled="!wsConnected"
              :readonly="persistingSend || savingEdit"
              @input="handleTyping; autoResizeTextarea($event)"
              @keydown="onInputKeydown"
            />
            <button type="button" class="input-action" aria-label="Эмодзи" @click.stop="toggleEmojiPicker" :disabled="!wsConnected || persistingSend">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <path d="M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01" />
              </svg>
            </button>
            <button type="submit" class="send-btn" :aria-label="editingMessage ? 'Сохранить изменение' : 'Отправить сообщение'" :disabled="(!composerText.trim() && (!!editingMessage || pendingAttachments.length === 0)) || !wsConnected || persistingSend || savingEdit">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </div>
        </form>
        <input ref="attachFileInput" type="file" multiple style="display: none" @change="handleAttachFileSelect" />
        <Transition name="pop">
          <div v-if="showAttachMenu" class="attach-menu" @click.stop>
            <button type="button" class="attach-item" @click="pendingExcerptSelection = pendingAttachments.filter(item => item.kind === 'excerpt').map(item => item.excerpt); showAttachExcerpt = true; showAttachMenu = false">Отрывок</button>
            <button type="button" class="attach-item" @click="attachFile" :disabled="!wsConnected || persistingSend">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              Файл
            </button>
            <button type="button" class="attach-item" @click="showAttachPlaylist = true; showAttachMenu = false; loadUserPlaylists()" :disabled="!wsConnected || persistingSend">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18V5l12-2v13" />
                <circle cx="6" cy="18" r="3" />
                <circle cx="18" cy="16" r="3" />
              </svg>
              Плейлист
            </button>
            <button type="button" class="attach-item" @click="showAttachAnime = true; showAttachMenu = false; openAnimeSearch()" :disabled="!wsConnected || persistingSend">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="2" y="2" width="20" height="20" rx="2.18" />
                <path d="M7 2v20M17 2v20M2 12h20M2 7h20M2 17h20" />
              </svg>
              Аниме
            </button>
          </div>
        </Transition>
        <Transition name="pop">
          <div v-if="showEmojiPicker" class="emoji-picker" @click.stop>
            <button v-for="emoji in emojiSet" :key="emoji" type="button" class="emoji-btn" @click="insertEmoji(emoji)">
              {{ emoji }}
            </button>
          </div>
        </Transition>
      </div>

      <ChatSettingsModal
        v-if="showSettings && currentChatId && chat && !loadingMessages"
        :chat-id="currentChatId"
        :chat-type="chat?.type || 'group'"
        :chat-name="chatName"
        :chat-avatar="chatAvatar"
        :is-owner="isChatOwner"
        :is-admin="canManageChat"
        @close="showSettings = false"
        @settings-saved="handleSettingsChanged"
      />

      <MessageSearchModal
        :is-open="showSearch"
        :chat-id="currentChatId || 0"
        :chat-type="chat?.type"
        :topic-id="topicId"
        @close="showSearch = false"
        @message-selected="(id) => scrollToMessage(id)"
      />

      <ForwardMessageModal
        :is-open="showForward"
        :message="messageForForward"
        :available-chats="chatsForForward"
        @close="showForward = false"
        @forwarded="handleForwardComplete"
      />

      <ChatInviteModal
        :is-open="showInvite"
        :chat-id="currentChatId || 0"
        @close="showInvite = false"
      />

      <Teleport to="body">
        <div v-if="showAttachExcerpt" class="attach-overlay" @click.self="showAttachExcerpt = false">
          <div class="attach-picker-modal"><div class="attach-picker-header"><h3>Прикрепить отрывок</h3><button type="button" class="attach-picker-close" @click="showAttachExcerpt = false" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button></div><ExcerptPicker :selected="pendingExcerptSelection" @update:selected="selectExcerpts" /><button type="button" class="attach-picker-close" @click="showAttachExcerpt = false">Готово</button></div>
        </div>
        <div v-if="showAttachAnime" class="attach-overlay" @click.self="showAttachAnime = false">
          <div class="attach-picker-modal">
            <div class="attach-picker-header">
              <h3>Выберите аниме</h3>
              <button type="button" class="attach-picker-close" @click="showAttachAnime = false" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
            </div>
            <div class="attach-picker-search">
              <input
                v-model="animeSearch"
                type="text"
                placeholder="Поиск аниме..."
                @input="debouncedAnimeSearch"
              />
              <span v-if="isSearching" class="attach-spinner">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner-icon">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              </span>
            </div>
            <div class="attach-picker-results">
              <div v-if="isSearching" class="attach-loading">Поиск...</div>
              <div v-else-if="animeSearchError" class="attach-empty">{{ animeSearchError }}</div>
              <div v-else-if="animeSearch.length >= 2 && searchResults.length === 0" class="attach-empty">
                Ничего не найдено по запросу «{{ animeSearch }}»
              </div>
              <div v-else-if="animeSearch.length >= 2 && searchResults.length > 0" class="attach-results-list" ref="resultsList">
                <p v-if="animeSearchTotalCount > 0" class="attach-count">Найдено: {{ animeSearchTotalCount }}</p>
                <button
                  v-for="anime in searchResults"
                  :key="anime.id"
                  type="button"
                  class="attach-result-item"
                  @click="selectAttachAnime(anime)"
                >
                  <img :src="resolvePosterUrl(anime.poster_url || anime.poster_image_url)" class="attach-poster" @error="handleImageError" />
                  <span class="attach-result-info">
                    <span class="attach-result-title">{{ anime.title_ru || anime.title_en || anime.title_jp || `#${anime.id}` }}</span>
                    <span class="attach-result-sub">
                      {{ anime.year }}{{ anime.episodes ? ` · ${anime.episodes} эп.` : "" }}<template v-if="anime.score"> · <SakuraIcon name="star" :size="12" /> {{ anime.score.toFixed(1) }}</template>
                    </span>
                  </span>
                </button>
              </div>
              <div v-else-if="!isSearching && animeSearch.length < 2 && searchResults.length === 0" class="attach-empty">
                Введите минимум 2 символа для поиска
              </div>
              <div v-if="hasMoreResults || searchPage > 1" class="attach-pagination">
                <button
                  v-if="searchPage > 1"
                  type="button"
                  class="attach-page-btn page-nav-prev"
                  :disabled="isSearching"
                  @click="prevPage"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                </button>
                <span class="attach-page-info">Страница {{ searchPage }}</span>
                <button
                  v-if="hasMoreResults"
                  type="button"
                  class="attach-page-btn page-nav-next"
                  :disabled="isSearching"
                  @click="nextPage"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-if="showAttachPlaylist" class="attach-overlay" @click.self="showAttachPlaylist = false">
          <div class="attach-picker-modal">
            <div class="attach-picker-header">
              <h3>Выберите плейлист</h3>
              <button type="button" class="attach-picker-close" @click="showAttachPlaylist = false" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
            </div>
            <div class="attach-picker-results">
              <p v-if="userPlaylists.length === 0 && !playlistsLoading" class="attach-empty">У вас пока нет плейлистов</p>
              <p v-if="playlistsLoading" class="attach-empty">Загрузка...</p>
              <button
                v-for="playlist in userPlaylists"
                :key="playlist.id"
                type="button"
                class="attach-result-item"
                @click="selectAttachPlaylist(playlist)"
              >
                <img :src="resolvePosterUrl(playlist.cover_image)" class="attach-poster attach-playlist-cover" @error="handleImageError" />
                <span class="attach-result-info">
                  <span class="attach-result-title">{{ playlist.title || playlist.name }}</span>
                  <span class="attach-result-sub">{{ playlist.items_count ?? 0 }} аниме</span>
                </span>
              </button>
            </div>
          </div>
        </div>
      </Teleport>

      <Teleport to="body">
        <div
          v-if="contextMenu.visible"
          ref="contextPopup"
          class="context-popup"
          :style="{ top: popupPosition.y + 'px', left: popupPosition.x + 'px' }"
          @click.stop
        >
          <div class="reaction-row">
            <button v-for="emoji in reactionEmojis" :key="emoji" class="reaction-btn" @click="selectedMessage && handleReaction(selectedMessage.id, emoji)">
              {{ emoji }}
            </button>
          </div>
          <div class="context-actions">
            <button class="context-action" @click="selectedMessage && selectMessage(selectedMessage)">Выбрать</button>
            <button v-if="selectedMessage && selectedMessage.sender_id === user?.id && selectedMessage.id > 0 && selectedMessage.text && selectedMessage.can_edit !== false" class="context-action" @click="handleEdit(selectedMessage)">
              Изменить
            </button>
            <button class="context-action" @click="handleReply(selectedMessage)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H13" />
              </svg>
              Ответить
            </button>
            <button
              v-if="selectedMessage?.sender_id === user?.id"
              class="context-action danger"
              @click="handleDelete(selectedMessage?.id ?? 0)"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              </svg>
              Удалить
            </button>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template>

<script setup lang="ts">
import { pendingChatSends, finishPendingSend, nextTemporaryMessageId, storePendingSend, hydrateChatOutbox } from "@/lib/chatOutbox";
import VirtualChatTimeline from "@/components/Chats/VirtualChatTimeline.vue";
import ExcerptPicker from "@/components/excerpts/ExcerptPicker.vue";
import type { Excerpt } from "@/api/excerpts";
import ChatContentCard from "@/components/Chats/ChatContentCard.vue";
import type { ChatContentCardData } from "@/types/chat";
import { useChatDraft } from "@/composables/useChatDraft";
import { ChatConnection, mergeMessages, webSocketProtocols } from "@/lib/chatTimeline";
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { useChatExtrasStore } from "@/stores/chatExtras";
import { usePrivateChatStore } from "@/stores/privateChat";
import { useGroupChatStore } from "@/stores/groupChat";
import { useAvatar } from "@/composables/useAvatar";
import { useOnlineStatus } from "@/composables/useOnlineStatus";
import { useGlobalWebSocket } from "@/composables/useGlobalWebSocket";
import { joinOpenedDiscussion } from "@/lib/discussionMembership";
import { validateMessageFiles } from "@/lib/chatUploadLimits";
import { prepareMediaFiles } from "@/lib/clientMediaConversion";
import { useAnimeAttachmentSearch } from "@/composables/useAnimeAttachmentSearch";
import ChatSystemMessage from "@/components/Chats/ChatSystemMessage.vue";
import ChatSettingsModal from "@/components/Chats/ChatSettingsModal.vue";
import FranchiseDiscussionChat from "@/components/Chats/FranchiseDiscussionChat.vue";
import MessageReplyPreview from "@/components/Chats/MessageReplyPreview.vue";
import MessageMeta from "@/components/Chats/MessageMeta.vue";
import MessageSearchModal from "@/components/modal/chats/MessageSearchModal.vue";
import ForwardMessageModal from "@/components/modal/chats/ForwardMessageModal.vue";
import ChatInviteModal from "@/components/modal/chats/ChatInviteModal.vue";
import { chatsApi, messageActionsApi } from "@/api/chats";
import apiClient, { getMediaUrl, getMediaBaseUrl } from "@/api/client";
import { useToast } from "@/composables/useToast";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import type { Chat, Message, ChatWallpaper, ChatTheme } from "@/types/chat";

type ChatUser = {
  id?: number;
  username?: string;
  display_name?: string | null;
  avatar?: string | null;
  avatar_url?: string | null;
  is_online?: boolean;
};

type ChatDetail = Chat & {
  public_id?: number;
  conversation_id?: number;
  franchise_id?: number | null;
  franchise_slug?: string | null;
  anime_id?: number | null;
  is_public?: boolean;
  discussion_type?: string;
  members_count?: number;
  name?: string;
  avatar_url?: string | null;
  description?: string;
  participants_usernames?: string[];
  user1?: ChatUser;
  user2?: ChatUser;
  other_user?: ChatUser;
  admins?: { id: number }[];
  created_by?: { id: number } | null;
  user_role?: { is_owner?: boolean; is_admin?: boolean } | null;
  user_permissions?: Record<string, boolean>;
};

type SharedPlaylistData = {
  id: number;
  title: string;
  cover_image?: string | null;
  items_count?: number;
  posters?: string[];
};

type SharedShortsData = {
  id: number;
  title?: string;
  image_url?: string | null;
  video_url?: string | null;
  thumbnail_url?: string | null;
  author?: { username?: string } | null;
  anime?: { title_ru?: string } | null;
};

const getPlaylistData = (m: Message): SharedPlaylistData => m.shared_playlist_data as SharedPlaylistData;
const getShortsData = (m: Message): SharedShortsData => m.shared_shorts_data as SharedShortsData;

interface Props {
  chatId?: number;
  franchiseId?: number;
  chatType?: "private" | "group" | null;
  topicId?: number;
  topicName?: string;
  topicIsGeneral?: boolean;
  topicAnimeId?: number | null;
  franchiseSlug?: string | null;
}
const props = defineProps<Props>();

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const chatExtrasStore = useChatExtrasStore();
const privateChatStore = usePrivateChatStore();
const groupChatStore = useGroupChatStore();
const { getAvatarUrl } = useAvatar();
const { isUserOnline } = useOnlineStatus();

const chat = ref<ChatDetail | null>(null);
const chatNotFound = ref(false);
const messages = ref<Message[]>([]);
const loadingMessages = ref(false);
const showChatInfo = ref(false);
const readMessageIds = ref<Set<number>>(new Set());
const showSettings = ref(false);
const showSearch = ref(false);
const showInvite = ref(false);
const showForward = ref(false);
const showAttachPlaylist = ref(false);
const showAttachAnime = ref(false);

type AttachAnimeItem = { 
  id: number; 
  title_ru?: string; 
  title_en?: string; 
  title_jp?: string;
  poster_url?: string | null; 
  poster_image_url?: string | null; 
  year?: number | null; 
  kind?: string | null;
  episodes?: number | null;
  score?: number | null;
};

type AttachPlaylistItem = { id: number; title?: string; name?: string; cover_image?: string | null; items_count?: number };
const selectedPlaylist = ref<AttachPlaylistItem | null>(null);
const selectedAnime = ref<AttachAnimeItem | null>(null);
const userPlaylists = ref<AttachPlaylistItem[]>([]);
const playlistsLoading = ref(false);
const playlistsLoadedAt = ref(0);
let playlistsRequest: Promise<void> | null = null;
const { animeSearch, searchResults, isSearching, searchPage, hasMoreResults, resultsList,
  animeSearchTotalCount, animeSearchError, debouncedAnimeSearch, clearAnimeSearch, openAnimeSearch,
  nextPage, prevPage } = useAnimeAttachmentSearch();
const attachFileInput = ref<HTMLInputElement>();
const messageToForward = ref<Message | null>(null);
const selectedMessage = ref<Message | null>(null);
const replyToMessage = ref<Message | null>(null);
const showPinnedBar = ref(false);
const newMessage = ref("");
const editingMessage = ref<Message | null>(null);
const editText = ref("");
const savingEdit = ref(false);
let editAbort: AbortController | null = null;
const composerText = computed({
  get: () => editingMessage.value ? editText.value : newMessage.value,
  set: value => { if (editingMessage.value) editText.value = value; else newMessage.value = value; },
});
const messagesContainer = ref<HTMLElement>();
const timeline = ref<{ scrollToMessage: (id: number) => Promise<boolean> }>();
useChatDraft(() => chat.value ? `${chat.value.type}:${chat.value.id}${props.topicId !== undefined ? `:${props.topicId}` : ''}` : null, newMessage);
const isOtherTyping = ref(false);
const wsConnected = ref(false);
const reconnectAttempts = ref(0);
const availableChats = ref<Chat[]>([]);
const currentWallpaper = ref<ChatWallpaper | null>(null);
const currentTheme = ref<ChatTheme | null>(null);

const wallpaperVars = computed((): Record<string, string> => {
  const wp = currentWallpaper.value as unknown as
    | Record<string, unknown>
    | null;
  if (!wp) return {};
  const type = String(wp.wallpaper_type || "solid");
  const color = String(wp.wallpaper_color || "#0f0f1a");
  const style: Record<string, string> = {};

  if (type === "image") {
    style.backgroundColor = color;
    const raw =
      typeof wp.wallpaper_image_url === "string" ? wp.wallpaper_image_url : "";
    const src = raw ? getMediaUrl(raw) : undefined;
    if (src) {
      style.backgroundImage = `url("${src}")`;
      style.filter = `blur(${Number(wp.wallpaper_blur ?? 0)}px) brightness(${Number(wp.wallpaper_intensity ?? 100) / 100})`;
    }
    return style;
  }

  if (type === "gradient") {
    const c2 = String(wp.wallpaper_color2 || color);
    style.backgroundColor = color;
    style.backgroundImage = `linear-gradient(${Number(wp.gradient_angle ?? 135)}deg, ${color}, ${c2})`;
    return style;
  }

  style.backgroundColor = color;
  return style;
});

const contextMenu = ref({ visible: false, x: 0, y: 0 });
const contextPopup = ref<HTMLElement | null>(null);
const popupPosition = ref({ x: 0, y: 0 });
const reactionEmojis = ["👍", "😢", "😮", "😠", "🎉", "🔥", "👀", "🙏"];
const showScrollDownBtn = ref(false);
const showEmojiPicker = ref(false);
const showAttachMenu = ref(false);
const showAttachExcerpt = ref(false);
const pendingExcerptSelection = ref<Excerpt[]>([]);
const selectExcerpts = (rows: Excerpt[]) => {
  pendingExcerptSelection.value = rows;
  pendingAttachments.value = [...pendingAttachments.value.filter(item => item.kind !== "excerpt"), ...rows.map(item => ({kind: "excerpt" as const, id: item.id, excerpt: item}))];
};
const pendingAttachments = ref<
  Array<
    | { kind: "excerpt"; id: number; excerpt: Excerpt }
    | { kind: "anime"; id: number; title_ru?: string; title_en?: string; poster_url?: string | null }
    | { kind: "playlist"; id: number; title?: string; cover_image?: string | null; items_count?: number }
    | { kind: "file"; file: File; mediaType: "image" | "video" | "file" }
  >
>([]);
const uploadProgress = ref(0);
const emojiSet = ["👍", "🔥", "❤️", "😂", "😢", "😮", "😠", "🎉", "👀", "🙏", "😅", "😍", "🤔", "😎", "🥳", "😇", "💯", "✨", "🌸", "🌙", "⭐", "🍣", "🎬", "📚"];
const toast = useToast();
const selectedMessages = ref<Set<number>>(new Set());
const isSelectionMode = ref(false);
let longPressTimer: ReturnType<typeof setTimeout> | null = null;
let longPressTargetId: number | null = null;
let wasLongPress = false;
const LONG_PRESS_DURATION = 500;

const highlightAnimeId = ref<number | undefined>(undefined);
const activeChatId = ref<number | undefined>(undefined);
const activeFranchiseId = ref<number | undefined>(undefined);
const franchiseData = ref<Record<string, unknown> | null>(null);

const currentChatId = computed(() => {
  if (props.chatId) return props.chatId;
  const routeId = route.params.id;
  if (routeId && routeId !== "undefined") {
    const parsed = parseInt(routeId as string);
    if (!isNaN(parsed)) return parsed;
  }
  return activeChatId.value;
});

const user = computed(() => authStore.user);

const chatName = computed(() => {
  if (chatNotFound.value) return "Чат не найден";
  if (!chat.value) return "Загрузка...";
  if (chat.value.type === "private") {
    const other = chat.value.other_user;
    return chat.value.name || other?.display_name || other?.username || "Личный чат";
  }
  if (chat.value.user1 && chat.value.user2) {
    const other = chat.value.other_user || (chat.value.user1?.id === authStore.user?.id ? chat.value.user2 : chat.value.user1);
    return other?.display_name || other?.username || "Личный чат";
  }
  if (chat.value.type === "group" && chat.value.anime_title) return chat.value.anime_title;
  return chat.value.name || "Групповой чат";
});

const otherUser = computed(() => chat.value?.type === "private" ? chat.value.other_user || null : null);

const chatAvatar = computed(() => {
  if (chat.value?.type === "group" && chat.value.anime_poster) return getMediaUrl(chat.value.anime_poster);
  if (chat.value?.type === "private" && otherUser.value) return getAvatarUrl(otherUser.value.avatar_url || otherUser.value.avatar, otherUser.value.id);
  return getAvatarUrl(chat.value?.avatar_url);
});

const isGroup = computed(() => chat.value?.type === "group");
const isFranchiseDiscussion = computed(() => props.topicId === undefined && chat.value?.type === "group" && !!chat.value?.franchise_id);
const topicPageTarget = computed(() => {
  if (props.topicId === undefined || !props.franchiseId) return "";
  if (props.topicIsGeneral) return `/franchise/${props.franchiseSlug || props.franchiseId}`;
  return props.topicAnimeId ? `/anime/${props.topicAnimeId}` : "";
});
const openTopicPage = () => {
  if (topicPageTarget.value) void router.push(topicPageTarget.value);
};
const isOnline = computed(() => otherUser.value ? isUserOnline(otherUser.value.id) : false);
const isChatOwner = computed(() => !!chat.value?.user_role?.is_owner);
const canManageChat = computed(() => isGroup.value && !!chat.value?.user_permissions?.can_manage_chat);
const inCurrentTopic = (message: Partial<Message>) => props.topicId === undefined || message.topic_id === props.topicId ||
  (!!props.topicIsGeneral && message.topic_id == null);
const queuedMessages = (id: number, kind: string) => [...pendingSends.values()]
  .filter(p => p.chatId === id && p.chatType === kind && inCurrentTopic(p.message)).map(p => p.message);

const pinnedMessages = computed(() => messages.value.filter((m) => m.is_pinned));
const chatsForForward = computed(() => {
  if (!Array.isArray(availableChats.value)) return [];
  const currentId = currentChatId.value;
  return availableChats.value
    .filter((c) => !(currentId && c.id === currentId))
    .map((c) => ({
      id: c.id,
      name: c.type === "group" ? c.name : c.other_user?.username || "Чат",
      avatar_url: c.type === "group" ? c.avatar_url : c.other_user?.avatar_url || c.other_user?.avatar,
      type: c.type,
    }));
});

const messageForForward = computed(() => {
  const m = messageToForward.value;
  if (!m) return null;
  return { id: m.id, sender_username: m.sender_username || "Пользователь", text: m.text };
});

const getFileName = (url: string) => {
  if (!url) return "Файл";
  try { return new URL(url).pathname.split("/").pop() || "Файл"; } catch { return url.split("/").pop() || "Файл"; }
};

type MediaItem = { url: string; type: "image" | "video" };

const getMediaItems = (m: Message): MediaItem[] => {
  const out: MediaItem[] = [];
  const list = Array.isArray(m.attachments) ? m.attachments : [];

  if (list.length > 0) {
    for (const raw of list) {
      if (!raw || typeof raw !== "object") continue;
      const type = String(raw.type || "");
      if (!["image", "video"].includes(type)) continue;
      const rawUrl = (raw.file_url || raw.file || raw.url) as string | undefined;
      if (!rawUrl) continue;
      out.push({ url: getMediaUrl(rawUrl) || rawUrl, type: type as MediaItem["type"] });
    }
  } else if (m.media && (m.media_type === "image" || m.media_type === "video")) {
    out.push({ url: getMediaUrl(m.media) || m.media, type: m.media_type });
  }

  return out;
};

const hasSharedCards = (m: Message): boolean => {
  return !!(m.shared_post_data || m.shared_anime_data || m.shared_playlist_data || m.shared_shorts_data);
};

const formatFileSize = (bytes?: number) => {
  if (!bytes || bytes <= 0) return "";
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(kb < 10 ? 1 : 0)} KB`;
  return `${(kb / 1024).toFixed(1)} MB`;
};

type FileCard = { url: string; name: string; sizeLabel: string };

const getFileCards = (m: Message): FileCard[] => {
  const out: FileCard[] = [];
  const list = Array.isArray(m.attachments) ? m.attachments : [];
  for (const raw of list) {
    if (!raw || typeof raw !== "object") continue;
    if (!["file", "audio"].includes(String(raw.type || ""))) continue;
    const rawUrl = (raw.file_url || raw.file || raw.url) as string | undefined;
    if (!rawUrl) continue;
    const url = getMediaUrl(rawUrl) || rawUrl;
    out.push({
      url,
      name: String(raw.file_name || getFileName(url)),
      sizeLabel: formatFileSize(Number(raw.file_size) || undefined),
    });
  }
  if (m.media && !["image", "video"].includes(m.media_type ?? "")) {
    const url = getMediaUrl(m.media) || m.media;
    out.push({ url, name: getFileName(url), sizeLabel: "" });
  }
  return out;
};

type ContentCardData = Record<string, unknown> & ChatContentCardData;

type ContentCard = { id: number; type: "anime" | "playlist" | "shorts" | "post" | "excerpt"; data: ContentCardData };

const getContentCards = (m: Message): ContentCard[] => {
  const list = Array.isArray(m.attachments) ? m.attachments : [];
  const out: ContentCard[] = [];
  for (const raw of list) {
    if (!raw || typeof raw !== "object") continue;
    const type = String(raw.type || "");
    if (!["anime", "playlist", "shorts", "post", "excerpt"].includes(type)) continue;
    const data = (raw.data ?? null) as ContentCardData | null;
    if (!data) continue;
    out.push({ id: Number(raw.object_id ?? data.id ?? 0), type: type as ContentCard["type"], data });
  }
  for (const [type, data] of [
    ["anime", m.shared_anime_data], ["playlist", m.shared_playlist_data],
    ["post", m.shared_post_data], ["shorts", m.shared_shorts_data],
  ] as const) {
    if (!data) continue;
    const id = Number(data.id ?? 0);
    if (!out.some(card => card.type === type && card.id === id)) out.push({ id, type, data: data as ContentCardData });
  }
  return out;
};

const openContentCard = (card: ContentCard) => {
  const id = card.data?.id ?? card.id;
  if (card.type === "anime") router.push(`/anime/${id}`);
  else if (card.type === "playlist") router.push(`/playlist/${id}`);
  else if (card.type === "post") goToPost(id);
};

const truncateText = (text: string, maxLen: number) => {
  if (!text) return "";
  const cleaned = text.replace(/\n/g, " ").trim();
  return cleaned.length > maxLen ? cleaned.substring(0, maxLen) + "..." : cleaned;
};

const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement | null;
  if (target) target.style.display = "none";
};
const handleMessageImageLoad = (event: Event) => {
  (event.target as HTMLImageElement).style.removeProperty('display');
};
const renewedMedia = new Set<string>();
const mediaRenewedAt = new Map<number, number>();
const renewMessageMedia = async (event: Event, messageId: number) => {
  const element = event.target as HTMLImageElement | HTMLVideoElement;
  const url = element.currentSrc || element.src;
  const key = `${messageId}:${url}`;
  if (!url.includes('/api/social/chat-media/') || renewedMedia.has(key) || !chat.value ||
      Date.now() - (mediaRenewedAt.get(messageId) ?? 0) < 60000) {
    if (element instanceof HTMLImageElement) handleImageError(event);
    return;
  }
  renewedMedia.add(key);
  mediaRenewedAt.set(messageId, Date.now());
  if (renewedMedia.size > 256) renewedMedia.delete(renewedMedia.values().next().value!);
  if (mediaRenewedAt.size > 256) mediaRenewedAt.delete(mediaRenewedAt.keys().next().value!);
  const generation = loadGeneration;
  try {
    const { data } = await apiClient.get(`/social/chats/${chat.value.id}/messages/`, {
      params: { type: chat.value.type, topic_id: props.topicId, around: messageId },
    });
    if (generation !== loadGeneration) return;
    if (element instanceof HTMLVideoElement) {
      const position = element.currentTime;
      element.addEventListener('loadedmetadata', () => { element.currentTime = position; }, { once: true });
    }
    messages.value = mergeMessages(messages.value, data.results, deletedMessages, clearedThroughSeq);
  } catch {
    if (generation === loadGeneration && element instanceof HTMLImageElement) handleImageError(event);
  }
};
const downloadChatFile = async (event: MouseEvent, raw: string, filename: string) => {
  handleInnerLinkClick(event);
  if (event.defaultPrevented) return;
  const url = new URL(raw, window.location.origin);
  if (!url.pathname.startsWith('/api/social/chat-media/')) return;
  event.preventDefault(); url.searchParams.set('download', '1');
  try {
    const { data } = await apiClient.get(url.pathname.slice(4) + url.search, { responseType: 'blob' });
    const blob = URL.createObjectURL(data), link = document.createElement('a');
    link.href = blob; link.download = filename; link.click();
    setTimeout(() => URL.revokeObjectURL(blob), 1000);
  } catch { toast.error('Файл недоступен для скачивания'); }
};

const formatMessageTime = (dateString: string) => new Date(dateString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const getMessageStatus = (message: Message): { status: "none" | "sent" | "read" | "group"; readCount: number } => {
  if (message.sender_id !== user.value?.id) return { status: "none", readCount: 0 };
  if (chat.value?.type === "private") return { status: message.is_read_by_other ? "read" : "sent", readCount: 0 };
  if (chat.value?.type === "group" && message.read_count && message.read_count > 0) {
    return { status: "group", readCount: message.read_count };
  }
  return { status: "none", readCount: 0 };
};

const scrollToBottom = (smooth = false) => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  }
};

const getDayKey = (timestamp: string) => `${new Date(timestamp).getFullYear()}-${new Date(timestamp).getMonth()}-${new Date(timestamp).getDate()}`;
const formatDayLabel = (timestamp: string) => {
  const d = new Date(timestamp);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  const sameDay = (x: Date) => x.getFullYear() === d.getFullYear() && x.getMonth() === d.getMonth() && x.getDate() === d.getDate();
  if (sameDay(today)) return "Сегодня";
  if (sameDay(yesterday)) return "Вчера";
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", weekday: "long" });
};

const isGroupedMessage = (cur: Message, prev: Message | undefined) => {
  if (cur.message_type === 'system' || prev?.message_type === 'system') return false;
  if (!prev) return false;
  if (cur.sender_id !== prev.sender_id) return false;
  if (getDayKey(cur.created_at) !== getDayKey(prev.created_at)) return false;
  const gap = new Date(cur.created_at).getTime() - new Date(prev.created_at).getTime();
  return gap < 5 * 60 * 1000;
};

type MessageMeta = { showDivider: boolean; day: string; grouped: boolean; groupedWithNext: boolean; showSenderHeader: boolean };

const messageMeta = computed(() => {
  const map = new Map<number, MessageMeta>();
  let lastDay = "";
  messages.value.forEach((m, i) => {
    const day = getDayKey(m.created_at);
    const showDivider = day !== lastDay;
    lastDay = day;
    const prev = messages.value[i - 1];
    const grouped = isGroupedMessage(m, prev);
    const showSenderHeader = !!isGroup.value && m.sender_id !== user.value?.id && !grouped;
    const next = messages.value[i + 1];
    const groupedWithNext = !!next && isGroupedMessage(next, m);
    map.set(m.id, { showDivider, day: showDivider ? formatDayLabel(m.created_at) : "", grouped, groupedWithNext, showSenderHeader });
  });
  return map;
});

const getSenderInitial = (senderName: string) => (senderName || "?").trim().charAt(0).toUpperCase();

const handleScroll = () => {
  const el = messagesContainer.value;
  if (!el) return;
  if (el.scrollTop < 100) void loadOlderMessages().catch(() => {});
  showScrollDownBtn.value = el.scrollHeight - el.scrollTop - el.clientHeight > 24;
};

const placeMessageMenu = async () => {
  await nextTick();
  if (!contextMenu.value.visible || !contextPopup.value) return;
  const viewport = window.visualViewport;
  const width = viewport?.width ?? window.innerWidth;
  const height = viewport?.height ?? window.innerHeight;
  const top = viewport?.offsetTop ?? 0;
  const rect = contextPopup.value.getBoundingClientRect();
  const padding = 8;
  popupPosition.value = {
    x: Math.max(padding, Math.min(contextMenu.value.x, width - rect.width - padding)),
    y: Math.max(top + padding, Math.min(contextMenu.value.y, top + height - rect.height - padding)),
  };
};
const showMessageMenu = (message: Message, event: MouseEvent) => {
  selectedMessage.value = message;
  contextMenu.value = { visible: true, x: event.clientX, y: event.clientY };
  void placeMessageMenu();
};

const selectMessage = (message: Message) => {
  contextMenu.value.visible = false;
  isSelectionMode.value = true;
  const set = selectedMessages.value;
  if (set.has(message.id)) set.delete(message.id);
  else set.add(message.id);
};

const handleMessagePointerDown = (message: Message, event: PointerEvent) => {
  if (event.button !== 0 || (event.target as Element)?.closest('a, button, input, video, audio')) return;
  wasLongPress = false;
  longPressTargetId = message.id;
  longPressTimer = setTimeout(() => {
    longPressTimer = null;
    wasLongPress = true;
    if (isSelectionMode.value) selectMessage(message);
    else showMessageMenu(message, event);
  }, LONG_PRESS_DURATION);
};

const handleMessagePointerUp = () => {
  if (longPressTimer) {
    clearTimeout(longPressTimer);
    longPressTimer = null;
  }
};

const handleMessageClick = (message: Message, event: MouseEvent) => {
  const targetId = longPressTargetId;
  longPressTargetId = null;

  if (wasLongPress) {
    wasLongPress = false;
    if (targetId === message.id) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
  }

  if (event.ctrlKey || event.metaKey) {
    event.preventDefault();
    const set = selectedMessages.value;
    if (set.has(message.id)) set.delete(message.id);
    else set.add(message.id);
    if (set.size === 0) isSelectionMode.value = false;
    return;
  }
  if (isSelectionMode.value) {
    const set = selectedMessages.value;
    if (set.has(message.id)) set.delete(message.id);
    else set.add(message.id);
    if (set.size === 0) isSelectionMode.value = false;
  }
};

const clearSelection = () => {
  selectedMessages.value.clear();
  isSelectionMode.value = false;
};

const deleteSelectedMessages = async () => {
  const ids = Array.from(selectedMessages.value);
  if (!ids.length) return;
  try {
    await Promise.all(ids.map((id) => messageActionsApi.delete(id)));
    messages.value = messages.value.filter((m) => !ids.includes(m.id));
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : typeof error === "object" && error && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Не удалось удалить сообщение")
          : "Не удалось удалить сообщение";
    const isForbidden = /^(Вы можете удалять только свои сообщения|Нельзя удалять чужие сообщения|permission|forbidden)/i.test(message);
    if (isForbidden) {
      toast.show("Нельзя удалять чужие сообщения", "warning");
    }
  } finally {
    clearSelection();
  }
};

const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement | null;
  if (!target) return;
  if (target.closest(".attach-menu") || target.closest(".emoji-picker") || target.closest(".context-popup") || target.closest(".attach-picker-modal")) return;
  if (isSelectionMode.value) {
    const clickedOnMessage = target.closest(".message[data-message-id]");
    if (!clickedOnMessage) {
      clearSelection();
    }
  }
  wasLongPress = false;
  longPressTargetId = null;
  showAttachMenu.value = false;
  showEmojiPicker.value = false;
  contextMenu.value.visible = false;
};

const handleInnerClick = (event: Event, handler: () => void) => {
  if (isSelectionMode.value || wasLongPress) {
    event.preventDefault();
    return;
  }
  handler();
};

const handleInnerLinkClick = (event: MouseEvent) => {
  if (isSelectionMode.value || wasLongPress) {
    event.preventDefault();
  }
};

const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === "Escape" && isSelectionMode.value) {
    clearSelection();
  }
};

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value;
  showAttachMenu.value = false;
};

const insertEmoji = (emoji: string) => {
  composerText.value += emoji;
  showEmojiPicker.value = false;
};

const toggleAttachMenu = () => {
  showAttachMenu.value = !showAttachMenu.value;
  showEmojiPicker.value = false;
};

const addPendingAttachment = (
  attachment:
    | { kind: "anime"; id: number; title_ru?: string; title_en?: string; poster_url?: string | null }
    | { kind: "playlist"; id: number; title?: string; cover_image?: string | null; items_count?: number }
    | { kind: "file"; file: File; mediaType: "image" | "video" | "file" }
) => {
  pendingAttachments.value.push(attachment);
};

const removePendingAttachment = (index: number) => {
  pendingAttachments.value.splice(index, 1);
};

const clearPendingAttachments = () => {
  pendingAttachments.value = [];
};

const messageInputEl = ref<HTMLTextAreaElement>();

const TEXTAREA_MAX_HEIGHT = 100;

const autoResizeTextarea = (event: Event) => {
  const el = event.target as HTMLTextAreaElement;
  el.style.height = "auto";
  const next = Math.min(el.scrollHeight, TEXTAREA_MAX_HEIGHT);
  el.style.height = next + "px";
  el.style.overflowY = el.scrollHeight > TEXTAREA_MAX_HEIGHT ? "auto" : "hidden";
};

const resetTextareaHeight = () => {
  const el = messageInputEl.value;
  if (!el) return;
  el.style.height = "auto";
  el.style.overflowY = "hidden";
};

const onInputKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && editingMessage.value) { event.preventDefault(); cancelEdit(); return; }
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    if (composerText.value.trim()) sendMessage();
  }
};

let chatConnection: ChatConnection | null = null;
let connectionKey = "";
let eventCursor: number | null = null;
let catchingUp = false;
let catchupTimer: ReturnType<typeof setInterval> | undefined;
const deletedMessages = new Map<number, number>();
let clearedThroughSeq = 0;
const historyCursor = ref<number | null>(null);
const loadingOlder = ref(false);
let restoreSequence = 0;
const reloadRestoredHistory = async () => {
  if (!chat.value) return;
  const id = chat.value.id, kind = chat.value.type, generation = loadGeneration;
  const { data } = await apiClient.get(`/social/chats/${id}/messages/`, { params: { type: kind, topic_id: props.topicId } });
  if (generation !== loadGeneration || chat.value?.id !== id || chat.value.type !== kind) return;
  deletedMessages.clear();
  clearedThroughSeq = Number(data.cleared_through_seq ?? 0);
  const queued = queuedMessages(id, kind);
  messages.value = mergeMessages(queued, data.results, deletedMessages, clearedThroughSeq);
  historyCursor.value = data.next_cursor;
  eventCursor = Math.max(eventCursor ?? 0, Number(data.event_cursor ?? 0));
  nextTick(() => { scrollToBottom(); setupMessageObserver(); });
};

const applyChatEvent = (data: Record<string, unknown>) => {
  if (data.sequence && Number(data.sequence) < restoreSequence) return;
  const incoming = data.message as Message | undefined;
  if (data.action === "new_message" || data.action === "message_ack" || data.action === "message_edited") {
    const follow = !showScrollDownBtn.value;
    if (incoming) mergeIncomingMessage(incoming);
    nextTick(() => { if (follow) scrollToBottom(); setupMessageObserver(); });
  } else if (data.action === "message_deleted") {
    const id = Number(data.message_id);
    deletedMessages.set(id, Number(data.version ?? 1));
    removeMessageLocally(id);
  } else if (data.action === "messages_read" && data.user_id !== user.value?.id) {
    const ids = new Set(data.message_ids as number[]);
    messages.value = messages.value.map(m => ids.has(m.id) ? { ...m, is_read_by_other: true } : m);
  } else if (data.action === "user_typing" && data.user_id !== user.value?.id && inCurrentTopic(data as Partial<Message>)) {
    isOtherTyping.value = !!data.is_typing;
    if (typingDebounceTimer) clearTimeout(typingDebounceTimer);
    typingDebounceTimer = window.setTimeout(() => { isOtherTyping.value = false; }, 5000);
  } else if (data.action === "chat_cleared") {
    clearedThroughSeq = Math.max(clearedThroughSeq, Number(data.cleared_through_seq ?? 0));
    messages.value = mergeMessages(messages.value, [], deletedMessages, clearedThroughSeq);
  } else if (data.action === "chat_restored") {
    if (Number(data.sequence) <= restoreSequence) return;
    restoreSequence = Number(data.sequence);
    void reloadRestoredHistory().catch(() => {});
  } else if (data.action === "member_updated" || data.action === "chat_updated") {
    void refreshChatDetail();
  }
};

const catchUp = async () => {
  if (catchingUp || eventCursor === null || !chat.value) return;
  catchingUp = true;
  const id = chat.value.id;
  const kind = chat.value.type;
  const generation = loadGeneration;
  try {
    let more = true;
    while (more && generation === loadGeneration) {
      const response: { data: { events: Record<string, unknown>[]; cursor: number; has_more: boolean } } = await apiClient.get(`/social/chats/${id}/events/`, { params: { type: kind, after: eventCursor } });
      const data = response.data;
      if (generation !== loadGeneration) return;
      for (const event of data.events) applyChatEvent(event);
      eventCursor = data.cursor;
      more = data.has_more;
    }
  } catch { /* retained cursor is retried on the next connection/tick */ }
  finally { catchingUp = false; }
};

const loadOlderMessages = async () => {
  if (loadingOlder.value || !historyCursor.value || !chat.value) return;
  loadingOlder.value = true;
  const id = chat.value.id;
  const generation = loadGeneration;
  const el = messagesContainer.value;
  const height = el?.scrollHeight ?? 0;
  try {
    const { data } = await apiClient.get(`/social/chats/${id}/messages/`, { params: { type: chat.value.type, topic_id: props.topicId, before: historyCursor.value } });
    if (generation !== loadGeneration) return;
    messages.value = mergeMessages(messages.value, data.results, deletedMessages, clearedThroughSeq);
    historyCursor.value = data.next_cursor;
    await nextTick();
    if (el) el.scrollTop += el.scrollHeight - height;
    setupMessageObserver();
  } finally { loadingOlder.value = false; }
};

const connectWebSocket = () => {
  if (!chat.value || chatNotFound.value || isFranchiseDiscussion.value) return;
  const id = chat.value.id;
  const kind = chat.value.type;
  const key = `${kind}:${id}:${props.topicId ?? ""}`;
  if (connectionKey === key && chatConnection) { chatConnection.start(); return; }
  disconnectWebSocket();
  connectionKey = key;
  chatConnection = new ChatConnection({
    url: () => `${getMediaBaseUrl().replace(/^http/, "ws")}/ws/chat/${id}/?type=${kind}${props.topicId !== undefined ? `&topic_id=${props.topicId}` : ""}`,
    protocols: () => webSocketProtocols(localStorage.getItem("anilux_access_token_v1") || ""),
    state: connected => { wsConnected.value = connected; },
    denied: code => {
      if (code === 4001) {
        void apiClient.get(`/social/chats/${id}/`, { params: { type: kind } }).then(() => {
          if (chat.value?.id === id && chat.value?.type === kind) { disconnectWebSocket(); connectWebSocket(); }
        }).catch(() => {});
      } else revokeAccess();
    },
    message: data => {
      if (data.action === "init") {
        clearedThroughSeq = Math.max(clearedThroughSeq, Number(data.cleared_through_seq ?? 0));
        const queued = queuedMessages(id, kind);
        messages.value = mergeMessages([...messages.value, ...queued], ((data.messages || []) as Message[]).filter(inCurrentTopic), deletedMessages, clearedThroughSeq);
        historyCursor.value = data.next_cursor as number | null;
        if (eventCursor === null) eventCursor = Number(data.event_cursor ?? 0);
        void catchUp();
        nextTick(() => {
          const anchor = Number(route.query.message);
          if (Number.isSafeInteger(anchor) && anchor > 0) void scrollToMessage(anchor);
          else if (!showScrollDownBtn.value) scrollToBottom();
          setupMessageObserver();
        });
      } else applyChatEvent(data);
    },
  });
  chatConnection.start();
  catchupTimer = setInterval(() => { if (document.visibilityState === "visible") void catchUp(); }, 20000);
};

const mergeIncomingMessage = (incoming?: Partial<Message>) => {
  if (!incoming?.id) return;
  if (inCurrentTopic(incoming)) messages.value = mergeMessages(messages.value, [incoming as Message], deletedMessages, clearedThroughSeq);
  if (incoming.id > 0 && incoming.sender_id === user.value?.id && incoming.client_message_id) {
    for (const [id, pending] of pendingSends) if (pending.message.client_message_id === incoming.client_message_id) finishPendingSend(id);
  }
};
const removeMessageLocally = (id?: number) => {
  if (id) messages.value = messages.value.filter(m => m.id !== id);
};
const disconnectWebSocket = () => {
  chatConnection?.stop();
  chatConnection = null;
  connectionKey = "";
  clearInterval(catchupTimer);
  cleanupRealtime();
  isOtherTyping.value = false;
};
const revokeAccess = () => {
  chatNotFound.value = true; messages.value = []; chat.value = null;
  showSettings.value = false; showSearch.value = false; showForward.value = false;
  disconnectWebSocket();
};

const removeUnavailableGroup = () => {
  const missingId = Number(currentChatId.value || props.chatId);
  groupChatStore.removeGroupChatFromList(missingId);
  toast.success("Группа удалена из списка чатов");
  void router.replace("/chats");
};

/** Единая точка очистки таймеров/наблюдателей realtime-слоя. */
const cleanupRealtime = () => {
  if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
  if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null; }
  if (typingDebounceTimer) { clearTimeout(typingDebounceTimer); typingDebounceTimer = null; }
  clearAnimeSearch();
  if (longPressTimer) { clearTimeout(longPressTimer); longPressTimer = null; }
  if (messageObserver) { messageObserver.disconnect(); messageObserver = null; }
};

const { subscribe: subscribeGlobal } = useGlobalWebSocket();
let globalUnsubscribers: (() => void)[] = [];
let detailRefresh: Promise<void> | null = null;
const refreshChatDetail = () => {
  if (detailRefresh) return detailRefresh;
  const current = chat.value;
  if (!current) return;
  const generation = loadGeneration;
  detailRefresh = (async () => {
    try {
      const { data } = await apiClient.get(`/social/chats/${current.id}/`, { params: { type: current.type } });
      if (generation === loadGeneration && chat.value?.id === current.id) chat.value = data;
    } catch { /* Catch-up or the next membership event retries the refresh. */ }
    finally { detailRefresh = null; }
  })();
  return detailRefresh;
};

const subscribeToGlobalChatEvents = () => {
  unsubscribeFromGlobalChatEvents();
  globalUnsubscribers = ["new_message", "message_edited", "message_deleted", "chat_cleared", "chat_restored", "messages_read", "chat_deleted", "access_revoked", "member_updated", "chat_updated"].map(action => subscribeGlobal(action, raw => {
    const event = raw as unknown as Record<string, unknown>;
    if (Number(event.chat_id) !== chat.value?.id || event.chat_type !== chat.value?.type) return;
    if (action === "chat_deleted" || action === "access_revoked") { revokeAccess(); return; }
    if (action === "member_updated" || action === "chat_updated") { void refreshChatDetail(); return; }
    if (!wsConnected.value) applyChatEvent(event);
  }));
};

const unsubscribeFromGlobalChatEvents = () => {
  globalUnsubscribers.forEach((unsub) => unsub());
  globalUnsubscribers = [];
};

const sendTypingStart = () => chatConnection?.send({ action: "typing_start" });
const sendTypingStop = () => chatConnection?.send({ action: "typing_stop" });
const handleTyping = () => {
  sendTypingStart();
  if (typingDebounceTimer) clearTimeout(typingDebounceTimer);
  typingDebounceTimer = window.setTimeout(sendTypingStop, 3000);
};

const applyThemeToDom = (theme: Record<string, unknown>) => {
  if (!theme) return;
  const root = messagesContainer.value?.closest<HTMLElement>(".chat-detail") || document.documentElement;
  const set = (name: string, value: unknown, suffix = "") => {
    if (value === undefined || value === null) return;
    root.style.setProperty(name, `${value}${suffix}`);
  };

  set("--chat-msg-mine-bg", theme.message_color_mine);
  set("--chat-msg-other-bg", theme.message_color_other);
  set("--chat-msg-mine-text", theme.message_text_color_mine);
  set("--chat-msg-other-text", theme.message_text_color_other);
  set("--chat-font-size", theme.font_size_px, "px");
  set("--chat-font-family", theme.font_family);
  set("--chat-font-weight", theme.font_weight);
  set("--chat-bubble-radius", theme.bubble_border_radius, "px");
  if (theme.bubble_shadow !== undefined) {
    root.style.setProperty("--chat-bubble-shadow", theme.bubble_shadow ? "0 2px 8px rgba(0,0,0,0.3)" : "none");
  }
  set("--chat-anime-card-radius", theme.anime_card_border_radius, "px");
  set("--chat-playlist-card-radius", theme.playlist_card_border_radius, "px");
  set("--chat-bg", theme.background_color);
  set("--chat-header-bg", theme.header_color);
  set("--chat-input-bg", theme.input_color);
  set("--chat-accent", theme.accent_color);
};

/** Обои и тема всегда перечитываются с сервера (единый источник правды). */
const refreshChatAppearance = async () => {
  const chatId = currentChatId.value;
  const generation = loadGeneration;
  if (!chatId || !chat.value) return;
  const [wallpaperRes, themeRes] = await Promise.allSettled([
    apiClient.get(`/social/chat-settings/${chat.value.type}/${chatId}/wallpaper/`),
    apiClient.get(`/social/chat-settings/${chat.value.type}/${chatId}/theme/`),
  ]);
  if (generation !== loadGeneration || chatId !== currentChatId.value) return;
  if (wallpaperRes.status === "fulfilled") {
    currentWallpaper.value = wallpaperRes.value.data?.wallpaper || null;
  }
  if (themeRes.status === "fulfilled") {
    const theme = themeRes.value.data?.theme || null;
    currentTheme.value = theme as ChatTheme | null;
    if (theme) {
      applyThemeToDom(theme);
    } else {
      clearThemeFromDom();
    }
  }
};
let chatFetchAbort: AbortController | null = null;

let loadGeneration = 0;
const loadChat = async () => {
  cancelEdit();
  let id = currentChatId.value;
  const generation = ++loadGeneration;
  chatFetchAbort?.abort();
  const ac = new AbortController();
  chatFetchAbort = ac;
  loadingMessages.value = true;
  chatNotFound.value = false;
  try {
    if (!id && (props.franchiseId || activeFranchiseId.value)) {
      const { data } = await apiClient.get(`/social/franchise/${props.franchiseId || activeFranchiseId.value}/discussion/`, { signal: ac.signal });
      if (generation !== loadGeneration) return;
      id = data.id; activeChatId.value = id;
    }
    if (!id) return;
    if (user.value?.id) await hydrateChatOutbox(user.value.id).catch(() => {});
    if (generation !== loadGeneration || ac.signal.aborted) return;
    const { data } = await apiClient.get(`/social/chats/${id}/`, { signal: ac.signal, params: { type: props.chatType || undefined } });
    if (generation !== loadGeneration || ac.signal.aborted) return;
    const detail = await joinOpenedDiscussion(data as ChatDetail, ac.signal);
    if (generation !== loadGeneration || ac.signal.aborted) return;
    chat.value = detail;
    void refreshChatAppearance().catch(() => {});
    window.setTimeout(() => {
      if (generation === loadGeneration && user.value?.id) void loadUserPlaylists();
    }, 0);
    if (eventCursor === null && !isFranchiseDiscussion.value) {
      try {
        const { data: history } = await apiClient.get(`/social/chats/${id}/messages/`, {
          signal: ac.signal, timeout: 10000,
          params: { type: chat.value.type, topic_id: props.topicId },
        });
        if (generation !== loadGeneration || ac.signal.aborted) return;
        clearedThroughSeq = Math.max(clearedThroughSeq, Number(history.cleared_through_seq ?? 0));
        messages.value = mergeMessages([...messages.value, ...queuedMessages(id, chat.value.type)],
          history.results, deletedMessages, clearedThroughSeq);
        historyCursor.value = history.next_cursor;
        eventCursor = Number(history.event_cursor ?? 0);
        nextTick(() => {
          const anchor = Number(route.query.message);
          if (Number.isSafeInteger(anchor) && anchor > 0) void scrollToMessage(anchor);
          else scrollToBottom();
          setupMessageObserver();
        });
      } catch {
        if (generation === loadGeneration && !ac.signal.aborted) toast.error("Не удалось загрузить историю сообщений");
      }
    }
  } catch (error) {
    if (generation === loadGeneration && !ac.signal.aborted) chatNotFound.value = true;
  } finally {
    if (generation === loadGeneration) {
      loadingMessages.value = false;
      chatFetchAbort = null;
    }
  }
};

const resolvePosterUrl = (raw?: string | null) => getMediaUrl(raw) || "/placeholder-anime.jpg";

const selectAttachAnime = (anime: AttachAnimeItem) => {
  showAttachAnime.value = false;
  addPendingAttachment({
    kind: "anime",
    id: anime.id,
    title_ru: anime.title_ru,
    title_en: anime.title_en || anime.title_jp,
    poster_url: anime.poster_url || anime.poster_image_url || null,
  });
};

const loadUserPlaylists = async () => {
  if (Date.now() - playlistsLoadedAt.value < 60_000 && userPlaylists.value.length) return;
  if (playlistsRequest) return playlistsRequest;
  playlistsLoading.value = true;
  playlistsRequest = apiClient.get("/playlists/playlists/my/", { params: { page: 1, page_size: 20 } })
    .then(({ data }) => {
      userPlaylists.value = Array.isArray(data) ? data : data?.results || [];
      playlistsLoadedAt.value = Date.now();
    })
    .catch((e) => {
      console.error("Failed to load playlists:", e);
      if (!userPlaylists.value.length) userPlaylists.value = [];
    })
    .finally(() => {
      playlistsLoading.value = false;
      playlistsRequest = null;
    });
  return playlistsRequest;
};

const selectAttachPlaylist = (playlist: AttachPlaylistItem) => {
  showAttachPlaylist.value = false;
  addPendingAttachment({
    kind: "playlist",
    id: playlist.id,
    title: playlist.title || playlist.name,
    cover_image: playlist.cover_image || null,
    items_count: playlist.items_count,
  });
};

const attachFile = () => attachFileInput.value?.click();

const handleAttachFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement;
  const files = Array.from(input.files || []);
  input.value = "";
  if (!files.length || !currentChatId.value) return;
  const sizeError = validateMessageFiles([
    ...pendingAttachments.value.filter(a => a.kind === 'file').map(a => a.file), ...files,
  ]);
  if (sizeError) { toast.error(sizeError); return; }
  const prepared = await prepareMediaFiles(files);
  for (const item of prepared) {
    addPendingAttachment({ kind: "file", file: item.file, mediaType: item.kind });
  }
};

const persistingSend = ref(false);
const sendMessage = async () => {
  if (editingMessage.value) { await saveEdit(); return; }
  if (persistingSend.value) return;
  const text = newMessage.value.trim();
  if (!text && pendingAttachments.value.length === 0) return;
  const sizeError = validateMessageFiles(pendingAttachments.value.filter(a => a.kind === 'file').map(a => a.file));
  if (sizeError) { toast.error(sizeError); return; }
  const chatId = currentChatId.value;
  if (!chatId || loadingMessages.value || chat.value?.id !== chatId) return;
  const generation = loadGeneration, kind = chat.value.type;
  const owner = user.value?.id;
  if (!owner) return;
  const hasFiles = pendingAttachments.value.some((a) => a.kind === "file");
  const formData = new FormData();
  formData.append("chat_id", String(chatId));
  formData.append("chat_type", chat.value?.type || props.chatType || "group");
  const commandId = crypto.randomUUID();
  formData.append("client_message_id", commandId);
  if (props.topicId !== undefined) formData.append("topic_id", String(props.topicId));
  if (text) formData.append("text", text);
  if (replyToMessage.value?.id) formData.append("reply_to", String(replyToMessage.value.id));

  const animeIds = pendingAttachments.value.filter((a) => a.kind === "anime").map((a) => a.id);
  const playlistIds = pendingAttachments.value.filter((a) => a.kind === "playlist").map((a) => a.id);
  const files = pendingAttachments.value.filter((a) => a.kind === "file") as Array<{ kind: "file"; file: File; mediaType: "image" | "video" | "file" }>;

  pendingAttachments.value.filter(item => item.kind === "excerpt").forEach(item => formData.append("excerpt_ids[]", String(item.id)));
  animeIds.forEach((id) => formData.append("anime_ids[]", String(id)));
  playlistIds.forEach((id) => formData.append("playlist_ids[]", String(id)));

  files.forEach((item, index) => {
    formData.append(`media_${index}`, item.file);
  });

  const firstFile = files[0];
  const urls = files.map(f => URL.createObjectURL(f.file));
  const tempMessage: Message = {
    id: nextTemporaryMessageId(),
    client_message_id: commandId,
    send_status: "pending",
    text,
    sender_id: user.value?.id || 0,
    sender_username: authStore.user?.username || "",
    sender_avatar: authStore.user?.avatar || undefined,
    chat_id: chatId,
    topic_id: props.topicId,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    reply_to: replyToMessage.value?.id,
    reply_to_message: replyToMessage.value
      ? {
          id: replyToMessage.value.id,
          sender_id: replyToMessage.value.sender_id,
          sender_username: replyToMessage.value.sender_username || "",
          sender_avatar: replyToMessage.value.sender_avatar || undefined,
          text: replyToMessage.value.text,
          created_at: replyToMessage.value.created_at,
          media: replyToMessage.value.media || null,
          media_type: replyToMessage.value.media_type || null,
        }
      : undefined,
    is_read_by_other: false,
    read_count: 0,
    is_read: true,
    is_edited: false,
    is_pinned: false,
    pinned_at: null,
    pinned_by_username: null,
    media: urls[0],
    media_type: firstFile ? firstFile.mediaType : undefined,
    attachments: [...files.map((f, index) => ({
      id: -(index + 1),
      type: f.mediaType,
      file_url: urls[index],
      file_name: f.file.name,
      file_size: f.file.size,
      mime_type: f.file.type,
    })), ...pendingAttachments.value.filter(a => a.kind === 'anime' || a.kind === 'playlist' || a.kind === 'excerpt').map(a => ({
      id: -a.id,
      type: a.kind,
      object_id: a.id,
      data: a.kind === 'excerpt' ? { ...a.excerpt } : a.kind === 'anime'
        ? { id: a.id, title_ru: a.title_ru, title_en: a.title_en, poster_url: a.poster_url }
        : { id: a.id, title: a.title, items_count: a.items_count, posters: a.cover_image ? [a.cover_image] : [] },
    }))],
    is_recurring: undefined,
    recurring_interval: undefined,
  };

  if (hasFiles) {
    uploadProgress.value = 0;
  }

  try {
    persistingSend.value = true;
    await storePendingSend(tempMessage.id, { formData, chatId, chatType: kind, message: tempMessage, urls });
  } catch {
    alert('Не удалось сохранить отправку на устройстве. Освободите место и попробуйте ещё раз. Текст и файлы сохранены в форме.');
    persistingSend.value = false;
    return;
  }
  if (generation !== loadGeneration || user.value?.id !== owner) { persistingSend.value = false; void retryMessage(tempMessage.id); return; }
  messages.value.push(tempMessage);
  messages.value = [...messages.value];
  await nextTick();
  scrollToBottom(true);

  newMessage.value = "";
  replyToMessage.value = null;
  clearPendingAttachments();
  await nextTick();
  resetTextareaHeight();

  persistingSend.value = false;
  await nextTick();
  if (generation === loadGeneration && user.value?.id === owner) messageInputEl.value?.focus({ preventScroll: true });
  await retryMessage(tempMessage.id);
};

const pendingSends = pendingChatSends;
const retryMessage = async (id: number) => {
  const pending = pendingSends.get(id);
  if (!pending || pending.inFlight || pending.message.sender_id !== user.value?.id) return;
  pending.inFlight = true;
  pending.message.send_status = "pending";
  messages.value = messages.value.map(m => m.id === id ? { ...m, send_status: "pending" } : m);
  try {
    const { data } = await apiClient.post(`/social/chats/${pending.chatId}/messages/`, pending.formData);
    if (currentChatId.value === pending.chatId && chat.value?.type === pending.chatType && user.value?.id === pending.message.sender_id) mergeIncomingMessage({ ...data, send_status: "sent" });
    finishPendingSend(id);
  } catch {
    if (!pendingSends.has(id)) return;
    pending.message.send_status = "failed";
    messages.value = messages.value.map(m => m.id === id ? { ...m, send_status: "failed" } : m);
  } finally { pending.inFlight = false; uploadProgress.value = 0; }
};

const pluralize = (count: number, words: [string, string, string]) => {
  const cases = [2, 0, 1, 1, 1, 2];
  const mod10 = count % 10;
  const mod100 = count % 100;
  const caseIndex = mod100 > 4 && mod100 < 20 ? 2 : Math.min(mod10, 5);
  return words[caseIndex ?? 2];
};

const markMessagesAsRead = async (messageIds: number[]) => {
  const chatId = currentChatId.value;
  if (!chatId) return;
  const ids = messageIds.filter((id) => typeof id === "number" && !readMessageIds.value.has(id));
  if (!ids.length) return;
  ids.forEach((id) => readMessageIds.value.add(id));
  try {
    if (chat.value?.type === "private") {
      await apiClient.post(`/social/private-chats/${chatId}/mark_as_read/`, { message_ids: ids });
    } else {
      await apiClient.post(`/social/group-chats/${chatId}/mark_as_read/`, { message_ids: ids });
    }
  } catch (err) {
    ids.forEach((id) => readMessageIds.value.delete(id));
    console.warn("mark_as_read failed:", err);
  }
};

const getMessageReactions = (messageId: number) => {
  const message = messages.value.find(m => m.id === messageId);
  if (message?.reactions) return Object.entries(message.reactions).flatMap(([emoji, ids]) => ids.map(id => ({ emoji, user: { id } })));
  return chatExtrasStore.messageReactions?.get(messageId) || [];
};

const getGroupedReactions = (messageId: number) => {
  const reactions = getMessageReactions(messageId) as Array<Record<string, unknown>>;
  const counts = new Map<string, number>();
  for (const r of reactions || []) {
    if (!r || typeof r !== "object") continue;
    const emoji = String(r.emoji || "");
    if (!emoji) continue;
    counts.set(emoji, (counts.get(emoji) || 0) + Number(r.count ?? 1));
  }
  return [...counts.entries()].map(([emoji, count]) => ({ emoji, count }));
};

const getMessageAuthorColor = (senderId: number | undefined) => {
  if (!senderId) return "var(--text-tertiary)";
  const colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#feca57", "#ff9ff3", "#54a0ff", "#5f27cd"];
  const index = senderId % colors.length;
  return colors[index < 0 ? -index : index];
};

const handleReaction = async (messageId: number, emoji: string) => {
  contextMenu.value.visible = false;
  const message = messages.value.find(m => m.id === messageId);
  const previous = message?.reactions
    ? Object.fromEntries(Object.entries(message.reactions).map(([key, ids]) => [key, [...ids]]))
    : undefined;
  if (message && user.value?.id) {
    const ownId = user.value.id;
    const next: Record<string, number[]> = {};
    for (const [symbol, ids] of Object.entries(message.reactions || {})) {
      const remaining = ids.filter(id => Number(id) !== Number(ownId));
      if (remaining.length) next[symbol] = remaining;
    }
    next[emoji] = [...(next[emoji] || []), ownId];
    message.reactions = next;
  }
  try {
    const { data } = await messageActionsApi.addReaction(messageId, emoji);
    if (message) message.reactions = data.reactions;
  } catch {
    if (message && previous) message.reactions = previous;
    toast.error('Не удалось изменить реакцию');
  }
};

const scrollToReply = async (quote: NonNullable<Message['reply_to_message']>) => {
  if (props.topicId !== undefined && quote.topic_id !== undefined && quote.topic_id !== props.topicId &&
      !(props.topicIsGeneral && quote.topic_id == null)) {
    await router.replace({ query: { ...route.query, topic: quote.topic_slug || 'general', message: String(quote.id) } });
    return;
  }
  await scrollToMessage(quote.id);
};
const scrollToMessage = async (messageId: number) => {
  if (!chat.value) return;
  const generation = loadGeneration;
  if (!messages.value.some(m => m.id === messageId)) {
    try {
      const { data } = await apiClient.get(`/social/chats/${chat.value.id}/messages/`, {
        params: { type: chat.value.type, topic_id: props.topicId, around: messageId },
      });
      if (generation !== loadGeneration) return;
      messages.value = mergeMessages(messages.value, data.results, deletedMessages, clearedThroughSeq);
      const cursor = data.next_cursor as number | null;
      if (cursor !== null) historyCursor.value = Math.min(historyCursor.value ?? cursor, cursor);
      await nextTick();
    } catch { toast.error('Сообщение недоступно'); return; }
  }
  await timeline.value?.scrollToMessage(messageId);
  const el = messagesContainer.value?.querySelector(`[data-message-id="${messageId}"]`);
  el?.scrollIntoView({ behavior: "smooth", block: "center" });
};
defineExpose({ scrollToMessage });

const setupMessageObserver = () => {
  messageObserver?.disconnect();
  messageObserver = new IntersectionObserver(entries => {
    if (document.visibilityState !== 'visible') return;
    const ids = entries.filter(e => e.isIntersecting).map(e => Number((e.target as HTMLElement).dataset.messageId))
      .filter(id => id > 0 && !readMessageIds.value.has(id));
    if (ids.length) void markMessagesAsRead(ids);
  }, { threshold: 0.5, root: messagesContainer.value });
  messagesContainer.value?.querySelectorAll('.message[data-message-id]').forEach(el => messageObserver?.observe(el));
};

const cancelEdit = () => {
  editAbort?.abort(); editAbort = null;
  editingMessage.value = null; editText.value = ''; savingEdit.value = false;
};

const handleEdit = async (message: Message | null) => {
  if (!message || message.sender_id !== user.value?.id || message.id <= 0) return;
  cancelEdit();
  editingMessage.value = { ...message }; editText.value = message.text || '';
  contextMenu.value.visible = false; showAttachMenu.value = false;
  await nextTick(); messageInputEl.value?.focus();
};

const saveEdit = async () => {
  const target = editingMessage.value;
  if (!target || savingEdit.value || !editText.value.trim() || !chat.value) return;
  const generation = loadGeneration, kind = chat.value.type, chatId = chat.value.id, topic = props.topicId;
  const controller = new AbortController(); editAbort = controller; savingEdit.value = true;
  try {
    const { data } = await apiClient.post(`/social/messages/${target.id}/edit/`,
      { text: editText.value.trim(), version: target.version }, { signal: controller.signal });
    if (generation !== loadGeneration || editingMessage.value?.id !== target.id) return;
    mergeIncomingMessage(data); cancelEdit();
  } catch (error) {
    if (controller.signal.aborted || generation !== loadGeneration) return;
    const status = (error as { response?: { status?: number } }).response?.status;
    if (status === 409) {
      try {
        const { data } = await apiClient.get(`/social/chats/${chatId}/messages/`,
          { params: { type: kind, topic_id: topic, around: target.id }, signal: controller.signal });
        const latest = (data.results as Message[]).find(message => message.id === target.id);
        if (latest && generation === loadGeneration && editingMessage.value?.id === target.id) {
          mergeIncomingMessage(latest); editingMessage.value = { ...latest };
        }
      } catch { /* Keep the unsaved text and original version until refresh succeeds. */ }
      toast.show('Сообщение изменилось на другом устройстве. Проверьте новую версию и повторите сохранение.', 'warning');
    } else {
      toast.show('Не удалось сохранить изменение. Текст сохранён в форме.', 'warning');
    }
  } finally {
    if (editAbort === controller) { editAbort = null; savingEdit.value = false; }
  }
};

const handleReply = (message: Message | null) => {
  if (!message) return;
  cancelEdit();
  replyToMessage.value = message;
  contextMenu.value.visible = false;
};

const cancelReply = () => { replyToMessage.value = null; };

const handleDelete = async (messageId: number) => {
  contextMenu.value.visible = false;
  try {
    await messageActionsApi.delete(messageId);
    messages.value = messages.value.filter((m) => m.id !== messageId);
  } catch (error: unknown) {
    const message =
      error instanceof Error
        ? error.message
        : typeof error === "object" && error && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? "Не удалось удалить сообщение")
          : "Не удалось удалить сообщение";
    const isForbidden = /^(Вы можете удалять только свои сообщения|permission|forbidden)/i.test(message);
    if (isForbidden) {
      toast.show("Нельзя удалять чужие сообщения", "warning");
    }
  }
};

const handleForwardComplete = () => { showForward.value = false; };

const handleInvite = () => { showInvite.value = true; };

/** Снять с :root все переменные темы чата. */
const clearThemeFromDom = () => {
  const root = messagesContainer.value?.closest<HTMLElement>(".chat-detail") || document.documentElement;
  [
    "--chat-msg-mine-bg",
    "--chat-msg-other-bg",
    "--chat-msg-mine-text",
    "--chat-msg-other-text",
    "--chat-bubble-radius",
    "--chat-bubble-shadow",
    "--chat-anime-card-radius",
    "--chat-playlist-card-radius",
    "--chat-font-size",
    "--chat-font-family",
    "--chat-font-weight",
    "--chat-bg",
    "--chat-header-bg",
    "--chat-input-bg",
    "--chat-accent",
  ].forEach((name) => root.style.removeProperty(name));
};

const handleSettingsChanged = (payload?: unknown) => {
  const p = payload as { type?: string; custom_name?: string } | undefined;

  if (p?.type === "wallpaper" || p?.type === "theme") {
    void refreshChatAppearance();
    return;
  }

  if (p?.type === "organize" && chat.value && "custom_name" in (p || {})) {
    chat.value = {
      ...chat.value,
      name: p.custom_name?.trim() || chat.value.name || "",
    };
  }

  const id = currentChatId.value;
  if (!id) return;
  void apiClient
    .get(`/social/chats/${id}/`, { params: { type: props.chatType || undefined } })
    .then(({ data }) => {
      if (currentChatId.value === id && chat.value) {
        chat.value = { ...chat.value, ...data } as ChatDetail;
      }
    })
    .catch(() => {});
};

const goToPost = (postId: number) => { router.push(`/posts/${postId}`); };

const loadFranchiseBySlug = async (slug: string): Promise<boolean> => {
  try {
    for (const params of [{ slug }, { search: slug.replace(/-/g, " ") }]) {
      const res = await apiClient.get("/anime/franchises/", { params });
      const results = res.data?.results || [];
      if (results.length > 0) {
        franchiseData.value = results[0];
        activeFranchiseId.value = results[0].id;
        return true;
      }
    }
  } catch { /* ignore */ }
  return false;
};

const loadAnimeChatBySlug = async (slug: string): Promise<boolean> => {
  try {
    for (const params of [{ slug }, { search: slug.replace(/-/g, " ") }]) {
      const res = await apiClient.get("/anime/", { params });
      const results = res.data?.results || [];
      if (results.length > 0) {
        const anime = results[0];
        const discussionRes = await apiClient.post(`/social/anime/${anime.id}/discussion-group/join/`);
        if (discussionRes.data?.id) {
          activeChatId.value = discussionRes.data.id;
          return true;
        }
      }
    }
  } catch { /* ignore */ }
  return false;
};

let typingDebounceTimer: number | null = null;
let messageObserver: IntersectionObserver | null = null;
let reconnectTimer: number | null = null;
let heartbeatTimer: number | null = null;
const readMessages = new Set<number>();

onMounted(async () => {
  window.addEventListener('resize', placeMessageMenu);
  window.visualViewport?.addEventListener('resize', placeMessageMenu);
  window.visualViewport?.addEventListener('scroll', placeMessageMenu);
  document.addEventListener("click", handleClickOutside);
  document.addEventListener("keydown", handleKeyDown);
  const slug = route.params.slug as string | undefined;
  if (slug) {
    const num = parseInt(slug);
    if (!isNaN(num)) {
      activeChatId.value = num;
    } else {
      const found = await loadFranchiseBySlug(slug);
      if (!found) await loadAnimeChatBySlug(slug);
    }
  }
  if (currentChatId.value || activeFranchiseId.value) {
    await loadChat();
    if (currentChatId.value) {
      connectWebSocket();
      subscribeToGlobalChatEvents();
    }
  }
  nextTick(() => resetTextareaHeight());
});

onUnmounted(() => {
  window.removeEventListener('resize', placeMessageMenu);
  window.visualViewport?.removeEventListener('resize', placeMessageMenu);
  window.visualViewport?.removeEventListener('scroll', placeMessageMenu);
  cancelEdit();
  ++loadGeneration;
  chatFetchAbort?.abort();
  document.removeEventListener("click", handleClickOutside);
  document.removeEventListener("keydown", handleKeyDown);
  cleanupRealtime();
  disconnectWebSocket();
  unsubscribeFromGlobalChatEvents();
});

watch(() => [props.chatId, props.chatType, props.topicId] as const, async ([newChatId, newChatType, newTopic], [oldChatId, oldChatType, oldTopic]) => {
  if (!newChatId || (newChatId === oldChatId && newChatType === oldChatType && newTopic === oldTopic)) return;
  messages.value = [];
  deletedMessages.clear();
  restoreSequence = 0;
  clearedThroughSeq = 0;
  eventCursor = null;
  clearSelection();
  cleanupRealtime();
  disconnectWebSocket();
  if (chatFetchAbort) { chatFetchAbort.abort(); chatFetchAbort = null; }
  readMessageIds.value = new Set();
  readMessages.clear();
  resetTextareaHeight();
  await loadChat();
  if (newChatId) {
    connectWebSocket();
    subscribeToGlobalChatEvents();
  }
});

watch(() => route.params.id, async (newRouteId, oldRouteId) => {
  if (props.chatId !== undefined) return;
  const parsed = newRouteId && String(newRouteId) !== 'undefined' ? parseInt(String(newRouteId), 10) : NaN;
  const targetId = !isNaN(parsed) ? parsed : undefined;
  if (targetId && newRouteId !== oldRouteId) {
    messages.value = [];
    deletedMessages.clear(); restoreSequence = 0; clearedThroughSeq = 0; eventCursor = null;
    clearSelection();
    cleanupRealtime();
    disconnectWebSocket();
    if (chatFetchAbort) { chatFetchAbort.abort(); chatFetchAbort = null; }
    readMessageIds.value = new Set();
    readMessages.clear();
    resetTextareaHeight();
    await loadChat();
    if (targetId) {
      connectWebSocket();
      subscribeToGlobalChatEvents();
    }
  }
});
</script>

<style scoped>
.chat-not-found-state {
  display: flex;
  flex: 1;
  min-height: 0;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  text-align: center;
  color: var(--text-primary);
}

.chat-not-found-state h2,
.chat-not-found-state p { margin: 0; }
.chat-not-found-state p { max-width: 460px; color: var(--text-secondary); line-height: 1.5; }
.chat-not-found-icon {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  color: var(--accent);
}
.chat-not-found-remove,
.chat-not-found-back {
  margin-top: 0.5rem;
  padding: 0.7rem 1rem;
  border: 1px solid var(--border-default);
  border-radius: 0.75rem;
  background: var(--surface-3);
  color: var(--text-primary);
  cursor: pointer;
}
.chat-not-found-remove { border-color: color-mix(in srgb, var(--danger, #ef4444) 55%, transparent); color: var(--danger, #ef4444); }
.chat-not-found-remove:hover,
.chat-not-found-back:hover { background: var(--surface-4); }

.chat-detail {
  position: relative;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface-1);
  min-height: 0;
}

/* Обои -на всю страницу чата: под шапкой, сообщениями и полем ввода */
.chat-wallpaper {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-size: cover;
  background-position: center;
}

.chat-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.65rem 1rem;
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-2);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
}

.avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--border-default);
}

.online-dot {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--success);
  border: 2px solid var(--surface-2);
}

.header-info {
  min-width: 0;
}

.chat-name {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-name.is-link {
  cursor: pointer;
  transition: color var(--duration-base) var(--ease-out);
}

.chat-name.is-link:hover,
.chat-name.is-link:focus-visible {
  color: var(--accent);
  outline: none;
}

.chat-status {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  margin: 0.15rem 0 0;
}

.chat-status .typing {
  color: var(--accent);
  font-style: italic;
}

.chat-status .online {
  color: var(--success);
}

.header-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--surface-4);
  color: var(--accent);
}

.messages-wrap {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.messages {
  position: relative;
  flex: 1;
  overflow-y: auto;
  padding: 1.75rem 1.6rem 1.75rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  min-height: 0;
  align-items: stretch;
}

.loading-state {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  color: var(--text-tertiary);
}
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--surface-5);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;

}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-messages {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
}

.day-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  width: 100%;
  padding: 0.75rem 0;
}

.day-label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--surface-1);
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
}

.messages-list {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
  gap: 0.875rem;
  padding: 0.4rem 0;
}

.message {
  position: relative;
  display: flex;
  gap: 0.5rem;
  width: 100%;
  animation: messageIn 0.2s ease-out;
  z-index: 1;
}

.message:hover,
.message:focus-within {
  z-index: 20;
}

@keyframes messageIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-body {
  position: relative;
  max-width: 75%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  z-index: 1;
  transform-origin: left top;
  transition: transform 160ms ease, z-index 0s linear 160ms;
}

.message--own .message-body {
  transform-origin: right top;
}

.message:hover .message-body,
.message:focus-within .message-body {
  z-index: 5;
  transform: scale(1.035);
  transition-delay: 0s;
}

@media (prefers-reduced-motion: reduce) {
  .message-body {
    transition: none;
  }
}

.message--own {
  flex-direction: row-reverse;
}

.message--grouped {
  margin-top: -0.125rem;
}

.message--has-reactions {
  margin-bottom: 0.35rem;
}

.message-sender-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.message-sender-avatar-placeholder {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.message-sender-name {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent);
  margin-left: 0.5rem;
}

.reply-quote {
  padding: 0.35rem 0.6rem 0.35rem 0.7rem;
  background: var(--chat-msg-other-bg, var(--surface-3));
  border-radius: var(--chat-bubble-radius, var(--radius-md));
  border-left: 2.5px solid var(--accent);
  cursor: pointer;
  margin-bottom: 0.25rem;
  transition: background 0.15s;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
  min-width: 0;
}

.message--own .reply-quote {
  background: color-mix(in srgb, var(--chat-msg-mine-bg, var(--accent)) 18%, var(--chat-msg-other-bg, var(--surface-3)));
  border-left-color: var(--accent-press);
}

.reply-quote:hover {
  background: var(--surface-4);
}

.message--own .reply-quote:hover {
  background: color-mix(in srgb, var(--chat-msg-mine-bg, var(--accent)) 28%, var(--chat-msg-other-bg, var(--surface-3)));
}

.message--other .reply-quote:hover {
  background: var(--surface-4);
}

.reply-author {
  font-size: 0.7rem;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--chat-msg-other-text, var(--text-primary));
}

.reply-text {
  font-size: 0.7rem;
  line-height: 1.25;
  color: var(--chat-msg-other-text, var(--text-secondary));
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message--own .reply-author {
  color: var(--chat-msg-mine-text, var(--text-on-accent));
}

.message--own .reply-text {
  color: var(--chat-msg-mine-text, var(--text-on-accent));
  opacity: 0.85;
}

.message-body > .reply-quote + .message-text {
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
}

.message-text {
  position: relative;
  padding: 0.55rem 0.85rem;
  background: var(--chat-msg-other-bg, var(--surface-3));
  border-radius: var(--chat-bubble-radius, var(--radius-lg));
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--chat-msg-other-text, var(--text-primary));
  word-break: break-word;
  box-shadow: var(--chat-bubble-shadow, none);
}

.message--own .message-text {
  background: var(--chat-msg-mine-bg, linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%));
  color: var(--chat-msg-mine-text, var(--text-on-accent));
  border-bottom-right-radius: var(--radius-sm);
}

.message--other .message-text {
  border-bottom-left-radius: var(--radius-sm);
}

/* Мета (время/статус) прижата к правому нижнему углу пузыря,
   текст обтекает её -как в Telegram, без жёстких распорок */
.meta-float {
  float: right;
  display: inline-flex;
  margin: 0.55rem -0.2rem -0.3rem 0.75rem;
}

.meta-float :deep(.mm) {
  margin: 0;
}

.message-image {
  max-width: 240px;
  max-height: 320px;
  border-radius: var(--radius-lg);
  object-fit: cover;
  cursor: pointer;
}

.message-media-grid {
  position: relative;
  display: inline-block;
}

.message-video {
  max-width: 240px;
  max-height: 320px;
  border-radius: var(--radius-lg);
  display: block;
}

.upload-progress {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.35rem;
}

.upload-progress-bar {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  overflow: hidden;
}

.upload-progress-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 0.2s ease;
}

.upload-progress-label {
  font-size: 0.6875rem;
  color: var(--text-tertiary);
  min-width: 2.2rem;
  text-align: right;
}

.message--own .upload-progress-bar {
  background: rgba(255, 255, 255, 0.25);
}

.message--own .upload-progress-label {
  color: rgba(255, 255, 255, 0.8);
}

.message-file {
  padding: 0.5rem 0.75rem;
  background: var(--chat-msg-other-bg, var(--surface-3));
  border-radius: var(--chat-bubble-radius, var(--radius-lg));
}

.message-file a {
  color: var(--chat-msg-other-text, var(--accent));
  font-size: 0.875rem;
  text-decoration: none;
}

.message-file a:hover {
  text-decoration: underline;
}


.reactions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.25rem;
  padding: 0.15rem 0.25rem;
  background: transparent;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
}

.reaction {
  padding: 0.15rem 0.4rem;
  background: var(--surface-3);
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  line-height: 1.2;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--text-primary);
}

.reaction:hover {
  border-color: var(--accent);
  background: var(--accent-subtle);
  transform: scale(1.05);
}

.reaction--collapsed {
  opacity: 0.6;
}

.message--own .mm {
  justify-content: flex-end;
}

.scroll-down {
  position: absolute;
  bottom: 1rem;
  right: 1rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 50%;
  color: var(--text-primary);
  cursor: pointer;
  box-shadow: var(--shadow-sm-md);
  transition: all 0.2s;
  z-index: 10;
}

.scroll-down:hover {
  background: var(--accent-subtle);
  color: var(--accent);
}

/* Зона ввода без отдельного блока: обои видны прямо за пилюлей */
.edit-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  color: var(--text-secondary);
  border-left: 3px solid var(--accent-color, #7c5cfc);
}
.edit-preview span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1; }
.edit-preview button { color: inherit; background: none; border: 0; cursor: pointer; font-size: 24px; }
.input-area {
  position: relative;
  z-index: 2;
  padding: 0.3rem 0.5rem 0.5rem;
  background: transparent;
  border-top: none;
  flex-shrink: 0;
}

.input-form {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 0.2rem;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: 22px;
  padding: 0.5rem 0.35rem;
  box-shadow: var(--shadow-sm-modal);
  transition:
    border-color 0.2s,
    box-shadow 0.2s,
    background 0.2s;
}

.input-row:focus-within {
  border-color: var(--accent);
  background: var(--surface-4);
  box-shadow: var(--border-glow);
}

.input-action {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 40px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition:
    background 0.2s,
    color 0.2s,
    transform 0.2s;
  flex-shrink: 0;
}

.input-action svg {
  width: 20px;
  height: 20px;
}

.input-action:hover:not(:disabled) {
  background: var(--accent-subtle);
  color: var(--accent);
  transform: scale(1.08);
}

.input-action:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.message-textarea {
  flex: 1;
  padding: 0.45rem 0.35rem !important;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 0.95rem;
  resize: none;
  min-height: 24px !important;
  max-height: 100px !important;
  overflow-y: hidden;
  font-family: inherit;
  outline: none;
  line-height: 1.4;
  scrollbar-width: thin;
}

.message-textarea::placeholder {
  color: var(--text-tertiary);
}

.message-textarea:hover,
.message-textarea:focus {
  border: none;
  background: transparent;
  box-shadow: none;
}

.message-textarea:disabled {
  opacity: 0.5;
}

.send-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  min-height: 40px;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent-press) 100%);
  color: var(--text-on-accent);
  cursor: pointer;
  transition:
    transform 0.2s,
    box-shadow 0.2s,
    opacity 0.2s;
  box-shadow: var(--shadow-sm-petal-sm);
  flex-shrink: 0;
}

.send-btn svg {
  width: 16px;
  height: 16px;
}

.send-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-sm-glow-sm);
  transform: scale(1.07);
}

.send-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.send-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

.attach-menu {
  position: absolute;
  bottom: calc(100% + 6px);
  left: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm-modal);
  padding: 0.5rem;
  z-index: 100;
  min-width: 180px;
}

.attach-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: all 0.2s;
  text-align: left;
}

.attach-item:hover:not(:disabled) {
  background: var(--surface-4);
  color: var(--accent);
}

.attach-item:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.attach-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.attach-picker-modal {
  background: var(--surface-2);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm-modal);
  width: 100%;
  max-width: 480px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.attach-picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.9rem 1.1rem;
  border-bottom: 1px solid var(--border-subtle);
}

.attach-picker-header h3 {
  margin: 0;
  font-size: 1rem;
  color: var(--text-primary);
}

.attach-picker-close {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  padding: 0.15rem 0.35rem;
  border-radius: var(--radius-md);
}

.attach-picker-close:hover {
  background: var(--surface-4);
  color: var(--text-primary);
}

.attach-picker-search {
  position: relative;
  padding: 0.85rem 1.1rem 0.4rem;
}

.attach-picker-search input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.55rem 2.2rem 0.55rem 0.75rem;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  background: var(--surface-4);
  color: var(--text-primary);
  font-size: 0.9rem;
  outline: none;
}

.attach-picker-search input:focus {
  border-color: var(--accent);
}

.attach-spinner {
  position: absolute;
  right: 1.6rem;
  top: 50%;
  transform: translateY(-30%);
  font-size: 0.85rem;
  pointer-events: none;
  color: var(--accent);
}

.spinner-icon {
  animation: spin 1s linear infinite;
  display: block;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.attach-picker-results {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 0.5rem 0.65rem 0.75rem;
  gap: 12px;
}

.attach-results-list {
  flex: 1;
  min-width: 0;
  min-height: 200px;
  max-height: 55vh;
  overflow-y: auto;
  padding-right: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.attach-results-list::-webkit-scrollbar {
  width: 6px;
}

.attach-results-list::-webkit-scrollbar-track {
  background: transparent;
}

.attach-results-list::-webkit-scrollbar-thumb {
  background: var(--surface-5);
  border-radius: 3px;
}

.attach-loading {
  padding: 1rem;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.attach-count {
  text-align: left;
  color: var(--text-secondary);
  font-size: 0.8rem;
  padding: 0 0.15rem 0.35rem;
  margin: 0;
  font-weight: 500;
}

.attach-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 0.875rem;
  padding: 1.25rem 0.5rem;
  margin: 0;
}

.attach-result-item {
  display: flex;
  flex-shrink: 0;
  height: auto;
  min-height: calc(60px + 1.5rem + 2px);
  overflow: hidden;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: var(--surface-3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.attach-result-item:hover {
  background: var(--surface-4);
  border-color: var(--accent);
}

.attach-poster {
  display: block;
  width: 44px;
  height: 60px;
  max-height: 60px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
  background: var(--surface-4);
}

.attach-playlist-cover {
  height: 36px;
  object-fit: cover;
}

.attach-result-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.attach-result-title {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attach-result-sub {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attach-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.6rem 0 0.2rem;
}

.attach-page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s;
}

.attach-page-btn:hover:not(:disabled) {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
  transform: scale(1.1);
}

.attach-page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.attach-page-info {
  display: flex;
  justify-content: center;
  padding: 0.5rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
  min-width: 5rem;
  text-align: center;
  color: var(--text-secondary);
  font-weight: 500;
  min-width: 3.5rem;
  text-align: center;
}

.attach-result-title {
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.attach-result-sub {
  color: var(--text-tertiary);
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.emoji-picker {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 1rem;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0.2rem;
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm-modal);
  padding: 0.75rem;
  z-index: 100;
  min-width: 240px;
  width: max-content;
}

.emoji-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1.25rem;
  transition: all 0.2s;
}

.emoji-btn:hover {
  background: var(--surface-4);
  transform: scale(1.15);
}

.context-popup {
  position: fixed;
  z-index: var(--z-modal);
  background: var(--surface-3);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm-modal);
  padding: 0.5rem;
  min-width: min(200px, calc(100vw - 16px));
  max-width: calc(100vw - 16px);
  max-height: calc(var(--viewport-height, 100dvh) - 16px);
  overflow-y: auto;
}

.reaction-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  padding: 0.5rem;
  border-bottom: 1px solid var(--border-subtle);
  margin-bottom: 0.5rem;
}

.reaction-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 1.25rem;
  transition: all 0.2s;
}

.reaction-btn:hover {
  background: var(--surface-4);
  transform: scale(1.15);
}

.context-actions {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.context-action {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-primary);
  font-size: 0.875rem;
  transition: all 0.2s;
  text-align: left;
}

.context-action:hover {
  background: var(--surface-4);
}

.context-action.danger {
  color: var(--danger);
}

.context-action.danger:hover {
  background: rgba(239, 68, 68, 0.1);
}

.pop-enter-active,
.pop-leave-active {
  transition: all 0.2s ease;
}

.pop-enter-from,
.pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
}

.pending-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem 0;
}

.pending-attachment {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--surface-4);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: 0.4rem 0.6rem;
  font-size: 0.8125rem;
  color: var(--text-primary);
  max-width: 100%;
}

.pending-poster {
  width: 32px;
  height: 44px;
  object-fit: cover;
  border-radius: var(--radius-md);
  background: var(--surface-4);
}

.pending-icon {
  font-size: 1rem;
  line-height: 1;
}

.pending-info {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.pending-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  flex-shrink: 0;
  transition: all 0.2s;
}

.pending-remove:hover {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

/* ===== Выделение сообщений ===== */
.message-body--selected {
  transition: background 0.2s ease;
}

.message-body--selected .message-text {
  background: var(--surface-4) !important;
  color: var(--text-primary) !important;
  box-shadow: 0 0 0 2px var(--accent), var(--bubble-shadow, none);
  transition: background 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
}

.message-body--selected .shared-card {
  box-shadow: 0 0 0 2px var(--accent);
  transition: box-shadow 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.message-body--selected .message-file {
  background: var(--surface-4) !important;
  box-shadow: 0 0 0 2px var(--accent);
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.message-body--selected .message-media-grid {
  outline: 2px solid var(--accent);
  outline-offset: -2px;
  border-radius: var(--radius-lg);
  transition: outline 0.2s ease;
}

.message-select-check {
  position: absolute;
  top: 0.35rem;
  left: 0.35rem;
  transform: none;
  width: 18px;
  min-width: 18px;
  max-width: 18px;
  height: 18px;
  min-height: 18px;
  max-height: 18px;
  border-radius: 50%;
  background: var(--accent);
  color: var(--text-on-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5;
  box-shadow: var(--shadow-sm-md);
  border: 2px solid var(--surface-1);
  font-size: 11px;
  transition: all 0.2s ease;
  flex-shrink: 0;
  aspect-ratio: 1 / 1;
}

.message-select-check svg {
  width: 12px;
  height: 12px;
  display: block;
  flex-shrink: 0;
}

.message--own .message-select-check {
  left: auto;
  right: 0.35rem;
  background: var(--text-on-accent);
  color: var(--accent);
  border-color: var(--accent);
}

.message--own .message-body--selected .message-text {
  box-shadow: 0 0 0 2px var(--text-on-accent), var(--bubble-shadow, none);
}


/* ===== Панель выделения ===== */
.message-select-bar {
  position: sticky;
  top: 0.5rem;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.4rem 1rem;
  margin: 0 0.75rem 0.5rem 0.75rem;
  background: rgba(var(--surface-2-rgb, 30, 30, 46), 0.85);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  gap: 0.75rem;
  animation: slideDown 0.2s ease-out;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow: var(--shadow-sm-modal);
  min-height: 44px;
  max-width: calc(100% - 1.5rem);
  margin-left: auto;
  margin-right: auto;
}

.message-select-count {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  line-height: 1.2;
  white-space: nowrap;
  flex-shrink: 0;
}

.message-select-count::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  flex-shrink: 0;
  display: inline-block;
}

.message-select-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
}


@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-12px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.message-select-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  min-width: 32px;
  max-width: 32px;
  height: 32px;
  min-height: 32px;
  max-height: 32px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s ease;
  padding: 0;
  flex-shrink: 0;
  aspect-ratio: 1 / 1;
}

.message-select-btn:hover {
  background: var(--surface-4);
  color: var(--text-primary);
  transform: scale(1.05);
}

.message-select-btn:active {
  transform: scale(0.93);
}

.message-select-btn.danger {
  color: var(--danger);
}

.message-select-btn.danger:hover {
  color: var(--danger-hover);
  background: rgba(239, 68, 68, 0.1);
}

.message-select-btn svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  display: block;
}


/* ===== Адаптив для мобильных ===== */
@media (max-width: 640px) {
  .message-select-bar {
    padding: 0.35rem 0.75rem;
    margin: 0.25rem 0.5rem 0.35rem 0.5rem;
    border-radius: var(--radius-lg);
    min-height: 38px;
    max-width: calc(100% - 1rem);
    gap: 0.5rem;
  }

  .message-select-count {
    font-size: 0.8rem;
  }

  .message-select-count::before {
    width: 6px;
    height: 6px;
  }

  .message-select-btn {
    width: 28px;
    min-width: 28px;
    max-width: 28px;
    height: 28px;
    min-height: 28px;
    max-height: 28px;
  }

  .message-select-btn svg {
    width: 14px;
    height: 14px;
  }

  .message-select-check {
    width: 16px;
    min-width: 16px;
    max-width: 16px;
    height: 16px;
    min-height: 16px;
    max-height: 16px;
    top: 0.25rem;
    left: 0.25rem;
    font-size: 9px;
    border-width: 1.5px;
  }

  .message--own .message-select-check {
    right: 0.25rem;
  }

  .message-select-check svg {
    width: 10px;
    height: 10px;
  }
}

@media (prefers-color-scheme: dark) {
  .message-select-bar {
    background: rgba(30, 30, 46, 0.88);
    border-color: rgba(255, 255, 255, 0.06);
  }
}

/* Светлая тема */
@media (prefers-color-scheme: light) {
  .message-select-bar {
    background: rgba(255, 255, 255, 0.88);
    border-color: rgba(0, 0, 0, 0.06);
  }
}


</style>
