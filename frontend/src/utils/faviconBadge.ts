let originalIcon: string | null = null;

export function updateFaviconBadge(n: number) {

  try {
    const link = document.querySelector('link[rel*="icon"]') as HTMLLinkElement | null;
    if (!link) return;
    originalIcon ??= link.href;
    if (n <= 0) { link.href = originalIcon; return; }
    const canvas = document.createElement('canvas');
    canvas.width = 32; canvas.height = 32;
    const ctx = canvas.getContext('2d')!;
    ctx.clearRect(0,0,32,32);
    ctx.beginPath(); ctx.arc(16,16,10,0,Math.PI*2); ctx.fillStyle='#e83e8c'; ctx.fill();
    if (n > 0) {
      ctx.fillStyle='#fff'; ctx.font='bold 10px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(String(n > 9 ? '9+' : n), 16, 16);
    }
    if (link) link.href = canvas.toDataURL('image/png');
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch(e){  }
}
