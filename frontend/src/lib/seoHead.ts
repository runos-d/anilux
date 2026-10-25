export interface SeoData {
  title: string;
  description: string;
  h1?: string;
  canonical?: string;
  ogImage?: string;
  image?: string;
  robots?: string;
  jsonLd?: Record<string, unknown> | Array<Record<string, unknown>>;
  schema?: Array<Record<string, unknown>>;
  site?: string;
  kind?: string;
  path?: string;
  contentHtml?: string;
  related?: Array<{ name: string; path: string }>;
  items?: Array<{ id?: number; slug?: string; name: string; path: string; image?: string; year?: number; kind?: string;
    type?: string; status?: string; score?: number; episodes?: number; genres?: string[] }>;
  crumbs?: Array<{ name: string; path: string }>;
  status?: number;
  text?: string;
  redirect?: string;
  number?: number;
  pages?: number;
  page_size?: number;
  count?: number;
}

function meta(attribute: 'name' | 'property', key: string, value?: string) {
  const elements = [...document.head.querySelectorAll<HTMLMetaElement>(`meta[${attribute}="${key}"]`)];
  let element = elements.shift();
  elements.forEach(item => item.remove());
  if (!value) { element?.remove(); return; }
  if (!element) {
    element = document.createElement('meta'); element.setAttribute(attribute, key); document.head.append(element);
  }
  element.content = value;
}

export function applySeoHead(data: SeoData) {
  document.title = data.title;
  document.documentElement.lang = 'ru';
  meta('name', 'description', data.description);
  meta('name', 'robots', data.robots || 'noindex,follow');
  document.querySelectorAll('link[rel="canonical"]').forEach(item => item.remove());
  if (data.canonical) {
    const link = document.createElement('link'); link.rel = 'canonical'; link.href = data.canonical; document.head.append(link);
  }
  const image = data.image || data.ogImage;
  const properties = { 'og:title': data.title, 'og:description': data.description,
    'og:url': data.canonical, 'og:type': data.kind === 'post' ? 'article' : 'website',
    'og:site_name': data.site, 'og:locale': 'ru_RU', 'og:image': image };
  Object.entries(properties).forEach(([key, value]) => meta('property', key, value));
  meta('name', 'twitter:card', image ? 'summary_large_image' : 'summary');
  meta('name', 'twitter:title', data.title); meta('name', 'twitter:description', data.description);
  meta('name', 'twitter:image', image);
  document.querySelectorAll('script[data-seo-jsonld]').forEach(item => item.remove());
  const schema = data.schema || (Array.isArray(data.jsonLd) ? data.jsonLd : data.jsonLd ? [data.jsonLd] : []);
  if (schema.length) {
    const script = document.createElement('script'); script.type = 'application/ld+json';
    script.dataset.seoJsonld = 'true'; script.textContent = JSON.stringify(schema); document.head.append(script);
  }
}

