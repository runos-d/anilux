import { ref } from 'vue';

const bc = typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('sound-leader') : null;
export type SoundType = 'message'|'mention'|'like'|'follower'|'contest_start'|'contest_win';
type WebkitAudioWindow = Window & typeof globalThis & {
  webkitAudioContext?: typeof AudioContext;
};

function playTone(type: SoundType, vol=0.3) {
  bc?.postMessage({ action: 'request', type });
  try {
    const AudioCtx = window.AudioContext || (window as WebkitAudioWindow).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.connect(g); g.connect(ctx.destination);
    osc.type = type === 'mention' ? 'sine' : (type === 'like' ? 'triangle' : 'sine');
    osc.frequency.setValueAtTime(type === 'contest_win' ? 880 : 440, ctx.currentTime);
    g.gain.setValueAtTime(vol, ctx.currentTime);
    g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc.addEventListener('ended', () => void ctx.close(), { once: true });
    osc.start(); osc.stop(ctx.currentTime + 0.3);
  } catch(e){ console.error('Sound error', e); }
}

export function useSoundPlayer() {
  const playing = ref(false);
  const play = (type: SoundType, vol=0.3) => { playing.value = true; playTone(type, vol); setTimeout(()=>playing.value=false, 350); };
  return { playing, play };
}
