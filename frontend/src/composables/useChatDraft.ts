import { watch, type Ref } from 'vue';

/** Persist a separate text draft for each conversation/topic in this tab. */
export function useChatDraft(key: () => string | null, text: Ref<string>) {
  let active: string | null = null;
  const save = () => {
    if (!active) return;
    try {
      if (text.value) sessionStorage.setItem(`chat-draft:${active}`, text.value);
      else sessionStorage.removeItem(`chat-draft:${active}`);
    } catch { /* Storage quota must not prevent sending. */ }
  };
  watch(key, value => {
    save(); active = value;
    try { text.value = value ? sessionStorage.getItem(`chat-draft:${value}`) || '' : ''; }
    catch { text.value = ''; }
  }, { immediate: true, flush: 'sync' });
  watch(text, save, { flush: 'sync' });
}
