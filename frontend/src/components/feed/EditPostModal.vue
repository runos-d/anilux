<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="edit-post-modal" @click.stop>
      <div class="modal-header">
        <h2>Редактирование поста</h2>
        <button class="close-btn" @click="$emit('close')" aria-label="Закрыть"><SakuraIcon name="x" :size="16" /></button>
      </div>

      <div class="content-area">
        <button type="button" @click="$emit('open-attach', 'excerpt')">Прикрепить отрывок</button>
        <div v-for="(row, index) in editAttachPreviewExcerpts" :key="row.id">{{ row.title || row.anime_title || 'Отрывок недоступен' }}<button type="button" @click="editAttachPreviewExcerpts.splice(index, 1)">Убрать</button></div>
        <textarea
          ref="textArea"
          v-model="text"
          class="text-input"
          placeholder="Текст поста..."
          @input="autoResize"
        ></textarea>

        <div
          class="char-count"
          :class="{ warning: text.length > 4500, error: text.length > 5000 }"
        >
          {{ text.length }}/5000
        </div>

        <label class="toggle-label">
          <span class="toggle-switch" :class="{ active: isSpoiler }">
            <span class="toggle-slider"></span>
          </span>
          <input type="checkbox" v-model="isSpoiler" class="toggle-input" />
          <span class="toggle-text">Спойлер</span>
        </label>

        <div v-if="isSpoiler" class="spoiler-settings">
          <input
            v-model="spoilerDescription"
            type="text"
            placeholder="О чём спойлер?"
            class="spoiler-for-input"
          />
        </div>

        <div class="tags-row">
          <div class="tags-chips">
            <span v-for="tag in normalizedTags" :key="tag" class="tag-chip">
              #{{ tag }}
              <button class="tag-remove" @click="removeTag(tag)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
            </span>
          </div>
          <input
            v-model="tagDraft"
            type="text"
            placeholder="тег"
            class="tag-input"
            @keydown.enter.prevent="addTagFromDraft"
            @blur="addTagFromDraft"
          />
        </div>

        <div class="compact-toolbar">
          <button type="button" class="toolbar-chip" @click="openAttach('media')">
            <SakuraIcon name="image" :size="14" /> Фото/Видео
          </button>
          <button type="button" class="toolbar-chip" @click="openAttach('anime')">
            <SakuraIcon name="anime-tv" :size="14" /> Аниме
          </button>
          <button type="button" class="toolbar-chip" @click="openAttach('playlist')">
            <SakuraIcon name="list" :size="14" /> Плейлист
          </button>
        </div>

        <div v-if="retainedMedia.length" class="media-strip">
          <div v-for="(m, idx) in retainedMedia" :key="m.id" class="media-thumb">
            <img v-if="m.media_type === 'image'" :src="m.url || m.file_url || ''" alt="" />
            <video v-else :src="m.url || m.file_url || ''" muted></video>
            <button class="remove-thumb-btn" @click="retainedMedia.splice(idx, 1)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
          </div>
        </div>
        <div v-if="editAttachPreviewMedia.length" class="media-strip">
          <div v-for="(m, idx) in editAttachPreviewMedia" :key="'em-' + idx" class="media-thumb">
            <img v-if="m.type === 'image'" :src="m.url" alt="" />
            <video v-else :src="m.url" muted></video>
            <button class="remove-thumb-btn" @click="removeEditMedia(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
          </div>
        </div>

        <div v-if="editAttachPreviewAnime.length || editAttachPreviewPlaylist.length" class="attach-chips">
          <span v-for="(a, idx) in editAttachPreviewAnime" :key="'ea-' + a.id" class="attach-chip">
            {{ a.title_ru || a.title_en }}
            <button class="remove-chip-btn" @click="removeEditAnime(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
          </span>
          <span v-for="(p, idx) in editAttachPreviewPlaylist" :key="'ep-' + p.id" class="attach-chip">
            {{ p.title }}
            <button class="remove-chip-btn" @click="removeEditPlaylist(idx)" aria-label="Удалить"><SakuraIcon name="x" :size="16" /></button>
          </span>
        </div>
      </div>

      <div class="submit-row">
        <button
          @click="savePost"
          :disabled="!canSubmit || saving"
          class="submit-btn"
        >
          {{ saving ? `Отправка ${progress}%` : "Сохранить" }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, toRaw, nextTick } from "vue";
import apiClient from "@/api/client";
import { postAccountGuard } from '@/lib/postAccount';
import { postDraftGet, postDraftPut } from '@/lib/postDrafts';
import { updatePost } from '@/lib/postPublication';
import { useAuthStore } from '@/stores/auth';
import { usePostStore } from '@/stores/posts';
const progress = ref(0);
const editClientId = ref<string>(crypto.randomUUID());
const draftOwner = useAuthStore().user?.id;
let completed = false;
let restoring = true;
let draftTimer: ReturnType<typeof setTimeout> | undefined;
const auth = useAuthStore();
import type { Excerpt } from "@/api/excerpts";
import SakuraIcon from "@/components/icons/SakuraIcon.vue";
import type { FeedPost, AnimeCard, PlaylistCard, MediaFile } from "@/api/feed";

const props = defineProps<{ post: FeedPost }>();
const emit = defineEmits<{ close: []; updated: [post: FeedPost]; "open-attach": [tab: "media" | "anime" | "playlist" | "excerpt"] }>();

const text = ref("");
const isSpoiler = ref(false);
const spoilerDescription = ref("");
const saving = ref(false);
const retainedMedia = ref<MediaFile[]>([...(props.post.media_files || [])]);
const textArea = ref<HTMLTextAreaElement | null>(null);

const tags = ref<string[]>([]);
const tagDraft = ref("");

const normalizedTags = computed(() => {
  return tags.value
    .map((t) => t.replace(/^#/, "").trim())
    .filter((t) => Boolean(t));
});

const editAttachPreviewMedia = ref<{ type: string; url: string; file: File }[]>([]);
const editAttachPreviewAnime = ref<AnimeCard[]>([]);
const editAttachPreviewExcerpts = ref<Excerpt[]>((props.post.attachments_data || []).filter(row => row.content_type === "excerpt").map(row => row.excerpt_data || ({id: Number(row.object_id), unavailable: true} as Excerpt)));
const editAttachPreviewPlaylist = ref<PlaylistCard[]>([]);

const canSubmit = computed(
  () => {
    const hasContent =
      text.value.trim().length > 0 ||
      retainedMedia.value.length > 0 ||
      editAttachPreviewMedia.value.length > 0 ||
      editAttachPreviewAnime.value.length > 0 ||
      editAttachPreviewPlaylist.value.length > 0 ||
      normalizedTags.value.length > 0 || editAttachPreviewExcerpts.value.length > 0;
    return hasContent && text.value.length <= 5000;
  },
);

const autoResize = () => {
  if (!textArea.value) return;
  textArea.value.style.height = "auto";
  textArea.value.style.height = textArea.value.scrollHeight + "px";
};

const parseRawTags = (raw: string) => {
  const parts = raw.split(/[\s,]+/);
  for (const part of parts) {
    const cleaned = part.replace(/^#/, "").trim();
    if (cleaned && !tags.value.includes(cleaned)) {
      tags.value.push(cleaned);
    }
  }
};

const addTagFromDraft = () => {
  const raw = tagDraft.value.trim();
  if (!raw) return;
  parseRawTags(raw);
  tagDraft.value = "";
};

const removeTag = (tag: string) => {
  tags.value = tags.value.filter((t) => t !== tag);
};

const openAttach = (tab: "media" | "anime" | "playlist") => {
  emit("open-attach", tab);
};

const removeEditMedia = (idx: number) => {
  const m = editAttachPreviewMedia.value[idx];
  if (m) URL.revokeObjectURL(m.url);
  editAttachPreviewMedia.value.splice(idx, 1);
};

const removeEditAnime = (idx: number) => {
  editAttachPreviewAnime.value.splice(idx, 1);
};

const removeEditPlaylist = (idx: number) => {
  editAttachPreviewPlaylist.value.splice(idx, 1);
};

const onAttachConfirmFromEdit = (
  anime: AnimeCard[],
  playlists: PlaylistCard[],
  media: { type: string; url: string; file: File }[],
  excerpts: Excerpt[] = editAttachPreviewExcerpts.value
) => {
  editAttachPreviewExcerpts.value = [...excerpts];
  editAttachPreviewAnime.value = anime.map((m) => ({ ...m }));
  editAttachPreviewPlaylist.value = playlists.map((m) => ({ ...m }));
  const oldUrls = new Set(editAttachPreviewMedia.value.map((m) => m.url));
  const newMedia = media.map((m) => ({ ...m }));
  editAttachPreviewMedia.value.forEach((m) => {
    if (!newMedia.some((s) => s.url === m.url)) URL.revokeObjectURL(m.url);
  });
  editAttachPreviewMedia.value = newMedia;
};

const savePost = async () => {
  if (!canSubmit.value || saving.value) return;
  saving.value = true;
  try {
    const fd = new FormData();
    fd.append("text", text.value);
    fd.append("is_spoiler", String(isSpoiler.value));
    if (isSpoiler.value && spoilerDescription.value.trim()) {
      fd.append("spoiler_description", spoilerDescription.value.trim());
    }

    const rawTags = normalizedTags.value.map(tag => `#${tag}`).join(" ");
    fd.set("text", [text.value, rawTags].filter(Boolean).join(" "));
    if (rawTags) {
      fd.append("hashtags", rawTags);
    }

    const owner = auth.user?.id;
    if (!owner) throw new Error('Войдите в аккаунт');
    const ensureAccount = postAccountGuard(owner);
    ensureAccount();
    await saveDraft();
    const files = editAttachPreviewMedia.value.map(item => item.file);
    fd.append('retain_media_ids', JSON.stringify(retainedMedia.value.map(item => item.id)));
    fd.append('version', String(props.post.version || 1));
    fd.append('client_edit_id', editClientId.value);

    const originalExcerptIds = (props.post.attachments_data || []).filter(row => row.content_type === 'excerpt').map(row => Number(row.object_id)).sort();
    const excerptIds = editAttachPreviewExcerpts.value.map(row => row.id);
    if (JSON.stringify([...excerptIds].sort()) !== JSON.stringify(originalExcerptIds)) fd.append('excerpt_ids', JSON.stringify(excerptIds));
    fd.append('anime_ids', JSON.stringify(editAttachPreviewAnime.value.map(item => item.id)));
    fd.append('playlist_ids', JSON.stringify(editAttachPreviewPlaylist.value.map(item => item.id)));

    const updatedPost = await updatePost(owner, props.post.id, editClientId.value, fd, files,
      retainedMedia.value.reduce((sum, item) => sum + (item.file_size || 0), 0), value => { progress.value = value; });
    ensureAccount();
    completed = true;
    if (draftTimer) clearTimeout(draftTimer);
    await postDraftPut('drafts', `${owner}:edit:${props.post.id}`);
    emit("updated", usePostStore().upsert(updatedPost));
    emit("close");
  } catch (e: unknown) {
    const err = e as {
      response?: { data?: { detail?: string } };
      message?: string;
    };
    alert(
      "Ошибка при сохранении: " + (err.response?.data?.detail || err.message),
    );
  } finally {
    saving.value = false;
  }
};

async function saveDraft() {
  if (!draftOwner || restoring || completed || String(auth.user?.id) !== String(draftOwner)) return;
  await postDraftPut('drafts', `${draftOwner}:edit:${props.post.id}`, {
    version: props.post.version || 1, clientId: editClientId.value,
    text: text.value, isSpoiler: isSpoiler.value, spoilerDescription: spoilerDescription.value,
    tags: [...tags.value], retained: retainedMedia.value.map(row => row.id),
    anime: JSON.parse(JSON.stringify(editAttachPreviewAnime.value)),
    excerpts: JSON.parse(JSON.stringify(editAttachPreviewExcerpts.value)),
    playlists: JSON.parse(JSON.stringify(editAttachPreviewPlaylist.value)),
    files: editAttachPreviewMedia.value.map(row => toRaw(row.file)),
  }).catch(() => undefined);
}
watch([editAttachPreviewExcerpts, text, isSpoiler, spoilerDescription, tags, retainedMedia, editAttachPreviewAnime, editAttachPreviewPlaylist, editAttachPreviewMedia], () => {
  if (draftTimer) clearTimeout(draftTimer);
  draftTimer = setTimeout(() => { void saveDraft(); }, 250);
}, { deep: true });
onUnmounted(() => {
  if (draftTimer) clearTimeout(draftTimer);
  void saveDraft();
  editAttachPreviewMedia.value.forEach(row => URL.revokeObjectURL(row.url));
});

onMounted(async () => {
  text.value = props.post.text || "";
  isSpoiler.value = props.post.is_spoiler ?? false;
  spoilerDescription.value =
    (props.post.spoiler_description || props.post.spoiler_for || "") as string;

  const initialTags = (props.post.hashtags || [])
    .map((t) => t.replace(/^#/, "").trim())
    .filter(Boolean);
  tags.value = initialTags;

  const initialAnime: AnimeCard[] = [];
  const seenAnimeIds = new Set<number>();
  if (props.post.anime && typeof props.post.anime === 'object' && 'id' in props.post.anime) {
    initialAnime.push(props.post.anime as AnimeCard);
    seenAnimeIds.add((props.post.anime as AnimeCard).id);
  }
  for (const attachment of props.post.attachments_data || []) {
    if (attachment.content_type === 'anime' && attachment.anime_data && !seenAnimeIds.has(attachment.anime_data.id)) {
      initialAnime.push(attachment.anime_data);
      seenAnimeIds.add(attachment.anime_data.id);
    }
  }
  editAttachPreviewAnime.value = initialAnime;

  const initialPlaylists: PlaylistCard[] = [];
  const seenPlaylistIds = new Set<string>();
  if (props.post.playlist && typeof props.post.playlist === 'object' && 'id' in props.post.playlist) {
    initialPlaylists.push(props.post.playlist as PlaylistCard);
    seenPlaylistIds.add(String((props.post.playlist as PlaylistCard).id).padStart(8, '0'));
  }
  for (const attachment of props.post.attachments_data || []) {
    if (attachment.content_type === 'playlist' && attachment.playlist_data && !seenPlaylistIds.has(String(attachment.playlist_data.id).padStart(8, '0'))) {
      initialPlaylists.push(attachment.playlist_data);
      seenPlaylistIds.add(String(attachment.playlist_data.id).padStart(8, '0'));
    }
  }
  editAttachPreviewPlaylist.value = initialPlaylists;

  const saved = draftOwner ? await postDraftGet<{version: number; clientId: string; text: string; isSpoiler: boolean; spoilerDescription: string; tags: string[]; retained: (number | string)[]; anime: AnimeCard[]; playlists: PlaylistCard[]; excerpts?: Excerpt[]; files: File[]}>('drafts', `${draftOwner}:edit:${props.post.id}`).catch(() => undefined) : undefined;
  if (saved && saved.version === (props.post.version || 1) && String(auth.user?.id) === String(draftOwner)) {
    editClientId.value = saved.clientId; text.value = saved.text; isSpoiler.value = saved.isSpoiler;
    spoilerDescription.value = saved.spoilerDescription; tags.value = saved.tags;
    retainedMedia.value = retainedMedia.value.filter(row => saved.retained.includes(row.id));
    editAttachPreviewExcerpts.value = saved.excerpts || editAttachPreviewExcerpts.value;
    editAttachPreviewAnime.value = saved.anime; editAttachPreviewPlaylist.value = saved.playlists;
    editAttachPreviewMedia.value = saved.files.map(file => ({file, url: URL.createObjectURL(file), type: file.type.startsWith('image') ? 'image' : 'video'}));
  }
  restoring = false;
  await nextTick();
  autoResize();
  textArea.value?.focus();
});

defineExpose({
  openAttach,
  onAttachConfirmFromEdit,
  editAttachPreviewMedia,
  editAttachPreviewAnime,
  editAttachPreviewPlaylist,
  editAttachPreviewExcerpts,
  removeEditMedia,
  removeEditAnime,
  removeEditPlaylist,
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: var(--viewport-top, 0px) 0 auto;
  height: var(--viewport-height, 100dvh);
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  backdrop-filter: blur(4px);
}

.edit-post-modal {
  background: var(--surface-1, #0a0a0a);
  border-radius: 16px;
  border: 1px solid var(--border-subtle, #1a1a1a);
  width: 100%;
  max-width: 560px;
  max-height: calc(var(--viewport-height, 100dvh) * 0.9);
  overflow-y: auto;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.7);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-subtle, #1a1a1a);
}

.modal-header h2 {
  color: var(--text-primary, #fff);
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-tertiary, #555);
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  color: var(--text-primary, #fff);
  background: var(--surface-3, #1a1a1a);
}

.content-area {
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.text-input {
  width: 100%;
  min-height: 110px;
  max-height: calc(var(--viewport-height, 100dvh) * 0.44);
  background: transparent;
  border: none;
  color: var(--text-primary, #e0e0e0);
  font-size: 0.95rem;
  line-height: 1.6;
  resize: none;
  box-sizing: border-box;
  font-family: inherit;
}

.text-input:focus {
  outline: none;
}

.text-input::placeholder {
  color: var(--text-tertiary, #444);
}

.char-count {
  text-align: right;
  color: var(--text-tertiary, #555);
  font-size: 0.75rem;
}

.char-count.warning {
  color: var(--warning, #f59e0b);
}

.char-count.error {
  color: var(--danger, #ef4444);
}

.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  color: var(--text-secondary, #888);
  font-size: 0.875rem;
  cursor: pointer;
  user-select: none;
  transition: color 0.2s;
}

.toggle-label:hover {
  color: var(--text-primary, #ddd);
}

.toggle-input {
  display: none;
}

.toggle-switch {
  position: relative;
  width: 38px;
  height: 22px;
  background: var(--surface-4, #222);
  border-radius: 22px;
  transition: all 0.25s ease;
  flex-shrink: 0;
}

.toggle-slider {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 16px;
  height: 16px;
  background: var(--text-tertiary, #555);
  border-radius: 50%;
  transition: all 0.25s ease;
}

.toggle-switch.active {
  background: var(--accent, #7c5cfc);
}

.toggle-switch.active .toggle-slider {
  left: 19px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(124, 92, 252, 0.4);
}

.spoiler-settings {
  margin-top: 0.25rem;
}

.spoiler-for-input {
  width: 100%;
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-default, #252525);
  color: var(--text-primary, #e0e0e0);
  padding: 0.6rem 0.8rem;
  border-radius: 10px;
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.spoiler-for-input:focus {
  outline: none;
  border-color: var(--warning, #fbbf24);
}

.spoiler-for-input::placeholder {
  color: var(--text-tertiary, #555);
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
}

.tags-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.5rem;
  border-radius: 999px;
  background: var(--accent-subtle, rgba(124, 92, 252, 0.15));
  border: 1px solid var(--accent, #7c5cfc);
  color: var(--text-primary);
  font-size: 0.8rem;
}

.tag-remove {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
}

.tag-input {
  flex: 1;
  min-width: 120px;
  background: var(--surface-3, #141414);
  border: 1px solid var(--border-default, #252525);
  color: var(--text-primary, #e0e0e0);
  padding: 0.55rem 0.75rem;
  border-radius: 999px;
  font-size: 0.85rem;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.tag-input:focus {
  outline: none;
  border-color: var(--accent, #7c5cfc);
}

.tag-input::placeholder {
  color: var(--text-tertiary, #555);
}

.compact-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toolbar-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.45rem 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border-default);
  background: var(--surface-3, #141414);
  color: var(--text-secondary);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-chip:hover {
  border-color: var(--accent, #7c5cfc);
  color: var(--text-primary);
}

.media-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.media-thumb {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border-default);
  background: var(--surface-3);
}

.media-thumb img,
.media-thumb video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-thumb-btn {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 20px;
  height: 20px;
  min-height: 20px;
  min-width: 20px;
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.7);
  color: #fff;
  cursor: pointer;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attach-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.attach-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.6rem;
  border-radius: 999px;
  background: var(--accent-subtle, rgba(124, 92, 252, 0.15));
  border: 1px solid var(--accent, #7c5cfc);
  color: var(--text-primary);
  font-size: 0.8rem;
}

.remove-chip-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0;
  line-height: 1;
}

.submit-row {
  padding: 1rem 1.25rem 1.25rem;
}

.submit-btn {
  width: 100%;
  background: var(--accent, #7c5cfc);
  color: #fff;
  border: none;
  padding: 0.75rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: var(--accent-hover, #6b4de8);
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>
