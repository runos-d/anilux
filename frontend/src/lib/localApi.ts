const loopbackHosts = new Set(['localhost', '127.0.0.1', '[::1]']);
export function isLocalApi(url: string) {
  try { return loopbackHosts.has(new URL(url).hostname); } catch { return false; }
}
export function resolveApiBase(configured: string | undefined, origin: string, development: boolean) {
  if (!configured) return origin + '/api';
  if (development && isLocalApi(configured)) {
    const url = new URL(configured);
    if (/^\/api\/?$/.test(url.pathname)) return origin + '/api';
  }
  return configured;
}
export function developmentProxyTarget(configured: string) {
  const url = new URL(configured);
  url.pathname = url.pathname.replace(/\/api\/?$/, '');
  if (isLocalApi(configured)) {
    url.hostname = '127.0.0.1';
    url.protocol = 'http:';
  }
  return url.href.replace(/\/$/, '');
}
