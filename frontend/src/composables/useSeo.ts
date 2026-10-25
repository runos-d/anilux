import { shallowRef } from 'vue';
import { applySeoHead as useSeo, type SeoData } from '@/lib/seoHead';
import apiClient from '@/api/client';
export { applySeoHead as useSeo } from '@/lib/seoHead';
export type { SeoData } from '@/lib/seoHead';

export const seoPage = shallowRef<SeoData | null>(null);
let generation = 0;
let controller: AbortController | undefined;
let currentPath = '';
let bootstrap: { path: string; data: SeoData } | undefined;
if (typeof document !== 'undefined') {
  const element = document.getElementById('seo-bootstrap');
  if (element?.textContent) {
    try { const path = location.pathname + location.search; if (!element.dataset.path || element.dataset.path === path) bootstrap = { path, data: JSON.parse(element.textContent) }; }
    catch { /* API remains authoritative when bootstrap is unavailable. */ }
    element.remove();
  }
}

export async function refreshSeo(path = currentPath, force = false) {
  currentPath = path;
  const personalSelection = /[?&]excluded_library_statuses=/.test(path);
  const ownGeneration = ++generation;
  controller?.abort();
  if (!force && !personalSelection && bootstrap?.path === path) {
    const data = bootstrap.data; bootstrap = undefined;
    seoPage.value = data; useSeo(data); return;
  }
  bootstrap = undefined;
  const site = seoPage.value?.site || 'AniLux';
  seoPage.value = null;
  useSeo({ title: site, description: '', robots: 'noindex,follow' });
  const ownController = new AbortController();
  controller = ownController;
  const timeout = setTimeout(() => ownController.abort(), 15000);
  try {
    let data: SeoData;
    if (personalSelection) {
      const response = await apiClient.get('/seo/page/', { params: { path }, signal: ownController.signal });
      data = response.data;
    } else {
      const response = await fetch('/api/seo/page/?path=' + encodeURIComponent(path), {
        signal: ownController.signal, credentials: 'omit', cache: 'no-store', headers: { Accept: 'application/json' },
      });
      if (!response.ok) throw new Error('SEO projection unavailable');
      data = await response.json();
    }
    if (ownGeneration !== generation) return;
    seoPage.value = data; useSeo(data);
  } catch {
    if (ownGeneration === generation) {
      const data = { title: site, description: '', robots: 'noindex,follow', status: 503,
        contentHtml: '<section class="seo-page"><h1>Страница временно недоступна</h1><a href="/anime">Каталог аниме</a></section>' };
      seoPage.value = data; useSeo(data);
    }
  } finally { clearTimeout(timeout); }
}
