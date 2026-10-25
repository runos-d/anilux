import { afterEach, describe, expect, it, vi } from 'vitest';
import { useSeo, refreshSeo, seoPage } from './useSeo';

const { accountGet } = vi.hoisted(() => ({ accountGet: vi.fn() }));
vi.mock('@/api/client', () => ({ default: { get: accountGet } }));

describe('useSeo', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    document.title = 'AniLux';
    document.head.querySelectorAll('meta[name="description"]').forEach((el) => el.remove());
    document.head.querySelectorAll('meta[name="robots"]').forEach((el) => el.remove());
    document.head.querySelectorAll('meta[property^="og:"]').forEach((el) => el.remove());
    document.head.querySelectorAll('meta[name^="twitter:"]').forEach((el) => el.remove());
    document.head.querySelectorAll('link[rel="canonical"]').forEach((el) => el.remove());
  });

  it('uses the authenticated catalog client for library exclusions', async () => {
    accountGet.mockResolvedValue({ data: { title: 'Личная подборка', description: '', robots: 'noindex,follow' } });
    const anonymousFetch = vi.fn();
    vi.stubGlobal('fetch', anonymousFetch);
    const path = '/anime/year/2025?excluded_library_statuses=completed';
    await refreshSeo(path, true);
    expect(accountGet).toHaveBeenCalledWith('/seo/page/', expect.objectContaining({ params: { path }, signal: expect.any(AbortSignal) }));
    expect(anonymousFetch).not.toHaveBeenCalled();
    expect(document.title).toBe('Личная подборка');
  });

  it('reloads personal refinements instead of using the anonymous HTML bootstrap', async () => {
    vi.resetModules();
    accountGet.mockClear();
    const path = '/anime/year/2025?excluded_library_statuses=completed';
    history.replaceState(null, '', path);
    const bootstrap = document.createElement('script');
    bootstrap.id = 'seo-bootstrap';
    bootstrap.type = 'application/json';
    bootstrap.dataset.path = path;
    bootstrap.textContent = JSON.stringify({ title: 'Анонимная выборка', description: '' });
    document.head.append(bootstrap);
    accountGet.mockResolvedValue({ data: { title: 'Моя выборка', description: '' } });
    const fresh = await import('./useSeo');
    await fresh.refreshSeo(path);
    expect(accountGet).toHaveBeenCalledTimes(1);
    expect(document.title).toBe('Моя выборка');
    history.replaceState(null, '', '/');
  });

  it('removes the preceding image and JSON-LD and deduplicates tags', () => {
    useSeo({ title: 'A', description: 'A', ogImage: '/poster.jpg', jsonLd: { '@type': 'TVSeries' } });
    const duplicate = document.createElement('meta'); duplicate.name = 'description'; document.head.append(duplicate);
    useSeo({ title: 'B', description: 'B' });
    expect(document.querySelector('meta[property="og:image"]')).toBeNull();
    expect(document.querySelector('meta[name="twitter:image"]')).toBeNull();
    expect(document.querySelector('script[data-seo-jsonld]')).toBeNull();
    expect(document.querySelectorAll('meta[name="description"]')).toHaveLength(1);
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex,follow');
  });

  it('ignores a late response from a previous route even if fetch ignores abort', async () => {
    let finishOld!: (value: unknown) => void;
    vi.stubGlobal('fetch', vi.fn()
      .mockImplementationOnce(() => new Promise(resolve => { finishOld = resolve; }))
      .mockResolvedValueOnce({ ok: true, json: async () => ({ title: 'New', description: 'New', robots: 'index,follow' }) }));
    const old = refreshSeo('/old');
    await refreshSeo('/new');
    finishOld({ ok: true, json: async () => ({ title: 'Old', description: 'Old' }) });
    await old;
    expect(document.title).toBe('New');
    expect(seoPage.value?.title).toBe('New');
  });

  it('clears public metadata immediately on a private navigation or failed read', async () => {
    useSeo({ title: 'Public secret', description: 'Public text', ogImage: '/poster.jpg' });
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')));
    await refreshSeo('/playlist/shared/token');
    expect(document.title).not.toContain('Public secret');
    expect(document.querySelector('meta[property="og:image"]')).toBeNull();
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('noindex,follow');
  });

  it('updates title, description, canonical and social tags', () => {
    useSeo({
      title: 'Test anime -смотреть онлайн',
      description: 'Смотрите Test anime онлайн и в хорошем качестве.',
      canonical: 'https://example.com/anime/test-anime',
      ogImage: 'https://example.com/poster.jpg',
      robots: 'index,follow',
    });

    expect(document.title).toBe('Test anime -смотреть онлайн');
    expect(document.querySelector('meta[name="description"]')?.getAttribute('content')).toBe('Смотрите Test anime онлайн и в хорошем качестве.');
    expect(document.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe('https://example.com/anime/test-anime');
    expect(document.querySelector('meta[name="robots"]')?.getAttribute('content')).toBe('index,follow');
    expect(document.querySelector('meta[property="og:title"]')?.getAttribute('content')).toBe('Test anime -смотреть онлайн');
    expect(document.querySelector('meta[property="og:description"]')?.getAttribute('content')).toBe('Смотрите Test anime онлайн и в хорошем качестве.');
    expect(document.querySelector('meta[property="og:image"]')?.getAttribute('content')).toBe('https://example.com/poster.jpg');
    expect(document.querySelector('meta[name="twitter:card"]')?.getAttribute('content')).toBe('summary_large_image');
  });
});
