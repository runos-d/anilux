/** Render plain post text without interpreting user HTML or enriching inside links. */
export function formatPostText(text: string): string {
  const escape = (value: string) => value.replace(/[&<>"']/g, (char) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[char] ?? char);
  return text.replace(/https?:\/\/[^\s<>"']+|#[\p{L}\p{N}_-]+|@[\p{L}\p{N}_]+|\n|[^\n]/gu, (token) => {
    const safe = escape(token);
    if (token.startsWith('http://') || token.startsWith('https://')) {
      return `<a href="${safe}" target="_blank" rel="noopener noreferrer">${safe}</a>`;
    }
    if (token.startsWith('#')) return `<span class="ht">${safe}</span>`;
    if (token.startsWith('@')) return `<span class="mn">${safe}</span>`;
    return token === '\n' ? '<br>' : safe;
  });
}
