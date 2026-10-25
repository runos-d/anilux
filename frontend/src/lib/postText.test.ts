import { describe, expect, it } from 'vitest';
import { formatPostText } from './postText';

describe('post text', () => {
  it('renders user HTML as text and cannot create event handlers', () => {
    const html = formatPostText('<img src=x onerror=alert(1)> https://example.org/"onclick="alert(2)');
    const root = document.createElement('div');
    root.innerHTML = html;
    expect(root.querySelector('img')).toBeNull();
    expect(root.querySelector('[onclick],[onerror]')).toBeNull();
    expect(root.querySelector('a')?.getAttribute('href')).toBe('https://example.org/');
    expect(root.textContent).toContain('<img src=x onerror=alert(1)>');
  });
  it('preserves links, unicode hashtags, mentions and line breaks', () => {
    const root = document.createElement('div');
    root.innerHTML = formatPostText('#аниме @user\nhttps://example.org/?a=1&b=2#tag');
    expect(root.querySelector('.ht')?.textContent).toBe('#аниме');
    expect(root.querySelector('.mn')?.textContent).toBe('@user');
    expect(root.querySelector('br')).not.toBeNull();
    expect(root.querySelector('a')?.getAttribute('href')).toBe('https://example.org/?a=1&b=2#tag');
  });
});
