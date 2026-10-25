export function loadFontStyles(): void {
  const families = [
    'family=Inter:wght@300;400;500;600;700&family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700',
  ];
  for (const family of families) {
    const href = `https://fonts.googleapis.com/css2?${family}&display=swap`;
    if ([...document.querySelectorAll<HTMLLinkElement>('link[rel="stylesheet"]')].some(link => link.href === href)) continue;
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.href = href;
    document.head.appendChild(link);
  }
}
