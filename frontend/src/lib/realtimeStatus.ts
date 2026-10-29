import { ref } from 'vue';

// Kept separate from chat stores so the app shell does not eagerly import them.
export const globalConnectionReady = ref(false);
let sender: ((data: Record<string, unknown>) => void) | null = null;
export function setGlobalSender(next: typeof sender) { sender = next; }
export function sendPresence(isActive: boolean) {
  if (!globalConnectionReady.value || !sender) return false;
  sender({ action: 'presence', is_active: isActive });
  return true;
}
